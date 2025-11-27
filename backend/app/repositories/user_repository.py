"""
User Repository
Handles database operations for User model
"""

from typing import Optional, List
from datetime import datetime
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model with custom queries"""

    def __init__(self):
        super().__init__(User)

    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find user by username

        Args:
            username: Username to search for

        Returns:
            User or None
        """
        return self.find_one_by(username=username)

    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email

        Args:
            email: Email to search for

        Returns:
            User or None
        """
        return self.find_one_by(email=email)

    def find_active_users(self) -> List[User]:
        """
        Get all active users

        Returns:
            List of active users
        """
        return self.find_by(is_active=True)

    def find_by_role(self, role: str) -> List[User]:
        """
        Find users by role

        Args:
            role: Role to filter by (admin, staff, readonly)

        Returns:
            List of users with specified role
        """
        return self.find_by(role=role)

    def find_by_academy(self, academy_id: int) -> List[User]:
        """
        Find users by academy

        Args:
            academy_id: Academy ID

        Returns:
            List of users in academy
        """
        return self.find_by(academy_id=academy_id)

    def create_user(self, username: str, email: str, password: str,
                    role: str = 'staff', academy_id: Optional[int] = None) -> User:
        """
        Create new user with hashed password

        Args:
            username: Username
            email: Email
            password: Plain text password (will be hashed)
            role: User role (default: 'staff')
            academy_id: Optional academy ID

        Returns:
            Created user
        """
        user = User(
            username=username,
            email=email,
            role=role,
            academy_id=academy_id,
            is_active=True
        )
        user.set_password(password)

        from app import db
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        return user

    def update_password(self, user: User, new_password: str) -> User:
        """
        Update user password

        Args:
            user: User to update
            new_password: New plain text password

        Returns:
            Updated user
        """
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()

        from app import db
        db.session.commit()
        db.session.refresh(user)

        return user

    def update_last_login(self, user: User) -> User:
        """
        Update user's last login timestamp

        Args:
            user: User to update

        Returns:
            Updated user
        """
        return self.update(user, last_login=datetime.utcnow())

    def deactivate_user(self, user: User) -> User:
        """
        Deactivate user account

        Args:
            user: User to deactivate

        Returns:
            Updated user
        """
        return self.update(user, is_active=False)

    def activate_user(self, user: User) -> User:
        """
        Activate user account

        Args:
            user: User to activate

        Returns:
            Updated user
        """
        return self.update(user, is_active=True)

    def username_exists(self, username: str) -> bool:
        """
        Check if username already exists

        Args:
            username: Username to check

        Returns:
            True if username exists
        """
        return self.exists(username=username)

    def email_exists(self, email: str) -> bool:
        """
        Check if email already exists

        Args:
            email: Email to check

        Returns:
            True if email exists
        """
        return self.exists(email=email)
