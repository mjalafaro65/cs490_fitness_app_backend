from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from datetime import datetime
from db import db
from models import (
    Messages, Conversations, ConversationParticipants, 
    Users, OnlineUsers
)
from schemas.messaging_schema import MessageSchema, SocketMessageSchema
import logging

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")

# Store connected users
connected_users = {}

@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    try:
        # Verify JWT token
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        # Store user connection
        connected_users[user_id] = request.sid
        
        # Update online status in database
        online_user = OnlineUsers.query.filter_by(user_id=user_id).first()
        if online_user:
            online_user.socket_id = request.sid
            online_user.last_seen = datetime.utcnow()
            online_user.is_online = True
        else:
            online_user = OnlineUsers(
                user_id=user_id,
                socket_id=request.sid,
                last_seen=datetime.utcnow(),
                is_online=True
            )
            db.session.add(online_user)
        
        db.session.commit()
        
        # Join user to their personal room for direct messages
        join_room(f"user_{user_id}")
        
        emit('connected', {'user_id': user_id})
        logging.info(f"User {user_id} connected")
        
    except Exception as e:
        logging.error(f"Connection error: {str(e)}")
        disconnect()
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        user_id = None
        # Find user by socket ID
        for uid, sid in connected_users.items():
            if sid == request.sid:
                user_id = uid
                break
        
        if user_id:
            # Remove from connected users
            del connected_users[user_id]
            
            # Update online status
            online_user = OnlineUsers.query.filter_by(user_id=user_id).first()
            if online_user:
                online_user.is_online = False
                online_user.last_seen = datetime.utcnow()
                db.session.commit()
            
            logging.info(f"User {user_id} disconnected")
            
    except Exception as e:
        logging.error(f"Disconnect error: {str(e)}")

@socketio.on('join_conversation')
def handle_join_conversation(data):
    """Handle joining a conversation room"""
    try:
        user_id = get_jwt_identity()
        conversation_id = data['conversation_id']
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not participant:
            emit('error', {'message': 'Access denied to conversation'})
            return
        
        # Join conversation room
        room = f"conversation_{conversation_id}"
        join_room(room)
        
        emit('joined_conversation', {'conversation_id': conversation_id})
        logging.info(f"User {user_id} joined conversation {conversation_id}")
        
    except Exception as e:
        logging.error(f"Join conversation error: {str(e)}")
        emit('error', {'message': 'Failed to join conversation'})

@socketio.on('leave_conversation')
def handle_leave_conversation(data):
    """Handle leaving a conversation room"""
    try:
        user_id = get_jwt_identity()
        conversation_id = data['conversation_id']
        
        room = f"conversation_{conversation_id}"
        leave_room(room)
        
        emit('left_conversation', {'conversation_id': conversation_id})
        logging.info(f"User {user_id} left conversation {conversation_id}")
        
    except Exception as e:
        logging.error(f"Leave conversation error: {str(e)}")

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message"""
    try:
        user_id = get_jwt_identity()
        conversation_id = data['conversation_id']
        body = data['body']
        message_type = data.get('message_type', 'text')
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not participant:
            emit('error', {'message': 'Access denied to conversation'})
            return
        
        # Create message
        new_message = Messages(
            conversation_id=conversation_id,
            sender_user_id=user_id,
            body=body,
            message_type=message_type,
            sent_at=datetime.utcnow()
        )
        
        db.session.add(new_message)
        
        # Update conversation timestamp
        conversation = Conversations.query.get(conversation_id)
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Serialize message
        message_schema = MessageSchema()
        message_data = message_schema.dump(new_message)
        
        # Create socket message
        socket_message = {
            'type': 'message',
            'data': message_data,
            'conversation_id': conversation_id,
            'sender_user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to conversation room
        room = f"conversation_{conversation_id}"
        emit('new_message', socket_message, room=room)
        
        # Send to online participants individually
        participants = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            is_active=True
        ).all()
        
        for participant in participants:
            if participant.user_id != user_id:
                participant_room = f"user_{participant.user_id}"
                emit('new_message', socket_message, room=participant_room)
        
        logging.info(f"Message sent in conversation {conversation_id} by user {user_id}")
        
    except Exception as e:
        logging.error(f"Send message error: {str(e)}")
        emit('error', {'message': 'Failed to send message'})

@socketio.on('typing_start')
def handle_typing_start(data):
    """Handle typing indicator start"""
    try:
        user_id = get_jwt_identity()
        conversation_id = data['conversation_id']
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not participant:
            return
        
        # Get user info
        user = Users.query.get(user_id)
        
        typing_data = {
            'type': 'typing_start',
            'data': {
                'user_id': user_id,
                'user_name': f"{user.first_name} {user.last_name}",
                'conversation_id': conversation_id
            },
            'conversation_id': conversation_id,
            'sender_user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to conversation room (excluding sender)
        room = f"conversation_{conversation_id}"
        emit('typing_indicator', typing_data, room=room, include_self=False)
        
    except Exception as e:
        logging.error(f"Typing start error: {str(e)}")

@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Handle typing indicator stop"""
    try:
        user_id = get_jwt_identity()
        conversation_id = data['conversation_id']
        
        typing_data = {
            'type': 'typing_stop',
            'data': {
                'user_id': user_id,
                'conversation_id': conversation_id
            },
            'conversation_id': conversation_id,
            'sender_user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to conversation room (excluding sender)
        room = f"conversation_{conversation_id}"
        emit('typing_indicator', typing_data, room=room, include_self=False)
        
    except Exception as e:
        logging.error(f"Typing stop error: {str(e)}")

@socketio.on('mark_read')
def handle_mark_read(data):
    """Handle marking messages as read"""
    try:
        user_id = get_jwt_identity()
        message_id = data['message_id']
        
        message = Messages.query.get_or_404(message_id)
        
        # Verify user is participant and not the sender
        participant = ConversationParticipants.query.filter_by(
            conversation_id=message.conversation_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not participant or message.sender_user_id == user_id:
            emit('error', {'message': 'Cannot mark this message as read'})
            return
        
        # Mark as read
        message.is_read = True
        message.read_at = datetime.utcnow()
        
        # Update participant's last_read_at
        participant.last_read_at = datetime.utcnow()
        
        db.session.commit()
        
        # Notify sender
        read_data = {
            'type': 'read_receipt',
            'data': {
                'message_id': message_id,
                'reader_user_id': user_id,
                'read_at': message.read_at.isoformat()
            },
            'conversation_id': message.conversation_id,
            'sender_user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to message sender
        sender_room = f"user_{message.sender_user_id}"
        emit('message_read', read_data, room=sender_room)
        
    except Exception as e:
        logging.error(f"Mark read error: {str(e)}")
        emit('error', {'message': 'Failed to mark message as read'})

# Utility function to get online users
def get_online_users():
    """Get list of online users"""
    return OnlineUsers.query.filter_by(is_online=True).all()

# Utility function to send notification to specific user
def send_notification_to_user(user_id, notification_data):
    """Send notification to specific user"""
    if user_id in connected_users:
        user_room = f"user_{user_id}"
        emit('notification', notification_data, room=user_room)
