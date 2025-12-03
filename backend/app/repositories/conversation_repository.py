"""
Conversation Repository
Handles database operations for Conversation and Message models
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import desc
from app.models import Conversation, Message, MessageDirection
from app.repositories.base_repository import BaseRepository
from app import db


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation model with custom queries"""

    def __init__(self):
        super().__init__(Conversation)

    def find_by_lead(self, lead_id: int) -> List[Conversation]:
        """
        Find all conversations for a lead

        Args:
            lead_id: Lead ID

        Returns:
            List of conversations
        """
        try:
            return db.session.query(Conversation).filter_by(
                lead_id=lead_id
            ).order_by(desc(Conversation.last_message_at)).all()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error finding conversations: {str(e)}")

    def find_active_conversation(self, lead_id: int) -> Optional[Conversation]:
        """
        Find active conversation for a lead

        Args:
            lead_id: Lead ID

        Returns:
            Active conversation or None
        """
        try:
            return db.session.query(Conversation).filter_by(
                lead_id=lead_id,
                is_active=True
            ).order_by(desc(Conversation.last_message_at)).first()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error finding active conversation: {str(e)}")

    def get_or_create_conversation(self, lead_id: int) -> Conversation:
        """
        Get active conversation or create new one

        Args:
            lead_id: Lead ID

        Returns:
            Conversation (existing or new)
        """
        conversation = self.find_active_conversation(lead_id)

        if not conversation:
            conversation = self.create(
                lead_id=lead_id,
                is_active=True,
                last_message_at=datetime.now()
            )

        return conversation

    def close_conversation(self, conversation: Conversation) -> Conversation:
        """
        Close a conversation

        Args:
            conversation: Conversation to close

        Returns:
            Updated conversation
        """
        return self.update(conversation, is_active=False)

    def reopen_conversation(self, conversation: Conversation) -> Conversation:
        """
        Reopen a closed conversation

        Args:
            conversation: Conversation to reopen

        Returns:
            Updated conversation
        """
        return self.update(
            conversation,
            is_active=True,
            last_message_at=datetime.now()
        )

    def update_last_message_time(self, conversation: Conversation) -> Conversation:
        """
        Update last message timestamp

        Args:
            conversation: Conversation to update

        Returns:
            Updated conversation
        """
        return self.update(conversation, last_message_at=datetime.now())


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model with custom queries"""

    def __init__(self):
        super().__init__(Message)

    def find_by_conversation(self, conversation_id: int,
                           limit: Optional[int] = None,
                           offset: int = 0) -> List[Message]:
        """
        Find messages for a conversation

        Args:
            conversation_id: Conversation ID
            limit: Optional limit
            offset: Optional offset

        Returns:
            List of messages
        """
        try:
            query = db.session.query(Message).filter_by(
                conversation_id=conversation_id
            ).order_by(Message.created_at)

            if offset > 0:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            return query.all()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error finding messages: {str(e)}")

    def get_conversation_history(self, conversation_id: int,
                                limit: int = 10) -> List[Message]:
        """
        Get recent conversation history

        Args:
            conversation_id: Conversation ID
            limit: Number of messages to return

        Returns:
            List of recent messages
        """
        try:
            return db.session.query(Message).filter_by(
                conversation_id=conversation_id
            ).order_by(desc(Message.created_at)).limit(limit).all()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error getting conversation history: {str(e)}")

    def get_last_message(self, conversation_id: int) -> Optional[Message]:
        """
        Get last message in conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            Last message or None
        """
        try:
            return db.session.query(Message).filter_by(
                conversation_id=conversation_id
            ).order_by(desc(Message.created_at)).first()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error getting last message: {str(e)}")

    def create_message(self, conversation_id: int, content: str,
                      direction: MessageDirection) -> Message:
        """
        Create new message

        Args:
            conversation_id: Conversation ID
            content: Message content
            direction: Message direction (INBOUND/OUTBOUND)

        Returns:
            Created message
        """
        return self.create(
            conversation_id=conversation_id,
            content=content,
            direction=direction,
            created_at=datetime.now()
        )

    def count_messages_in_conversation(self, conversation_id: int) -> int:
        """
        Count messages in conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            Message count
        """
        return self.count(conversation_id=conversation_id)

    def find_inbound_messages(self, conversation_id: int) -> List[Message]:
        """
        Find all inbound messages in conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            List of inbound messages
        """
        return self.find_by(
            conversation_id=conversation_id,
            direction=MessageDirection.INBOUND
        )

    def find_outbound_messages(self, conversation_id: int) -> List[Message]:
        """
        Find all outbound messages in conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            List of outbound messages
        """
        return self.find_by(
            conversation_id=conversation_id,
            direction=MessageDirection.OUTBOUND
        )
