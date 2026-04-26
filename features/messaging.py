from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import or_, and_
from db import db
from models import (
    Messages, Conversations, ConversationParticipants, 
    Users, OnlineUsers,  CoachClientRelationships, CoachProfiles, ClientProfiles
)
from schemas.messaging_schema import (
    MessageSchema, ConversationSchema, CreateConversationSchema,
    SendMessageSchema, MarkMessageReadSchema, OnlineUserSchema
)

def _auth_id_int():
    raw = get_jwt_identity()
    if raw is None:
        abort(401, description="Not authenticated.")
    try:
        return int(raw)
    except (TypeError, ValueError):
        abort(401, description="Invalid token.")

def _current_user():
    user = Users.query.filter_by(auth_id=_auth_id_int()).first()
    if not user:
        abort(404, description="User record not found.")
    return user

messaging_blp = Blueprint("Messaging", __name__, url_prefix="/messaging", description="Instant messaging operations")

@messaging_blp.route("/conversations")
class ConversationList(MethodView):
    @jwt_required()
    @messaging_blp.response(200, ConversationSchema(many=True))
    def get(self):
        """Get all conversations for the current user"""
        user = _current_user()
        
        # Get conversations where user is a participant
        # conversations = db.session.query(Conversations).join(
        #     ConversationParticipants,
        #     Conversations.conversation_id == ConversationParticipants.conversation_id
        # ).filter(
        #     ConversationParticipants.user_id == user.user_id,
        #     ConversationParticipants.is_active == True
        # ) .distinct().order_by(Conversations.updated_at.desc()).all()
        conversations = (
            db.session.query(Conversations)
            .join(ConversationParticipants)
            .filter(
                ConversationParticipants.user_id == user.user_id,
                ConversationParticipants.is_active.is_(True)
            )
            .order_by(Conversations.updated_at.desc())
            .all()
        )
        
        return conversations

# @messaging_blp.route("/conversations")
# class CreateConversation(MethodView):
#     @jwt_required()
#     @messaging_blp.arguments(CreateConversationSchema)
#     @messaging_blp.response(201, ConversationSchema)
#     def post(self, data):
#         """Create a new conversation"""
#         user = _current_user()
#         participant_ids = data['participant_ids']
        
#         # Ensure current user is included in participants
#         if user.user_id not in participant_ids:
#             participant_ids.append(user.user_id)
        
#         # Check if conversation already exists for direct messages
#         if data['conversation_type'] == 'direct' and len(participant_ids) == 2:
#             existing_conversation = db.session.query(Conversations).join(
#                 ConversationParticipants,
#                 Conversations.conversation_id == ConversationParticipants.conversation_id
#             ).filter(
#                 Conversations.conversation_type == 'direct',
#                 ConversationParticipants.user_id.in_(participant_ids)
#             ).group_by(Conversations.conversation_id).having(
#                 db.func.count(ConversationParticipants.user_id) == 2
#             ).first()
            
#             if existing_conversation:
#                 return existing_conversation
        
#         relationship_id = data["relationship_id"]
#         existing_convo = Conversations.query.filter_by(
#             relationship_id=relationship_id
#         ).first()

#         if existing_convo:
#             return existing_convo  # or return 200 with it
        
#         # Create new conversation
#         # Generate unique relationship_id if needed
#         relationship_id = data['relationship_id']
#         if relationship_id == 0:
#             # Generate a unique relationship_id using timestamp
#             relationship_id = int(datetime.utcnow().timestamp())
        
#         new_conversation = Conversations(
#             relationship_id=relationship_id,
#             conversation_type=data['conversation_type']
#         )
        
        
#         try:
#             db.session.add(new_conversation)
#             db.session.flush()  # Get the conversation_id
            
#             for user_id in set(participant_ids):
#                 db.session.add(ConversationParticipants(
#                     conversation_id=new_conversation.conversation_id,
#                     user_id=user_id
#                 ))

#         except Exception as e:
#             # Handle duplicate relationship_id
#             if "Duplicate entry" in str(e):
#                 # Generate a new unique relationship_id
#                 relationship_id = int(datetime.utcnow().timestamp()) + len(participant_ids)
#                 new_conversation.relationship_id = relationship_id
#                 db.session.add(new_conversation)
#                 db.session.flush()
#             else:
#                 raise e
        
#         # Add participants (check for duplicates)
#         for user_id in participant_ids:
#             # Check if participant already exists
#             existing_participant = ConversationParticipants.query.filter_by(
#                 conversation_id=new_conversation.conversation_id,
#                 user_id=user_id
#             ).first()
            
#             if not existing_participant:
#                 participant = ConversationParticipants(
#                     conversation_id=new_conversation.conversation_id,
#                     user_id=user_id
#                 )
#                 db.session.add(participant)
        
#         db.session.commit()
#         return new_conversation

@messaging_blp.route("/conversations")
class CreateConversation(MethodView):

    @jwt_required()
    @messaging_blp.arguments(CreateConversationSchema)
    @messaging_blp.response(201, ConversationSchema)
    def post(self, data):

        user = _current_user()
        participant_ids = set(data["participant_ids"])

        # ensure current user is included
        participant_ids.add(user.user_id)

        conversation_type = data["conversation_type"]
        relationship_id = data.get("relationship_id")

        # DIRECT CHAT DEDUPLICATION
        if conversation_type == "direct" and len(participant_ids) == 2:

            subquery = (
                db.session.query(ConversationParticipants.conversation_id)
                .filter(ConversationParticipants.user_id.in_(participant_ids))
                .group_by(ConversationParticipants.conversation_id)
                .having(db.func.count() == 2)
                .subquery()
            )

            existing = db.session.query(Conversations).filter(
                Conversations.conversation_id.in_(subquery),
                Conversations.conversation_type == "direct"
            ).first()

            if existing:
                return existing, 200

        # 2. RELATIONSHIP-BASED DEDUPLICATION
        if relationship_id:
            relationship = CoachClientRelationships.query.filter_by(
                relationship_id=relationship_id
            ).first()

            if not relationship:
                abort(403, "Invalid relationship")
                
            if user.user_id not in [
                relationship.client_user_id,
                relationship.coach_profile.user_id
            ]:
                abort(403, "Not part of this relationship")

            existing = Conversations.query.filter_by(
                relationship_id=relationship_id
            ).first()

            if existing:
                return existing, 200

        # 3. CREATE CONVERSATION
        new_conversation = Conversations(
            relationship_id=relationship_id,
            conversation_type=conversation_type
        )

        db.session.add(new_conversation)
        db.session.flush()

        # ADD PARTICIPANTS (ONLY ONCE)
     
        db.session.add_all([
            ConversationParticipants(
                conversation_id=new_conversation.conversation_id,
                user_id=uid
            )
            for uid in participant_ids
        ])

        # 5. COMMIT SAFELY
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return {"message": "Failed to create conversation"}, 500

        return new_conversation, 201

@messaging_blp.route("/conversations/<int:conversation_id>")
class ConversationDetail(MethodView):
    @jwt_required()
    @messaging_blp.response(200, ConversationSchema)
    def get(self, conversation_id):
        """Get conversation details"""
        user = _current_user()
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=user.user_id,
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
        user = _current_user()
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=user.user_id,
            # is_active=True
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
        user = _current_user()
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=user.user_id,
            is_active=True
        ).first()
        
        if not participant:
            abort(403, description="Access denied to this conversation")
        
        # Create message
        new_message = Messages(
            conversation_id=conversation_id,
            sender_user_id=user.user_id,
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
        user = _current_user()
        
        message = Messages.query.get_or_404(message_id)
        
        # Verify user is participant and not the sender
        participant = ConversationParticipants.query.filter_by(
            conversation_id=message.conversation_id,
            user_id=user.user_id,
            is_active=True
        ).first()
        
        if not participant or message.sender_user_id == user.user_id:
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
        user = _current_user()
        
        # Verify user is participant
        participant = ConversationParticipants.query.filter_by(
            conversation_id=conversation_id,
            user_id=user.user_id,
            is_active=True
        ).first()
        
        if not participant:
            abort(403, description="Access denied to this conversation")
        
        # This will be handled by WebSocket events
        return {"message": "Typing indicator sent via WebSocket"}
    
@messaging_blp.route("/relationships")
class UserRelationships(MethodView):
    @jwt_required()
    def get(self):
        user = _current_user()
        print(user.user_id)

        coach_profile = CoachProfiles.query.filter_by(
            user_id=user.user_id
        ).first()
        print(coach_profile)


        query = db.session.query(CoachClientRelationships).filter(
            CoachClientRelationships.status == "active"
        )

        if coach_profile:
            query = query.filter(
                CoachClientRelationships.coach_profile_id == coach_profile.coach_profile_id
            )
        else:
            query = query.filter(
                CoachClientRelationships.client_user_id == user.user_id
            )
           

        relationships = query.all()
        print(relationships)
        
        print("USER:", user.user_id)
        print("COACH PROFILE:", coach_profile)

        if coach_profile:
            print("PROFILE ID:", coach_profile.coach_profile_id)

        count = db.session.query(CoachClientRelationships).count()
        print("TOTAL RELATIONSHIPS:", count)
        print(db.session.query(CoachClientRelationships).all())
        
        from sqlalchemy import text
        print(CoachClientRelationships.__tablename__)

        print(db.session.execute(text("SELECT DATABASE()")).fetchone())
        rel = CoachClientRelationships.query.first()
        print(rel.client_user_id, type(rel.client_user_id))
        print(CoachClientRelationships.client_user_id.type)
        result = []

        for rel in relationships:
            client = Users.query.get(rel.client_user_id)
            print(client.user_id)


            coach_profile = CoachProfiles.query.get(rel.coach_profile_id)
            if not coach_profile:
                continue

            coach = Users.query.get(coach_profile.user_id)
            if not coach:
                continue

            is_client = user.user_id == client.user_id
            

            other_user = coach if is_client else client
            relationship_role = "client" if is_client else "coach"

            result.append({
                "relationship_id": rel.relationship_id,
                "status":  str(rel.status), 
                "started_at": rel.started_at,

                "client": {
                    "user_id": client.user_id,
                    "first_name": client.first_name,
                    "last_name": client.last_name
                },

                "coach": {
                    "user_id": coach.user_id,
                    "first_name": coach.first_name,
                    "last_name": coach.last_name
                },

                "other_user": {
                    "user_id": coach.user_id if is_client else client.user_id,
                    "first_name": coach.first_name if is_client else client.first_name,
                    "last_name":coach.last_name if is_client else client.last_name
                },

                "relationship_role": relationship_role
            })


        return result
    

@messaging_blp.route("/inbox")
class InboxView(MethodView):

    @jwt_required()
    def get(self):
        user = _current_user()

        coach_profile = CoachProfiles.query.filter_by(
            user_id=user.user_id,
            status="approved"
        ).first()

        # get relationships
        query = db.session.query(CoachClientRelationships).filter(
            CoachClientRelationships.status == "active"
        )

        if coach_profile:
            query = query.filter(
                CoachClientRelationships.coach_profile_id == coach_profile.coach_profile_id
                
            )
        else:
            query = query.filter(
                CoachClientRelationships.client_user_id == user.user_id
            )

        relationships = query.all()

        result = []

        for rel in relationships:

            # 2. find other user
            if coach_profile:
                other_user_id = rel.client_user_id
            else:
                other_user_id = rel.coach_profile.user_id

            other_user = Users.query.get(other_user_id)

            # 3. get conversation
            convo = Conversations.query.filter_by(
                relationship_id=rel.relationship_id
            ).first()

            last_message = None
            unread_count = 0

            if convo:

                msg = Messages.query.filter_by(
                    conversation_id=convo.conversation_id
                ).order_by(Messages.sent_at.desc()).first()

                if msg:
                    last_message = msg.body

                unread_count = Messages.query.filter(
                    Messages.conversation_id == convo.conversation_id,
                    Messages.sender_user_id != user.user_id,
                    Messages.is_read == False
                ).count()

            # 4. profile picture (THIS IS YOUR FIX)
            profile_picture = None

            if coach_profile:
                client_profile = ClientProfiles.query.filter_by(
                    client_id=other_user_id
                ).first()
                if client_profile:
                    profile_picture = client_profile.profile_photo 
            else:
                coach_prof = CoachProfiles.query.filter_by(
                    user_id=other_user_id
                ).first()
                if coach_prof:
                    profile_picture = coach_prof.profile_photo 

            # 5. response
            result.append({
                "relationship_id": rel.relationship_id,
                "conversation_id": convo.conversation_id if convo else None,

                "other_user": {
                    "user_id": other_user.user_id,
                    "first_name": other_user.first_name,
                    "last_name": other_user.last_name,
                    "profile_picture": profile_picture
                },

                "last_message": last_message,
                "unread_count": unread_count
            })

        return result
