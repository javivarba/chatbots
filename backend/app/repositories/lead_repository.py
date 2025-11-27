"""
Lead Repository
Handles database operations for Lead model
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_
from app.models import Lead, LeadStatus
from app.repositories.base_repository import BaseRepository
from app import db


class LeadRepository(BaseRepository[Lead]):
    """Repository for Lead model with custom queries"""

    def __init__(self):
        super().__init__(Lead)

    def find_by_phone(self, phone: str) -> Optional[Lead]:
        """
        Find lead by phone number

        Args:
            phone: Phone number

        Returns:
            Lead or None
        """
        return self.find_one_by(phone=phone)

    def find_by_status(self, status: LeadStatus, limit: Optional[int] = None) -> List[Lead]:
        """
        Find leads by status

        Args:
            status: Lead status
            limit: Optional limit

        Returns:
            List of leads
        """
        try:
            query = db.session.query(Lead).filter_by(status=status)

            if limit:
                query = query.limit(limit)

            return query.all()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error finding leads by status: {str(e)}")

    def find_by_academy(self, academy_id: int) -> List[Lead]:
        """
        Find leads by academy

        Args:
            academy_id: Academy ID

        Returns:
            List of leads
        """
        return self.find_by(academy_id=academy_id)

    def find_scheduled_leads(self) -> List[Lead]:
        """
        Find leads with scheduled trial classes

        Returns:
            List of leads with trial_class_date set
        """
        try:
            return db.session.query(Lead).filter(
                Lead.trial_class_date.isnot(None)
            ).order_by(Lead.trial_class_date).all()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error finding scheduled leads: {str(e)}")

    def find_needs_followup(self, days: int = 3) -> List[Lead]:
        """
        Find leads that need follow-up (no contact in X days)

        Args:
            days: Number of days since last contact

        Returns:
            List of leads needing follow-up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            return db.session.query(Lead).filter(
                and_(
                    Lead.status.notin_([LeadStatus.SCHEDULED, LeadStatus.CONVERTED]),
                    or_(
                        Lead.last_contact_date == None,
                        Lead.last_contact_date < cutoff_date
                    )
                )
            ).all()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error finding leads needing followup: {str(e)}")

    def find_hot_leads(self, min_score: int = 7) -> List[Lead]:
        """
        Find hot leads (high lead score)

        Args:
            min_score: Minimum lead score

        Returns:
            List of hot leads
        """
        try:
            return db.session.query(Lead).filter(
                Lead.lead_score >= min_score
            ).order_by(desc(Lead.lead_score)).all()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error finding hot leads: {str(e)}")

    def create_lead(self, phone: str, name: Optional[str] = None,
                    source: str = 'whatsapp', academy_id: Optional[int] = None) -> Lead:
        """
        Create new lead

        Args:
            phone: Phone number
            name: Optional name
            source: Lead source (default: whatsapp)
            academy_id: Optional academy ID

        Returns:
            Created lead
        """
        return self.create(
            phone=phone,
            name=name,
            source=source,
            academy_id=academy_id,
            status=LeadStatus.NEW,
            lead_score=0
        )

    def update_status(self, lead: Lead, new_status: LeadStatus) -> Lead:
        """
        Update lead status

        Args:
            lead: Lead to update
            new_status: New status

        Returns:
            Updated lead
        """
        return self.update(
            lead,
            status=new_status,
            updated_at=datetime.now()
        )

    def update_lead_score(self, lead: Lead, score: int) -> Lead:
        """
        Update lead score

        Args:
            lead: Lead to update
            score: New score (0-10)

        Returns:
            Updated lead
        """
        if not 0 <= score <= 10:
            raise ValueError("Lead score must be between 0 and 10")

        return self.update(lead, lead_score=score)

    def schedule_trial_class(self, lead: Lead, trial_date: datetime) -> Lead:
        """
        Schedule trial class for lead

        Args:
            lead: Lead to update
            trial_date: Trial class date/time

        Returns:
            Updated lead
        """
        return self.update(
            lead,
            trial_class_date=trial_date,
            status=LeadStatus.SCHEDULED,
            updated_at=datetime.now()
        )

    def update_last_contact(self, lead: Lead) -> Lead:
        """
        Update last contact timestamp

        Args:
            lead: Lead to update

        Returns:
            Updated lead
        """
        return self.update(
            lead,
            last_contact_date=datetime.now(),
            updated_at=datetime.now()
        )

    def count_by_status(self) -> dict:
        """
        Count leads by status

        Returns:
            Dictionary with status counts
        """
        try:
            from sqlalchemy import func

            results = db.session.query(
                Lead.status,
                func.count(Lead.id)
            ).group_by(Lead.status).all()

            return {status: count for status, count in results}
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error counting leads by status: {str(e)}")

    def get_recent_leads(self, limit: int = 10) -> List[Lead]:
        """
        Get most recent leads

        Args:
            limit: Number of leads to return

        Returns:
            List of recent leads
        """
        try:
            return db.session.query(Lead).order_by(
                desc(Lead.created_at)
            ).limit(limit).all()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error getting recent leads: {str(e)}")

    def phone_exists(self, phone: str) -> bool:
        """
        Check if phone number already exists

        Args:
            phone: Phone number to check

        Returns:
            True if phone exists
        """
        return self.exists(phone=phone)
