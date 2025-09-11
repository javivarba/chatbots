from datetime import datetime
from enum import Enum
from app import db

class LeadStatus(str, Enum):
    NEW = 'new'
    ENGAGED = 'engaged'
    INTERESTED = 'interested'
    SCHEDULED = 'scheduled'
    SHOWED_UP = 'showed_up'
    NO_SHOW = 'no_show'
    CONVERTED = 'converted'
    FOLLOW_UP = 'follow_up'
    RE_ENGAGED = 're_engaged'
    LOST = 'lost'

class LeadSource(str, Enum):
    WHATSAPP = 'whatsapp'
    FACEBOOK = 'facebook'
    INSTAGRAM = 'instagram'
    WEBSITE = 'website'
    REFERRAL = 'referral'
    OTHER = 'other'

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    academy_id = db.Column(db.Integer, db.ForeignKey('academies.id'), nullable=False)
    
    phone = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    
    source = db.Column(db.String(20), default='whatsapp')
    status = db.Column(db.String(20), default='new')
    
    goals = db.Column(db.Text)
    experience_level = db.Column(db.String(20))
    
    trial_class_date = db.Column(db.DateTime)
    converted_date = db.Column(db.DateTime)
    
    last_contact_date = db.Column(db.DateTime)
    follow_up_count = db.Column(db.Integer, default=0)
    
    lead_score = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def normalize_phone(self):
        import re
        if self.phone:
            normalized = re.sub(r'[^\d+]', '', self.phone)
            self.phone = normalized
    
    def calculate_lead_score(self):
        score = 0
        if self.name:
            score += 10
        if self.email:
            score += 10
        if self.status == 'interested':
            score += 20
        if self.status == 'scheduled':
            score += 30
        self.lead_score = min(100, score)
        return self.lead_score
