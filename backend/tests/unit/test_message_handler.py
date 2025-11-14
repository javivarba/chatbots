"""
Unit tests for MessageHandler service.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.message_handler import MessageHandler
from app.utils.database import execute_query


class TestMessageHandlerInit:
    """Test MessageHandler initialization."""

    def test_init_sets_db_path(self, test_db):
        """Test that initialization sets the database path."""
        handler = MessageHandler()
        assert handler.db_path == 'bjj_academy.db'

    @patch('app.services.message_handler.OpenAI')
    def test_init_with_openai(self, mock_openai, test_db):
        """Test initialization with OpenAI available."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key-12345'}):
            handler = MessageHandler()
            assert handler.ai_enabled is True


class TestGetOrCreateLead:
    """Test _get_or_create_lead method."""

    def test_create_new_lead(self, test_db):
        """Test creating a new lead."""
        handler = MessageHandler()
        handler.db_path = test_db

        lead_id = handler._get_or_create_lead('+50611111111', 'New User')

        assert lead_id > 0

        # Verify lead was created
        results = execute_query(
            "SELECT * FROM lead WHERE id = ?",
            (lead_id,),
            db_path=test_db
        )
        assert len(results) == 1
        assert results[0]['phone_number'] == '+50611111111'
        assert results[0]['name'] == 'New User'

    def test_get_existing_lead(self, test_db, sample_lead):
        """Test getting an existing lead."""
        handler = MessageHandler()
        handler.db_path = test_db

        # Get the existing lead
        lead_id = handler._get_or_create_lead('+50612345678', 'Different Name')

        # Should return the existing lead ID
        assert lead_id == sample_lead


class TestGetOrCreateConversation:
    """Test _get_or_create_conversation method."""

    def test_create_new_conversation(self, test_db, sample_lead):
        """Test creating a new conversation."""
        handler = MessageHandler()
        handler.db_path = test_db

        conv_id = handler._get_or_create_conversation(sample_lead)

        assert conv_id > 0

        # Verify conversation was created
        results = execute_query(
            "SELECT * FROM conversation WHERE id = ?",
            (conv_id,),
            db_path=test_db
        )
        assert len(results) == 1
        assert results[0]['lead_id'] == sample_lead
        assert results[0]['status'] == 'active'

    def test_get_existing_conversation(self, test_db, sample_conversation, sample_lead):
        """Test getting an existing active conversation."""
        handler = MessageHandler()
        handler.db_path = test_db

        conv_id = handler._get_or_create_conversation(sample_lead)

        # Should return the existing conversation ID
        assert conv_id == sample_conversation


class TestSaveMessage:
    """Test _save_message method."""

    def test_save_message(self, test_db, sample_conversation):
        """Test saving a message."""
        handler = MessageHandler()
        handler.db_path = test_db

        handler._save_message(
            sample_conversation,
            'user',
            'Test message content',
            'greeting'
        )

        # Verify message was saved
        results = execute_query(
            "SELECT * FROM message WHERE conversation_id = ?",
            (sample_conversation,),
            db_path=test_db
        )
        assert len(results) == 1
        assert results[0]['sender'] == 'user'
        assert results[0]['content'] == 'Test message content'
        assert results[0]['intent_detected'] == 'greeting'


class TestGetLeadInfo:
    """Test _get_lead_info method."""

    def test_get_lead_info_success(self, test_db, sample_lead):
        """Test getting lead info successfully."""
        handler = MessageHandler()
        handler.db_path = test_db

        info = handler._get_lead_info(sample_lead)

        assert info['id'] == sample_lead
        assert info['phone'] == '+50612345678'
        assert info['name'] == 'Test User'
        assert info['status'] == 'new'

    def test_get_lead_info_not_found(self, test_db):
        """Test getting lead info for non-existent lead."""
        handler = MessageHandler()
        handler.db_path = test_db

        info = handler._get_lead_info(9999)

        assert info == {}


class TestGetAcademyInfo:
    """Test _get_academy_info method."""

    def test_get_academy_info(self, test_db):
        """Test getting academy info."""
        handler = MessageHandler()
        handler.db_path = test_db

        info = handler._get_academy_info()

        assert 'name' in info
        assert 'phone' in info
        assert info['name'] == 'BJJ Mingo Test'


class TestGetConversationHistory:
    """Test _get_conversation_history method."""

    def test_get_conversation_history(self, test_db, sample_conversation):
        """Test getting conversation history."""
        handler = MessageHandler()
        handler.db_path = test_db

        # Add some messages
        handler._save_message(sample_conversation, 'user', 'Message 1')
        handler._save_message(sample_conversation, 'assistant', 'Response 1')
        handler._save_message(sample_conversation, 'user', 'Message 2')

        history = handler._get_conversation_history(sample_conversation, limit=5)

        assert len(history) == 3
        # Should be in chronological order
        assert history[0]['content'] == 'Message 1'
        assert history[1]['content'] == 'Response 1'
        assert history[2]['content'] == 'Message 2'

    def test_get_conversation_history_with_limit(self, test_db, sample_conversation):
        """Test conversation history respects limit."""
        handler = MessageHandler()
        handler.db_path = test_db

        # Add many messages
        for i in range(10):
            handler._save_message(sample_conversation, 'user', f'Message {i}')

        history = handler._get_conversation_history(sample_conversation, limit=3)

        assert len(history) == 3
        # Should get the most recent 3
        assert history[0]['content'] == 'Message 7'
        assert history[2]['content'] == 'Message 9'


class TestUpdateLeadStatus:
    """Test _update_lead_status method."""

    def test_update_status_to_interested(self, test_db, sample_lead):
        """Test updating lead status based on interest."""
        handler = MessageHandler()
        handler.db_path = test_db

        handler._update_lead_status(sample_lead, 'Quiero agendar una clase')

        # Verify status was updated
        results = execute_query(
            "SELECT status, interest_level FROM lead WHERE id = ?",
            (sample_lead,),
            db_path=test_db
        )
        assert results[0]['status'] == 'interested'
        assert results[0]['interest_level'] == 8

    def test_update_status_to_contacted(self, test_db, sample_lead):
        """Test updating lead status to contacted."""
        handler = MessageHandler()
        handler.db_path = test_db

        handler._update_lead_status(sample_lead, 'Hola')

        # Verify status was updated
        results = execute_query(
            "SELECT status FROM lead WHERE id = ?",
            (sample_lead,),
            db_path=test_db
        )
        assert results[0]['status'] == 'contacted'


class TestProcessMessage:
    """Test process_message method (integration test with mocks)."""

    @patch('app.services.message_handler.OpenAI')
    def test_process_message_with_ai(self, mock_openai_class, test_db, mock_openai_client):
        """Test processing a message with AI."""
        # Setup mock
        mock_openai_class.return_value = mock_openai_client

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            handler = MessageHandler()
            handler.db_path = test_db

            response = handler.process_message('+50611111111', 'Hola', 'Test User')

            assert response is not None
            assert len(response) > 0

    def test_process_message_creates_lead_and_conversation(self, test_db):
        """Test that processing a message creates lead and conversation."""
        handler = MessageHandler()
        handler.db_path = test_db
        handler.ai_enabled = False  # Disable AI for this test

        response = handler.process_message('+50699999999', 'Test message', 'New User')

        # Verify lead was created
        lead_results = execute_query(
            "SELECT * FROM lead WHERE phone_number = ?",
            ('+50699999999',),
            db_path=test_db
        )
        assert len(lead_results) == 1

        # Verify conversation was created
        lead_id = lead_results[0]['id']
        conv_results = execute_query(
            "SELECT * FROM conversation WHERE lead_id = ?",
            (lead_id,),
            db_path=test_db
        )
        assert len(conv_results) == 1
