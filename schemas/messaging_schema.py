from marshmallow import Schema, fields, validate
from datetime import datetime

class MessageSchema(Schema):
    message_id = fields.Integer(dump_only=True)
    conversation_id = fields.Integer(required=True)
    sender_user_id = fields.Integer(required=True)
    body = fields.String(required=True, validate=validate.Length(min=1, max=1000))
    message_type = fields.String(required=True, validate=validate.OneOf(['text', 'image', 'file']))
    is_read = fields.Boolean(dump_only=True)
    read_at = fields.DateTime(dump_only=True)
    delivered_at = fields.DateTime(dump_only=True)
    sent_at = fields.DateTime(dump_only=True)
    deleted_at = fields.DateTime(dump_only=True)
    
    # Nested relationships
    sender = fields.Nested('UserSchema', dump_only=True, only=['user_id', 'first_name', 'last_name'])

class ConversationSchema(Schema):
    conversation_id = fields.Integer(dump_only=True)
    relationship_id = fields.Integer(required=True)
    conversation_type = fields.String(required=True, validate=validate.OneOf(['direct', 'group']))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Nested relationships
    participants = fields.List(fields.Nested('ConversationParticipantSchema'), dump_only=True)
    messages = fields.List(fields.Nested('MessageSchema'), dump_only=True)
    last_message = fields.Nested('MessageSchema', dump_only=True)

class ConversationParticipantSchema(Schema):
    participant_id = fields.Integer(dump_only=True)
    conversation_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    joined_at = fields.DateTime(dump_only=True)
    last_read_at = fields.DateTime(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    
    # Nested relationships
    user = fields.Nested('UserSchema', dump_only=True, only=['user_id', 'first_name', 'last_name'])

class CreateConversationSchema(Schema):
    relationship_id = fields.Integer(required=True)
    conversation_type = fields.String(required=True, validate=validate.OneOf(['direct', 'group']))
    participant_ids = fields.List(fields.Integer(), required=True)

class SendMessageSchema(Schema):
    body = fields.String(required=True, validate=validate.Length(min=1, max=1000))
    message_type = fields.String(required=False, validate=validate.OneOf(['text', 'image', 'file']), load_default='text')

class MarkMessageReadSchema(Schema):
    message_id = fields.Integer(required=True)

class OnlineUserSchema(Schema):
    user_id = fields.Integer(dump_only=True)
    is_online = fields.Boolean(dump_only=True)
    last_seen = fields.DateTime(dump_only=True)

class UserSchema(Schema):
    user_id = fields.Integer(dump_only=True)
    first_name = fields.String(dump_only=True)
    last_name = fields.String(dump_only=True)
    email = fields.String(dump_only=True)

# WebSocket message schemas
class SocketMessageSchema(Schema):
    type = fields.String(required=True)  # message, typing, read_receipt, etc.
    data = fields.Dict(required=True)
    conversation_id = fields.Integer(required=True)
    sender_user_id = fields.Integer(required=True)
    timestamp = fields.DateTime(dump_only=True)
