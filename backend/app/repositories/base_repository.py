"""
Base Repository
Provides generic CRUD operations for all repositories
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from app import db

# Generic type for model classes
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self):
                super().__init__(User)
    """

    def __init__(self, model_class: type[T]):
        """
        Initialize repository with model class

        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class

    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get entity by ID

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        try:
            return db.session.get(self.model_class, id)
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error fetching {self.model_class.__name__} by ID: {str(e)}")

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """
        Get all entities with optional pagination

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities
        """
        try:
            query = db.session.query(self.model_class)

            if offset > 0:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error fetching all {self.model_class.__name__}: {str(e)}")

    def find_by(self, **filters) -> List[T]:
        """
        Find entities by filter criteria

        Args:
            **filters: Key-value pairs for filtering

        Returns:
            List of matching entities

        Example:
            users = user_repo.find_by(role='admin', is_active=True)
        """
        try:
            return db.session.query(self.model_class).filter_by(**filters).all()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error finding {self.model_class.__name__}: {str(e)}")

    def find_one_by(self, **filters) -> Optional[T]:
        """
        Find single entity by filter criteria

        Args:
            **filters: Key-value pairs for filtering

        Returns:
            Entity or None if not found

        Example:
            user = user_repo.find_one_by(username='admin')
        """
        try:
            return db.session.query(self.model_class).filter_by(**filters).first()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error finding {self.model_class.__name__}: {str(e)}")

    def create(self, **attributes) -> T:
        """
        Create new entity

        Args:
            **attributes: Entity attributes

        Returns:
            Created entity

        Example:
            user = user_repo.create(username='john', email='john@example.com')
        """
        try:
            entity = self.model_class(**attributes)
            db.session.add(entity)
            db.session.commit()
            db.session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error creating {self.model_class.__name__}: {str(e)}")

    def update(self, entity: T, **attributes) -> T:
        """
        Update entity attributes

        Args:
            entity: Entity to update
            **attributes: Attributes to update

        Returns:
            Updated entity

        Example:
            user = user_repo.get_by_id(1)
            user_repo.update(user, email='newemail@example.com')
        """
        try:
            for key, value in attributes.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            db.session.commit()
            db.session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error updating {self.model_class.__name__}: {str(e)}")

    def delete(self, entity: T) -> bool:
        """
        Delete entity

        Args:
            entity: Entity to delete

        Returns:
            True if deleted successfully

        Example:
            user = user_repo.get_by_id(1)
            user_repo.delete(user)
        """
        try:
            db.session.delete(entity)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error deleting {self.model_class.__name__}: {str(e)}")

    def delete_by_id(self, id: int) -> bool:
        """
        Delete entity by ID

        Args:
            id: Entity ID

        Returns:
            True if deleted successfully

        Example:
            user_repo.delete_by_id(1)
        """
        entity = self.get_by_id(id)
        if entity:
            return self.delete(entity)
        return False

    def count(self, **filters) -> int:
        """
        Count entities with optional filters

        Args:
            **filters: Optional filter criteria

        Returns:
            Count of entities

        Example:
            active_users = user_repo.count(is_active=True)
        """
        try:
            query = db.session.query(self.model_class)

            if filters:
                query = query.filter_by(**filters)

            return query.count()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error counting {self.model_class.__name__}: {str(e)}")

    def exists(self, **filters) -> bool:
        """
        Check if entity exists with given filters

        Args:
            **filters: Filter criteria

        Returns:
            True if at least one entity exists

        Example:
            exists = user_repo.exists(username='admin')
        """
        return self.count(**filters) > 0

    def bulk_create(self, entities_data: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple entities at once

        Args:
            entities_data: List of dictionaries with entity attributes

        Returns:
            List of created entities

        Example:
            users = user_repo.bulk_create([
                {'username': 'user1', 'email': 'user1@example.com'},
                {'username': 'user2', 'email': 'user2@example.com'}
            ])
        """
        try:
            entities = [self.model_class(**data) for data in entities_data]
            db.session.add_all(entities)
            db.session.commit()

            for entity in entities:
                db.session.refresh(entity)

            return entities
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error bulk creating {self.model_class.__name__}: {str(e)}")

    def refresh(self, entity: T) -> T:
        """
        Refresh entity from database

        Args:
            entity: Entity to refresh

        Returns:
            Refreshed entity
        """
        try:
            db.session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error refreshing {self.model_class.__name__}: {str(e)}")
