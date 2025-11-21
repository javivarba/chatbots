"""
Reminder models for BJJ Academy Bot
Handles class reminders and notifications
"""

from datetime import datetime
from enum import Enum
from app import db


class ReminderStatus(str, Enum):
    """Status of a reminder"""
    PENDING = 'pending'      # Reminder scheduled but not sent
    SENT = 'sent'           # Reminder successfully sent
    FAILED = 'failed'       # Failed to send reminder
    CANCELLED = 'cancelled' # Reminder cancelled (e.g., class cancelled)


class ClassReminder(db.Model):
    """
    Represents a scheduled reminder for a class.

    Reminders are created when a trial week is booked and are sent
    24 hours before each class during the trial period.
    """
    __tablename__ = 'class_reminders'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    academy_id = db.Column(db.Integer, db.ForeignKey('academies.id'), nullable=False)

    # Class information
    class_type = db.Column(db.String(50), nullable=False)  # adultos_jiujitsu, kids, etc.
    class_datetime = db.Column(db.DateTime, nullable=False, index=True)  # When the class happens

    # Reminder scheduling
    send_at = db.Column(db.DateTime, nullable=False, index=True)  # When to send reminder (24h before)
    sent_at = db.Column(db.DateTime)  # When reminder was actually sent

    # Status tracking
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)

    # Message tracking
    message_sid = db.Column(db.String(100))  # Twilio message SID (if sent via Twilio)
    error_message = db.Column(db.Text)  # Error details if failed
    retry_count = db.Column(db.Integer, default=0)  # Number of send attempts

    # Additional info
    notes = db.Column(db.Text)  # Optional notes about this reminder

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_reminder_send_pending', 'send_at', 'status'),
        db.Index('idx_reminder_lead_class', 'lead_id', 'class_datetime'),
    )

    def __repr__(self):
        return (f'<ClassReminder {self.id}: '
                f'Lead {self.lead_id} - '
                f'{self.class_type} on {self.class_datetime.strftime("%Y-%m-%d %H:%M")} - '
                f'Status: {self.status}>')

    def mark_as_sent(self, message_sid=None):
        """Mark reminder as successfully sent"""
        self.status = ReminderStatus.SENT
        self.sent_at = datetime.utcnow()
        if message_sid:
            self.message_sid = message_sid
        db.session.commit()

    def mark_as_failed(self, error_message):
        """Mark reminder as failed with error message"""
        self.status = ReminderStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
        db.session.commit()

    def cancel(self):
        """Cancel this reminder"""
        self.status = ReminderStatus.CANCELLED
        db.session.commit()

    @property
    def is_pending(self):
        """Check if reminder is pending"""
        return self.status == ReminderStatus.PENDING

    @property
    def is_sent(self):
        """Check if reminder was sent"""
        return self.status == ReminderStatus.SENT

    @property
    def should_send_now(self):
        """Check if reminder should be sent now"""
        if self.status != ReminderStatus.PENDING:
            return False
        return datetime.utcnow() >= self.send_at

    @classmethod
    def get_pending_reminders(cls, limit=100):
        """
        Get pending reminders that are ready to be sent

        Args:
            limit: Maximum number of reminders to return

        Returns:
            List of ClassReminder objects ready to send
        """
        return cls.query.filter(
            cls.status == ReminderStatus.PENDING,
            cls.send_at <= datetime.utcnow()
        ).order_by(cls.send_at).limit(limit).all()

    @classmethod
    def get_reminders_for_lead(cls, lead_id, status=None):
        """
        Get all reminders for a specific lead

        Args:
            lead_id: The lead ID
            status: Optional status filter

        Returns:
            List of ClassReminder objects
        """
        query = cls.query.filter_by(lead_id=lead_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.class_datetime).all()

    @classmethod
    def cancel_future_reminders_for_lead(cls, lead_id):
        """
        Cancel all future reminders for a lead

        Args:
            lead_id: The lead ID

        Returns:
            Number of reminders cancelled
        """
        count = cls.query.filter(
            cls.lead_id == lead_id,
            cls.status == ReminderStatus.PENDING,
            cls.class_datetime > datetime.utcnow()
        ).update({
            'status': ReminderStatus.CANCELLED,
            'updated_at': datetime.utcnow()
        })
        db.session.commit()
        return count
