from datetime import datetime
from enum import Enum
from app import db

class MessageDirection(str, Enum):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    academy_id = db.Column(db.Integer, db.ForeignKey('academies.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    
    platform = db.Column(db.String(20), nullable=False)
    session_id = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    
    message_count = db.Column(db.Integer, default=0)
    inbound_count = db.Column(db.Integer, default=0)
    outbound_count = db.Column(db.Integer, default=0)
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    
    direction = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
