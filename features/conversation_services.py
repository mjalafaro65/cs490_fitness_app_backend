from db import db
from models import Conversations, ConversationParticipants, CoachClientRelationships

def create_conversation(participant_ids, conversation_type, relationship_id=None):
    participant_ids = set(participant_ids)

    # Relationship validation (if needed)
    if relationship_id:
        relationship = CoachClientRelationships.query.filter_by(
            relationship_id=relationship_id
        ).first()

        if not relationship:
            raise Exception("Invalid relationship")
        
    # DIRECT CHAT DEDUP
    if conversation_type == "direct" and len(participant_ids) == 2:
        existing = Conversations.query.join(ConversationParticipants).filter(
            ConversationParticipants.user_id.in_(participant_ids),
            Conversations.conversation_type == "direct"
        ).group_by(Conversations.conversation_id).first()

        if existing:
            return existing

    # RELATIONSHIP DEDUP
    if relationship_id:
        existing = Conversations.query.filter_by(
            relationship_id=relationship_id
        ).first()

        if existing:
            return existing

    # CREATE CONVERSATION
    conversation = Conversations(
        relationship_id=relationship_id,
        conversation_type=conversation_type
    )

    db.session.add(conversation)
    db.session.flush()

    # 5. ADD PARTICIPANTS
    db.session.add_all([
        ConversationParticipants(
            conversation_id=conversation.conversation_id,
            user_id=uid
        )
        for uid in participant_ids
    ])

    db.session.commit()

    return conversation
