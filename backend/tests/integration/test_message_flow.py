"""
Integration tests for complete message processing flow - MIGRATED TO SQLALCHEMY

Tests the entire flow from receiving a WhatsApp message to storing in database
and generating AI responses.
"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime

from app import db
from app.models import Lead, Conversation, Message, MessageDirection, LeadStatus
from app.services.message_handler import MessageHandler
from app.services.appointment_scheduler import AppointmentScheduler


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

                # Process message
                response = handler.process_message(
                    phone_number='+50699999999',
                    message='Hola',
                    name='Integration Test User'
                )

                # Verify response was generated
                assert response is not None
                assert len(response) > 0

                # Verify lead was created using SQLAlchemy
                lead = Lead.query.filter_by(phone='+50699999999').first()
                assert lead is not None
                assert lead.name == 'Integration Test User'
                # Status can be 'contacted', 'engaged', or 'new' depending on flow
                assert lead.status in ['contacted', LeadStatus.ENGAGED, LeadStatus.NEW]

                # Verify conversation was created
                conversation = Conversation.query.filter_by(lead_id=lead.id).first()
                assert conversation is not None
                assert conversation.is_active is True

                # Verify messages were saved
                messages = Message.query.filter_by(
                    conversation_id=conversation.id
                ).order_by(Message.created_at).all()

                assert len(messages) == 2
                assert messages[0].direction == MessageDirection.INBOUND
                assert messages[0].content == 'Hola'
                assert messages[1].direction == MessageDirection.OUTBOUND

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

                # Process message about classes
                response = handler.process_message(
                    phone_number='+50612345678',  # sample_lead's phone
                    message='Quiero agendar una clase de prueba',
                    name='Test User'
                )

                # Verify response
                assert response is not None

                # Verify lead status was updated using SQLAlchemy
                lead = Lead.query.get(sample_lead)
                assert lead.status == LeadStatus.INTERESTED
                assert lead.lead_score == 8

                # Verify messages
                messages = Message.query.filter_by(
                    conversation_id=sample_conversation
                ).order_by(Message.created_at).all()

                assert len(messages) >= 2
                # Check that user message contains keywords
                user_messages = [m for m in messages if m.direction == MessageDirection.INBOUND]
                assert any('agendar' in m.content.lower() for m in user_messages)


@pytest.mark.integration
class TestBookingFlow:
    """Test complete booking flow integration."""

    def test_trial_week_booking_flow(self, test_db, sample_lead):
        """
        Test complete trial week booking flow.

        Flow:
        1. User requests trial week
        2. System books trial week
        3. Trial is saved to database (using lead.trial_class_date)
        4. Lead status is updated
        5. Confirmation message is generated
        """
        scheduler = AppointmentScheduler()
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

        # Verify lead was updated using SQLAlchemy
        lead = Lead.query.get(sample_lead)
        assert lead.trial_class_date is not None
        assert lead.status == LeadStatus.SCHEDULED
        assert lead.lead_score == 9

        # Verify confirmation message contains key information
        message = result['message']
        assert 'Jiu-Jitsu Adultos' in message
        assert 'Lunes' in message or 'Martes' in message  # At least one day
        assert 'Waze' in message
        assert 'Qué traer' in message

    def test_duplicate_booking_prevention(self, test_db, sample_lead):
        """Test that duplicate trial bookings are prevented."""
        scheduler = AppointmentScheduler()
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

                phone = '+50688888888'
                name = 'Journey Test User'

                # Step 1: Initial greeting
                response1 = handler.process_message(phone, 'Hola!', name)
                assert response1 is not None

                # Verify lead created using SQLAlchemy
                lead = Lead.query.filter_by(phone=phone).first()
                assert lead is not None
                # Status can be 'contacted', 'engaged', or 'new' depending on flow
                assert lead.status in ['contacted', LeadStatus.ENGAGED, LeadStatus.NEW]
                lead_id = lead.id

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
                lead = Lead.query.get(lead_id)
                assert lead.status == LeadStatus.INTERESTED
                assert lead.lead_score == 8

                # Step 4: Book trial week
                scheduler = AppointmentScheduler()
                scheduler.notifier = None

                result = scheduler.book_trial_week(
                    lead_id,
                    'adultos_jiujitsu',
                    'Booked via WhatsApp integration test'
                )

                assert result['success'] is True

                # Step 5: Verify complete journey in database using SQLAlchemy
                # Check all messages saved
                conversations = Conversation.query.filter_by(lead_id=lead_id).all()
                assert len(conversations) == 1

                messages = Message.query.filter_by(
                    conversation_id=conversations[0].id
                ).all()
                # Should have user + assistant messages for each interaction
                assert len(messages) >= 6  # At least 3 exchanges

                # Check lead was updated with trial date
                lead = Lead.query.get(lead_id)
                assert lead.trial_class_date is not None
                assert lead.status == LeadStatus.SCHEDULED


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

                # Get lead and conversation using SQLAlchemy
                lead = Lead.query.filter_by(phone=phone).first()
                assert lead is not None

                conversations = Conversation.query.filter_by(lead_id=lead.id).all()
                assert len(conversations) == 1

                # Verify all messages saved in chronological order
                messages = Message.query.filter_by(
                    conversation_id=conversations[0].id
                ).order_by(Message.created_at).all()

                # Should have user messages + assistant responses
                assert len(messages) >= len(messages_to_send)

                # Verify messages are in order
                user_messages = [m for m in messages if m.direction == MessageDirection.INBOUND]
                for i, expected_msg in enumerate(messages_to_send):
                    assert user_messages[i].content == expected_msg
