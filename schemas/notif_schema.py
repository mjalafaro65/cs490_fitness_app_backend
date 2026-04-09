from marshmallow import Schema, fields, validate
from models import CoachProfiles, CoachDocuments
from db import db

class NotificationTypeSchema(Schema):
    slug = fields.Str(dump_only=True)
    display_name = fields.Str(dump_only=True)
    priority = fields.Str(dump_only=True)

class NotificationResponseSchema(Schema):
    notification_id = fields.Int(dump_only=True)
    title = fields.Str(dump_only=True)
    body = fields.Str(dump_only=True)
    is_read = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    #nesting
    notification_type = fields.Nested(NotificationTypeSchema)