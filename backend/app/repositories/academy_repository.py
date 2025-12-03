"""
Academy Repository
Handles database operations for Academy and TeamMember models
"""

from typing import Optional, List
from app.models import Academy, TeamMember
from app.repositories.base_repository import BaseRepository


class AcademyRepository(BaseRepository[Academy]):
    """Repository for Academy model with custom queries"""

    def __init__(self):
        super().__init__(Academy)

    def find_by_name(self, name: str) -> Optional[Academy]:
        """
        Find academy by name

        Args:
            name: Academy name

        Returns:
            Academy or None
        """
        return self.find_one_by(name=name)

    def get_first_academy(self) -> Optional[Academy]:
        """
        Get first academy (for single-academy setups)

        Returns:
            First academy or None
        """
        academies = self.get_all(limit=1)
        return academies[0] if academies else None

    def create_academy(self, name: str, location: Optional[str] = None,
                      phone: Optional[str] = None,
                      schedule: Optional[str] = None) -> Academy:
        """
        Create new academy

        Args:
            name: Academy name
            location: Optional location
            phone: Optional phone
            schedule: Optional schedule

        Returns:
            Created academy
        """
        return self.create(
            name=name,
            location=location,
            phone=phone,
            schedule=schedule
        )


class TeamMemberRepository(BaseRepository[TeamMember]):
    """Repository for TeamMember model with custom queries"""

    def __init__(self):
        super().__init__(TeamMember)

    def find_by_academy(self, academy_id: int) -> List[TeamMember]:
        """
        Find team members by academy

        Args:
            academy_id: Academy ID

        Returns:
            List of team members
        """
        return self.find_by(academy_id=academy_id)

    def find_by_name(self, name: str) -> Optional[TeamMember]:
        """
        Find team member by name

        Args:
            name: Member name

        Returns:
            Team member or None
        """
        return self.find_one_by(name=name)

    def create_team_member(self, academy_id: int, name: str,
                          role: Optional[str] = None,
                          bio: Optional[str] = None) -> TeamMember:
        """
        Create new team member

        Args:
            academy_id: Academy ID
            name: Member name
            role: Optional role
            bio: Optional bio

        Returns:
            Created team member
        """
        return self.create(
            academy_id=academy_id,
            name=name,
            role=role,
            bio=bio
        )

    def get_academy_instructors(self, academy_id: int) -> List[TeamMember]:
        """
        Get instructors for academy (team members with 'instructor' role)

        Args:
            academy_id: Academy ID

        Returns:
            List of instructors
        """
        try:
            from app import db
            return db.session.query(TeamMember).filter(
                TeamMember.academy_id == academy_id,
                TeamMember.role.ilike('%instructor%')
            ).all()
        except Exception as e:
            from app import db
            db.session.rollback()
            raise Exception(f"Error getting instructors: {str(e)}")
