"""
Integration tests for complete message processing flow.

Tests the entire flow from receiving a WhatsApp message to storing in database
and generating AI responses.
"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.message_handler import MessageHandler
from app.services.appointment_scheduler import AppointmentScheduler
from app.utils.database import execute_query


@pytest.mark.integration
class TestCompleteMessageFlow:
    """Test complete message processing flow."""

    def test_new_user_greeting_flow(self, test_db, mock_openai_client):
        """
        Test complete flow for a new user sending a greeting.

        Flow:
        1. New user sends "Hola"
        2. System creates lead
        3. System creates conversation
        4. System saves user message
        5. System generates AI response
        6. System saves AI response
        """
        with patch('app.services.message_handler.OpenAI') as mock_openai_class:
            mock_openai_class.return_value = mock_openai_client

            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                handler = MessageHandler()
                handler.db_path = test_db

                # Process message
                response = handler.process_message(
                    phone_number='+50699999999',
                    message='Hola',
                    name='Integration Test User'
                )

                # Verify response was generated
                assert response is not None
                assert len(response) > 0

                # Verify lead was created
                leads = execute_query(
                    "SELECT * FROM lead WHERE phone_number = ?",
                    ('+50699999999',),
                    db_path=test_db
                )
                assert len(leads) == 1
                assert leads[0]['name'] == 'Integration Test User'
                assert leads[0]['status'] == 'contacted'

                # Verify conversation was created
                conversations = execute_query(
                    "SELECT * FROM conversation WHERE lead_id = ?",
                    (leads[0]['id'],),
                    db_path=test_db
                )
                assert len(conversations) == 1
                assert conversations[0]['status'] == 'active'

                # Verify messages were saved
                messages = execute_query(
                    "SELECT * FROM message WHERE conversation_id = ? ORDER BY timestamp",
                    (conversations[0]['id'],),
                    db_path=test_db
                )
                assert len(messages) == 2
                assert messages[0]['sender'] == 'user'
                assert messages[0]['content'] == 'Hola'
                assert messages[1]['sender'] == 'assistant'

    def test_returning_user_class_inquiry_flow(self, test_db, sample_lead, sample_conversation, mock_openai_client):
        """
        Test flow for returning user asking about classes.

        Flow:
        1. Existing user asks about classes
        2. System updates lead status to 'interested'
        3. System saves message
        4. AI generates response with class info
        5. Response is saved
        """
        with patch('app.services.message_handler.OpenAI') as mock_openai_class:
            mock_openai_class.return_value = mock_openai_client

            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                handler = MessageHandler()
                handler.db_path = test_db

                # Process message about classes
                response = handler.process_message(
                    phone_number='+50612345678',  # sample_lead's phone
                    message='Quiero agendar una clase de prueba',
                    name='Test User'
                )

                # Verify response
                assert response is not None

                # Verify lead status was updated
                leads = execute_query(
                    "SELECT status, interest_level FROM lead WHERE id = ?",
                    (sample_lead,),
                    db_path=test_db
                )
                assert leads[0]['status'] == 'interested'
                assert leads[0]['interest_level'] == 8

                # Verify messages
                messages = execute_query(
                    "SELECT * FROM message WHERE conversation_id = ? ORDER BY timestamp",
                    (sample_conversation,),
                    db_path=test_db
                )
                assert len(messages) >= 2
                # Check that user message contains keywords
                user_messages = [m for m in messages if m['sender'] == 'user']
                assert any('agendar' in m['content'].lower() for m in user_messages)


@pytest.mark.integration
class TestBookingFlow:
    """Test complete booking flow integration."""

    def test_trial_week_booking_flow(self, test_db, sample_lead):
        """
        Test complete trial week booking flow.

        Flow:
        1. User requests trial week
        2. System books trial week
        3. Trial is saved to database
        4. Lead status is updated
        5. Confirmation message is generated
        """
        scheduler = AppointmentScheduler()
        scheduler.db_path = test_db
        scheduler.notifier = None  # Disable notifications for test

        # Book trial week
        result = scheduler.book_trial_week(
            lead_id=sample_lead,
            clase_tipo='adultos_jiujitsu',
            notes='Integration test booking'
        )

        # Verify booking was successful
        assert result['success'] is True
        assert 'trial_id' in result
        assert 'message' in result
        assert 'SEMANA DE PRUEBA CONFIRMADA' in result['message']

        # Verify trial was saved
        trials = execute_query(
            "SELECT * FROM trial_weeks WHERE lead_id = ?",
            (sample_lead,),
            db_path=test_db
        )
        assert len(trials) == 1
        assert trials[0]['clase_tipo'] == 'adultos_jiujitsu'
        assert trials[0]['status'] == 'active'
        assert trials[0]['notes'] == 'Integration test booking'

        # Verify confirmation message contains key information
        message = result['message']
        assert 'Jiu-Jitsu Adultos' in message
        assert 'Lunes' in message or 'Martes' in message  # At least one day
        assert 'Waze' in message
        assert 'Qué traer' in message

    def test_duplicate_booking_prevention(self, test_db, sample_lead):
        """Test that duplicate trial bookings are prevented."""
        scheduler = AppointmentScheduler()
        scheduler.db_path = test_db
        scheduler.notifier = None

        # Book first trial
        result1 = scheduler.book_trial_week(sample_lead, 'adultos_jiujitsu')
        assert result1['success'] is True

        # Attempt second booking
        result2 = scheduler.book_trial_week(sample_lead, 'adultos_striking')
        assert result2['success'] is False
        assert 'ya ten' in result2['message'].lower()


@pytest.mark.integration
class TestMessageAndBookingIntegration:
    """Test integration between message handling and booking."""

    def test_complete_user_journey(self, test_db, mock_openai_client):
        """
        Test complete user journey from first contact to booking.

        Journey:
        1. New user sends greeting
        2. User asks about classes
        3. User requests to book
        4. System processes booking
        5. User receives confirmation
        """
        with patch('app.services.message_handler.OpenAI') as mock_openai_class:
            mock_openai_class.return_value = mock_openai_client

            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                handler = MessageHandler()
                handler.db_path = test_db

                phone = '+50688888888'
                name = 'Journey Test User'

                # Step 1: Initial greeting
                response1 = handler.process_message(phone, 'Hola!', name)
                assert response1 is not None

                # Verify lead created
                leads = execute_query(
                    "SELECT * FROM lead WHERE phone_number = ?",
                    (phone,),
                    db_path=test_db
                )
                assert len(leads) == 1
                lead_id = leads[0]['id']
                assert leads[0]['status'] == 'contacted'

                # Step 2: Ask about classes
                response2 = handler.process_message(
                    phone,
                    '¿Cuáles son los horarios de jiu-jitsu?',
                    name
                )
                assert response2 is not None

                # Step 3: Request booking
                response3 = handler.process_message(
                    phone,
                    'Quiero agendar una clase de prueba',
                    name
                )
                assert response3 is not None

                # Verify lead status updated to interested
                leads = execute_query(
                    "SELECT status, interest_level FROM lead WHERE id = ?",
                    (lead_id,),
                    db_path=test_db
                )
                assert leads[0]['status'] == 'interested'
                assert leads[0]['interest_level'] == 8

                # Step 4: Book trial week
                scheduler = AppointmentScheduler()
                scheduler.db_path = test_db
                scheduler.notifier = None

                result = scheduler.book_trial_week(
                    lead_id,
                    'adultos_jiujitsu',
                    'Booked via WhatsApp integration test'
                )

                assert result['success'] is True

                # Step 5: Verify complete journey in database
                # Check all messages saved
                conversations = execute_query(
                    "SELECT * FROM conversation WHERE lead_id = ?",
                    (lead_id,),
                    db_path=test_db
                )
                assert len(conversations) == 1

                messages = execute_query(
                    "SELECT * FROM message WHERE conversation_id = ?",
                    (conversations[0]['id'],),
                    db_path=test_db
                )
                # Should have user + assistant messages for each interaction
                assert len(messages) >= 6  # At least 3 exchanges

                # Check trial booking
                trials = execute_query(
                    "SELECT * FROM trial_weeks WHERE lead_id = ?",
                    (lead_id,),
                    db_path=test_db
                )
                assert len(trials) == 1
                assert trials[0]['status'] == 'active'


@pytest.mark.integration
@pytest.mark.slow
class TestConversationHistory:
    """Test conversation history and context maintenance."""

    def test_conversation_context_maintained(self, test_db, mock_openai_client):
        """Test that conversation context is maintained across messages."""
        with patch('app.services.message_handler.OpenAI') as mock_openai_class:
            mock_openai_class.return_value = mock_openai_client

            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                handler = MessageHandler()
                handler.db_path = test_db

                phone = '+50677777777'

                # Send multiple messages
                messages_to_send = [
                    'Hola, quisiera información',
                    '¿Cuánto cuesta?',
                    '¿Dónde están ubicados?',
                    'Ok, gracias'
                ]

                for msg in messages_to_send:
                    handler.process_message(phone, msg, name='Context Test User')

                # Get lead and conversation
                leads = execute_query(
                    "SELECT * FROM lead WHERE phone_number = ?",
                    (phone,),
                    db_path=test_db
                )
                assert len(leads) == 1

                conversations = execute_query(
                    "SELECT * FROM conversation WHERE lead_id = ?",
                    (leads[0]['id'],),
                    db_path=test_db
                )
                assert len(conversations) == 1

                # Verify all messages saved in chronological order
                messages = execute_query(
                    """SELECT * FROM message
                       WHERE conversation_id = ?
                       ORDER BY timestamp ASC""",
                    (conversations[0]['id'],),
                    db_path=test_db
                )

                # Should have user messages + assistant responses
                assert len(messages) >= len(messages_to_send)

                # Verify messages are in order
                user_messages = [m for m in messages if m['sender'] == 'user']
                for i, expected_msg in enumerate(messages_to_send):
                    assert user_messages[i]['content'] == expected_msg
