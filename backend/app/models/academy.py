from datetime import datetime
from app import db

class Academy(db.Model):
    __tablename__ = 'academies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    website = db.Column(db.String(200))
    
    address_street = db.Column(db.String(200))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(50))
    address_zip = db.Column(db.String(20))
    address_country = db.Column(db.String(50), default='USA')
    timezone = db.Column(db.String(50), default='America/Los_Angeles')
    
    description = db.Column(db.Text)
    instructor_name = db.Column(db.String(100))
    instructor_belt = db.Column(db.String(20))
    
    ai_context = db.Column(db.Text)
    business_hours = db.Column(db.JSON, default=dict)
    class_types = db.Column(db.JSON, default=list)
    pricing_info = db.Column(db.JSON, default=dict)
    
    trial_class_enabled = db.Column(db.Boolean, default=True)
    trial_class_duration_days = db.Column(db.Integer, default=7)
    
    auto_followup_enabled = db.Column(db.Boolean, default=True)
    followup_delays_hours = db.Column(db.JSON, default=[24, 72, 168])
    
    is_active = db.Column(db.Boolean, default=True)
    subscription_plan = db.Column(db.String(20), default='free')
    subscription_status = db.Column(db.String(20), default='active')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    academy_id = db.Column(db.Integer, db.ForeignKey('academies.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='member')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
