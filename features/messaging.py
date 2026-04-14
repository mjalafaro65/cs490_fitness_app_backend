from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import or_, and_
from db import db
from models import (
    Messages, Conversations, ConversationParticipants, 
    Users, OnlineUsers
)
from schemas.messaging_schema import (
    MessageSchema, ConversationSchema, CreateConversationSchema,
    SendMessageSchema, MarkMessageReadSchema, OnlineUserSchema
)

messaging_blp = Blueprint("Messaging", __name__, url_prefix="/messaging", description="Instant messaging operations")

@messaging_blp.route("/conversations")
class ConversationList(MethodView):
    @jwt_required()
    @messaging_blp.response(200, ConversationSchema(many=True))
    def get(self):
        """Get all conversations for the current user"""
        current_user_id = get_jwt_identity()
        
        # Get conversations where user is a participant
        conversations = db.session.query(Conversations).join(
            ConversationParticipants,
            Conversations.conversation_id == ConversationParticipants.conversation_id
        ).filter(
            ConversationParticipants.user_id == current_user_id,
            ConversationParticipants.is_active == True
        ).order_by(Conversations.updated_at.desc()).all()
        
        return conversations

@messaging_blp.route("/conversations")
class CreateConversation(MethodView):
    @jwt_required()
    @messaging_blp.arguments(CreateConversationSchema)
    @messaging_blp.response(201, ConversationSchema)
    def post(self, data):
        """Create a new conversation"""
        current_user_id = get_jwt_identity()
        participant_ids = data['participant_ids']
        
        # Ensure current user is included in participants
        if current_user_id not in participant_ids:
            participant_ids.append(current_user_id)
        
        # Check if conversation already exists for direct messages
        if data['conversation_type'] == 'direct' and len(participant_ids) == 2:
            existing_conversation = db.session.query(Conversations).join(
                ConversationParticipants,
                Conversations.conversation_id == ConversationParticipants.conversation_id
            ).filter(
                Conversations.conversation_type == 'direct',
                ConversationParticipants.user_id.in_(participant_ids)
            ).group_by(Conversations.conversation_id).having(
                db.func.count(ConversationParticipants.user_id) == 2
            ).first()
            
            if existing_conversation:
                return existing_conversation
        
        # Create new conversation
        # Generate unique relationship_id if needed
        relationship_id = data['relationship_id']
        if relationship_id == 0:
            # Generate a unique relationship_id using timestamp
            relationship_id = int(datetime.utcnow().timestamp())
        
        new_conversation = Conversations(
            relationship_id=relationship_id,
            conversation_type=data['conversation_type']
        )
        
        try:
            db.session.add(new_conversation)
            db.session.flush()  # Get the conversation_id
        except Exception as e:
            # Handle duplicate relationship_id
            if "Duplicate entry" in str(e):
                # Generate a new unique relationship_id
                relationship_id = int(datetime.utcnow().timestamp()) + len(participant_ids)
                new_conversation.relationship_id = relationship_id
                db.session.add(new_conversation)
                db.session.flush()
            else:
                raise e
        
        # Add participants (check for duplicates)
        for user_id in participant_ids:
            # Check if participant already exists
            existing_participant = ConversationParticipants.query.filter_by(
                conversation_id=new_conversation.conversation_id,
                user_id=user_id
            ).first()
            
            if not existing_participant:
                participant = ConversationParticipants(
                    conversation_id=new_conversation.conversation_id,
                    user_id=user_id
                )
                db.session.add(participant)
        
        db.session.commit()
        return new_conversation

@messaging_blp.route("/conversations/<int:conversation_id>")
class ConversationDetail(MethodView):
    @jwt_required()
    @messaging_blp.response(200, ConversationSchema)
    def get(self, conversation_id):
        """Get conversation details"""
        current_user_id = get_jwt_identity()
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not participant:
            abort(403, description="Access denied to this conversation")
        
        conversation = Conversations.query.get_or_404(conversation_id)
        return conversation

@messaging_blp.route("/conversations/<int:conversation_id>/messages")
class MessageList(MethodView):
    @jwt_required()
    @messaging_blp.response(200, MessageSchema(many=True))
    def get(self, conversation_id):
        """Get messages in a conversation"""
        current_user_id = get_jwt_identity()
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not participant:
            abort(403, description="Access denied to this conversation")
        
        # Get messages, ordered by sent_at
        messages = Messages.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Messages.sent_at.asc()).all()
        
        return messages

@messaging_blp.route("/conversations/<int:conversation_id>/messages")
class SendMessage(MethodView):
    @jwt_required()
    @messaging_blp.arguments(SendMessageSchema)
    @messaging_blp.response(201, MessageSchema)
    def post(self, data, conversation_id):
        """Send a message to a conversation"""
        current_user_id = get_jwt_identity()
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not participant:
            abort(403, description="Access denied to this conversation")
        
        # Create message
        new_message = Messages(
            conversation_id=conversation_id,
            sender_user_id=current_user_id,
            body=data['body'],
            message_type=data['message_type'],
            sent_at=datetime.utcnow()
        )
        
        db.session.add(new_message)
        
        # Update conversation timestamp
        conversation = Conversations.query.get(conversation_id)
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        return new_message

@messaging_blp.route("/messages/<int:message_id>/read")
class MarkMessageRead(MethodView):
    @jwt_required()
    @messaging_blp.response(200, MessageSchema)
    def put(self, message_id):
        """Mark a message as read"""
        current_user_id = get_jwt_identity()
        
        message = Messages.query.get_or_404(message_id)
        
        # Verify user is participant and not the sender
        participant = ConversationParticipants.query.filter_by(
            conversation_id=message.conversation_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not participant or message.sender_user_id == current_user_id:
            abort(403, description="Cannot mark this message as read")
        
        # Mark as read
        message.is_read = True
        message.read_at = datetime.utcnow()
        
        # Update participant's last_read_at
        participant.last_read_at = datetime.utcnow()
        
        db.session.commit()
        return message

@messaging_blp.route("/users/online")
class OnlineUsersList(MethodView):
    @jwt_required()
    @messaging_blp.response(200, OnlineUserSchema(many=True))
    def get(self):
        """Get list of online users"""
        online_users = OnlineUsers.query.filter_by(is_online=True).all()
        return online_users

@messaging_blp.route("/conversations/<int:conversation_id>/typing")
class TypingIndicator(MethodView):
    @jwt_required()
    def post(self, conversation_id):
        """Send typing indicator (placeholder for WebSocket implementation)"""
        current_user_id = get_jwt_identity()
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not participant:
            abort(403, description="Access denied to this conversation")
        
        # This will be handled by WebSocket events
        return {"message": "Typing indicator sent via WebSocket"}
