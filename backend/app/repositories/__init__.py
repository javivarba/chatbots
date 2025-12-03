"""
Repository Pattern Implementation
Provides abstraction layer for data persistence operations
"""

from .base_repository import BaseRepository
from .user_repository import UserRepository
from .lead_repository import LeadRepository
from .conversation_repository import ConversationRepository
from .academy_repository import AcademyRepository

__all__ = [
    'BaseRepository',
    'UserRepository',
    'LeadRepository',
    'ConversationRepository',
    'AcademyRepository'
]
