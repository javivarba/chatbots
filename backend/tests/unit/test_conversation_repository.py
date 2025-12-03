"""
Unit Tests for ConversationRepository and MessageRepository
Testing Repository Pattern implementation
Created: 25/11/2025
"""

import pytest
from datetime import datetime
from app.repositories.conversation_repository import ConversationRepository, MessageRepository
from app.models import Conversation, Message, MessageDirection, Lead
from app import db


@pytest.fixture
def conversation_repo():
    """Fixture para ConversationRepository"""
    return ConversationRepository()


@pytest.fixture
def message_repo():
    """Fixture para MessageRepository"""
    return MessageRepository()


@pytest.fixture
def sample_lead(app):
    """Fixture para crear un lead de prueba"""
    with app.app_context():
        lead = Lead(
            phone='+50612345678',
            name='Test User',
            source='whatsapp',
            status='new',
            lead_score=0,
            academy_id=1
        )
        db.session.add(lead)
        db.session.commit()
        yield lead

        # Cleanup
        try:
            db.session.delete(lead)
            db.session.commit()
        except:
            db.session.rollback()


@pytest.fixture
def sample_conversation(app, sample_lead):
    """Fixture para crear una conversación de prueba"""
    with app.app_context():
        conversation = Conversation(
            lead_id=sample_lead.id,
            academy_id=1,
            platform='whatsapp',
            is_active=True,
            message_count=0,
            inbound_count=0,
            outbound_count=0,
            started_at=datetime.now(),
            last_message_at=datetime.now()
        )
        db.session.add(conversation)
        db.session.commit()
        yield conversation

        # Cleanup
        try:
            db.session.delete(conversation)
            db.session.commit()
        except:
            db.session.rollback()


class TestConversationRepositoryBasicCRUD:
    """Tests para operaciones CRUD básicas de Conversation"""

    def test_create_conversation(self, app, conversation_repo, sample_lead):
        """Test crear conversación usando repository"""
        with app.app_context():
            conversation = conversation_repo.create(
                lead_id=sample_lead.id,
                academy_id=1,
                platform='whatsapp',
                is_active=True,
                message_count=0,
                inbound_count=0,
                outbound_count=0,
                started_at=datetime.now(),
                last_message_at=datetime.now()
            )

            assert conversation.id is not None
            assert conversation.lead_id == sample_lead.id
            assert conversation.is_active is True
            assert conversation.platform == 'whatsapp'

            # Cleanup
            db.session.delete(conversation)
            db.session.commit()

    def test_get_by_id(self, app, conversation_repo, sample_conversation):
        """Test obtener conversación por ID"""
        with app.app_context():
            conversation = conversation_repo.get_by_id(sample_conversation.id)

            assert conversation is not None
            assert conversation.id == sample_conversation.id
            assert conversation.lead_id == sample_conversation.lead_id

    def test_update_conversation(self, app, conversation_repo, sample_conversation):
        """Test actualizar conversación"""
        with app.app_context():
            updated = conversation_repo.update(
                sample_conversation,
                message_count=5,
                inbound_count=3,
                outbound_count=2
            )

            assert updated.message_count == 5
            assert updated.inbound_count == 3
            assert updated.outbound_count == 2


class TestConversationRepositoryQueries:
    """Tests para queries especializados de Conversation"""

    def test_find_by_lead(self, app, conversation_repo, sample_lead, sample_conversation):
        """Test buscar conversaciones por lead"""
        with app.app_context():
            conversations = conversation_repo.find_by_lead(sample_lead.id)

            assert len(conversations) > 0
            assert all(c.lead_id == sample_lead.id for c in conversations)

    def test_find_active_conversation(self, app, conversation_repo, sample_lead, sample_conversation):
        """Test buscar conversación activa"""
        with app.app_context():
            active = conversation_repo.find_active_conversation(sample_lead.id)

            assert active is not None
            assert active.is_active is True
            assert active.lead_id == sample_lead.id

    def test_find_active_conversation_not_found(self, app, conversation_repo):
        """Test buscar conversación activa que no existe"""
        with app.app_context():
            active = conversation_repo.find_active_conversation(99999)
            assert active is None

    def test_get_or_create_conversation_existing(self, app, conversation_repo, sample_lead, sample_conversation):
        """Test get_or_create con conversación existente"""
        with app.app_context():
            conversation = conversation_repo.get_or_create_conversation(sample_lead.id)

            assert conversation.id == sample_conversation.id
            assert conversation.is_active is True

    def test_get_or_create_conversation_new(self, app, conversation_repo):
        """Test get_or_create creando nueva conversación"""
        with app.app_context():
            # Crear lead temporal sin conversación
            lead = Lead(
                phone='+50699999999',
                name='No Conversation Lead',
                source='whatsapp',
                status='new',
                academy_id=1
            )
            db.session.add(lead)
            db.session.commit()

            conversation = conversation_repo.get_or_create_conversation(lead.id)

            assert conversation.id is not None
            assert conversation.lead_id == lead.id
            assert conversation.is_active is True

            # Cleanup
            db.session.delete(conversation)
            db.session.delete(lead)
            db.session.commit()

    def test_close_conversation(self, app, conversation_repo, sample_conversation):
        """Test cerrar conversación"""
        with app.app_context():
            closed = conversation_repo.close_conversation(sample_conversation)

            assert closed.is_active is False

            # Verificar que se guardó
            from_db = conversation_repo.get_by_id(sample_conversation.id)
            assert from_db.is_active is False

    def test_reopen_conversation(self, app, conversation_repo, sample_conversation):
        """Test reabrir conversación"""
        with app.app_context():
            # Primero cerrar
            conversation_repo.close_conversation(sample_conversation)

            # Luego reabrir
            reopened = conversation_repo.reopen_conversation(sample_conversation)

            assert reopened.is_active is True
            assert reopened.last_message_at is not None

    def test_update_last_message_time(self, app, conversation_repo, sample_conversation):
        """Test actualizar timestamp del último mensaje"""
        with app.app_context():
            original_time = sample_conversation.last_message_at

            updated = conversation_repo.update_last_message_time(sample_conversation)

            assert updated.last_message_at >= original_time


class TestMessageRepositoryBasicCRUD:
    """Tests para operaciones CRUD básicas de Message"""

    def test_create_message(self, app, message_repo, sample_conversation):
        """Test crear mensaje usando repository"""
        with app.app_context():
            message = message_repo.create_message(
                conversation_id=sample_conversation.id,
                content='Test message',
                direction=MessageDirection.INBOUND
            )

            assert message.id is not None
            assert message.conversation_id == sample_conversation.id
            assert message.content == 'Test message'
            assert message.direction == MessageDirection.INBOUND

            # Cleanup
            db.session.delete(message)
            db.session.commit()

    def test_get_by_id(self, app, message_repo, sample_conversation):
        """Test obtener mensaje por ID"""
        with app.app_context():
            # Crear mensaje
            message = message_repo.create_message(
                conversation_id=sample_conversation.id,
                content='Test',
                direction=MessageDirection.INBOUND
            )

            # Obtener
            retrieved = message_repo.get_by_id(message.id)

            assert retrieved is not None
            assert retrieved.id == message.id
            assert retrieved.content == 'Test'

            # Cleanup
            db.session.delete(message)
            db.session.commit()


class TestMessageRepositoryQueries:
    """Tests para queries especializados de Message"""

    def test_find_by_conversation(self, app, message_repo, sample_conversation):
        """Test buscar mensajes por conversación"""
        with app.app_context():
            # Crear varios mensajes
            msg1 = message_repo.create_message(
                sample_conversation.id, 'Message 1', MessageDirection.INBOUND
            )
            msg2 = message_repo.create_message(
                sample_conversation.id, 'Message 2', MessageDirection.OUTBOUND
            )

            messages = message_repo.find_by_conversation(sample_conversation.id)

            assert len(messages) >= 2
            assert all(m.conversation_id == sample_conversation.id for m in messages)

            # Cleanup
            db.session.delete(msg1)
            db.session.delete(msg2)
            db.session.commit()

    def test_find_by_conversation_with_limit(self, app, message_repo, sample_conversation):
        """Test buscar mensajes con límite"""
        with app.app_context():
            # Crear 3 mensajes
            for i in range(3):
                message_repo.create_message(
                    sample_conversation.id,
                    f'Message {i}',
                    MessageDirection.INBOUND
                )

            messages = message_repo.find_by_conversation(
                sample_conversation.id,
                limit=2
            )

            assert len(messages) == 2

            # Cleanup
            for msg in messages:
                db.session.delete(msg)
            db.session.commit()

    def test_get_conversation_history(self, app, message_repo, sample_conversation):
        """Test obtener historial de conversación"""
        with app.app_context():
            # Crear mensajes
            msg1 = message_repo.create_message(
                sample_conversation.id, 'First', MessageDirection.INBOUND
            )
            msg2 = message_repo.create_message(
                sample_conversation.id, 'Second', MessageDirection.OUTBOUND
            )

            history = message_repo.get_conversation_history(
                sample_conversation.id,
                limit=10
            )

            assert len(history) >= 2

            # Cleanup
            db.session.delete(msg1)
            db.session.delete(msg2)
            db.session.commit()

    def test_get_last_message(self, app, message_repo, sample_conversation):
        """Test obtener último mensaje"""
        with app.app_context():
            # Crear mensajes
            msg1 = message_repo.create_message(
                sample_conversation.id, 'First', MessageDirection.INBOUND
            )
            msg2 = message_repo.create_message(
                sample_conversation.id, 'Last', MessageDirection.OUTBOUND
            )

            last = message_repo.get_last_message(sample_conversation.id)

            assert last is not None
            assert last.content == 'Last'

            # Cleanup
            db.session.delete(msg1)
            db.session.delete(msg2)
            db.session.commit()

    def test_count_messages_in_conversation(self, app, message_repo, sample_conversation):
        """Test contar mensajes en conversación"""
        with app.app_context():
            # Crear mensajes
            msg1 = message_repo.create_message(
                sample_conversation.id, 'One', MessageDirection.INBOUND
            )
            msg2 = message_repo.create_message(
                sample_conversation.id, 'Two', MessageDirection.OUTBOUND
            )

            count = message_repo.count_messages_in_conversation(sample_conversation.id)

            assert count >= 2

            # Cleanup
            db.session.delete(msg1)
            db.session.delete(msg2)
            db.session.commit()

    def test_find_inbound_messages(self, app, message_repo, sample_conversation):
        """Test buscar mensajes entrantes"""
        with app.app_context():
            # Crear mensajes mixtos
            inbound1 = message_repo.create_message(
                sample_conversation.id, 'Inbound 1', MessageDirection.INBOUND
            )
            outbound = message_repo.create_message(
                sample_conversation.id, 'Outbound', MessageDirection.OUTBOUND
            )
            inbound2 = message_repo.create_message(
                sample_conversation.id, 'Inbound 2', MessageDirection.INBOUND
            )

            inbound_messages = message_repo.find_inbound_messages(sample_conversation.id)

            assert len(inbound_messages) >= 2
            assert all(m.direction == MessageDirection.INBOUND for m in inbound_messages)

            # Cleanup
            db.session.delete(inbound1)
            db.session.delete(outbound)
            db.session.delete(inbound2)
            db.session.commit()

    def test_find_outbound_messages(self, app, message_repo, sample_conversation):
        """Test buscar mensajes salientes"""
        with app.app_context():
            # Crear mensajes mixtos
            inbound = message_repo.create_message(
                sample_conversation.id, 'Inbound', MessageDirection.INBOUND
            )
            outbound1 = message_repo.create_message(
                sample_conversation.id, 'Outbound 1', MessageDirection.OUTBOUND
            )
            outbound2 = message_repo.create_message(
                sample_conversation.id, 'Outbound 2', MessageDirection.OUTBOUND
            )

            outbound_messages = message_repo.find_outbound_messages(sample_conversation.id)

            assert len(outbound_messages) >= 2
            assert all(m.direction == MessageDirection.OUTBOUND for m in outbound_messages)

            # Cleanup
            db.session.delete(inbound)
            db.session.delete(outbound1)
            db.session.delete(outbound2)
            db.session.commit()
