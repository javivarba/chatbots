"""
Unit tests for AppointmentScheduler service - MIGRATED TO SQLALCHEMY
"""

import pytest
from datetime import datetime, timedelta
from app.services.appointment_scheduler import AppointmentScheduler
from app.models import Lead, Academy, LeadStatus
from app import db


class TestAppointmentSchedulerInit:
    """Test AppointmentScheduler initialization."""

    def test_init_loads_horarios(self, test_db):
        """Test that initialization loads schedule data."""
        scheduler = AppointmentScheduler()
        assert hasattr(scheduler, 'horarios')
        assert 'adultos_jiujitsu' in scheduler.horarios


class TestGetNextClassDate:
    """Test _get_next_class_date method."""

    def test_get_next_class_date_jiu_jitsu(self, test_db):
        """Test getting next class date for Jiu-Jitsu."""
        scheduler = AppointmentScheduler()
        next_date = scheduler._get_next_class_date('adultos_jiujitsu')

        assert next_date is not None
        assert isinstance(next_date, datetime)
        # Should be in the future
        assert next_date > datetime.now()
        # Should be a weekday (0-4 = Monday-Friday)
        assert next_date.weekday() in [0, 1, 2, 3, 4]


class TestBookTrialWeek:
    """Test book_trial_week method."""

    def test_book_trial_week_success(self, test_db, sample_lead):
        """Test successfully booking a trial week."""
        scheduler = AppointmentScheduler()
        scheduler.notifier = None  # Disable notifications for test

        result = scheduler.book_trial_week(
            sample_lead,
            'adultos_jiujitsu',
            'Test booking notes'
        )

        assert result['success'] is True
        assert 'message' in result
        assert 'trial_id' in result

        # Verify lead was updated using SQLAlchemy
        lead = Lead.query.get(sample_lead)
        assert lead is not None
        assert lead.trial_class_date is not None
        assert lead.status == LeadStatus.SCHEDULED
        assert lead.lead_score == 9

    def test_book_trial_week_duplicate_prevention(self, test_db, sample_lead):
        """Test that duplicate trial weeks are prevented."""
        scheduler = AppointmentScheduler()
        scheduler.notifier = None

        # Book first trial
        result1 = scheduler.book_trial_week(sample_lead, 'adultos_jiujitsu')
        assert result1['success'] is True

        # Try to book second trial
        result2 = scheduler.book_trial_week(sample_lead, 'adultos_striking')
        assert result2['success'] is False
        assert 'ya ten' in result2['message'].lower()  # "ya tenés"

    def test_book_trial_week_with_notification(self, test_db, sample_lead, mocker):
        """Test booking trial week with notification."""
        scheduler = AppointmentScheduler()

        # Mock notifier
        mock_notifier = mocker.Mock()
        mock_notifier.notify_new_trial_booking.return_value = {
            'success': True,
            'message': 'Notification sent'
        }
        scheduler.notifier = mock_notifier

        result = scheduler.book_trial_week(sample_lead, 'adultos_jiujitsu', 'With notification')

        assert result['success'] is True
        # Verify notifier was called
        mock_notifier.notify_new_trial_booking.assert_called_once()


class TestGetDiasTexto:
    """Test _get_dias_texto method."""

    def test_get_dias_texto(self, test_db):
        """Test converting day numbers to text."""
        scheduler = AppointmentScheduler()

        # Test weekdays (1=Lunes, 5=Viernes in the code)
        text = scheduler._get_dias_texto([1, 2, 3, 4, 5])
        assert 'Lunes' in text
        assert 'Martes' in text
        assert 'Viernes' in text

    def test_get_dias_texto_single_day(self, test_db):
        """Test converting single day."""
        scheduler = AppointmentScheduler()
        text = scheduler._get_dias_texto([1])
        assert text == 'Lunes'


class TestGetPhone:
    """Test _get_phone method."""

    def test_get_phone_from_db(self, test_db):
        """Test getting phone from database."""
        scheduler = AppointmentScheduler()

        phone = scheduler._get_phone()
        # Should get from test DB or return default
        assert phone is not None
        assert '+' in phone

    def test_get_phone_default(self, test_db):
        """Test getting default phone when DB has none."""
        scheduler = AppointmentScheduler()

        # Clear academies table using SQLAlchemy
        Academy.query.delete()
        db.session.commit()

        phone = scheduler._get_phone()
        assert phone == '+506-8888-8888'


class TestFormatAvailableSlotsMessage:
    """Test format_available_slots_message method."""

    def test_format_empty_slots(self, test_db):
        """Test formatting message with no slots."""
        scheduler = AppointmentScheduler()
        message = scheduler.format_available_slots_message([])

        assert 'no hay horarios disponibles' in message.lower()

    def test_format_with_slots(self, test_db):
        """Test formatting message with available slots."""
        scheduler = AppointmentScheduler()

        slots = [
            {
                'datetime': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 18:00'),
                'day': 'Lunes',
                'time': '18:00',
                'clase_tipo': 'adultos_jiujitsu'
            },
            {
                'datetime': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d 18:00'),
                'day': 'Martes',
                'time': '18:00',
                'clase_tipo': 'adultos_jiujitsu'
            }
        ]

        message = scheduler.format_available_slots_message(slots, 'adultos_jiujitsu')

        assert 'horarios disponibles' in message.lower()
        assert 'Lunes' in message or 'Martes' in message  # At least one day should be mentioned


class TestIntegrationBookingFlow:
    """Integration tests for complete booking flow."""

    def test_complete_booking_flow(self, test_db):
        """Test complete flow from lead creation to trial booking."""
        # Create lead using SQLAlchemy
        academy = Academy.query.first()

        lead = Lead(
            academy_id=academy.id,
            phone='+50644444444',
            name='Flow Test User',
            status=LeadStatus.NEW,
            source='whatsapp',
            lead_score=5,
            created_at=datetime.now()
        )
        db.session.add(lead)
        db.session.commit()
        lead_id = lead.id

        # Book trial
        scheduler = AppointmentScheduler()
        scheduler.notifier = None

        result = scheduler.book_trial_week(lead_id, 'adultos_jiujitsu', 'Integration test')

        # Verify everything
        assert result['success'] is True

        # Check lead was updated using SQLAlchemy
        lead = Lead.query.get(lead_id)
        assert lead.trial_class_date is not None
        assert lead.status == LeadStatus.SCHEDULED

        # Verify message has key information
        message = result['message']
        assert 'SEMANA DE PRUEBA CONFIRMADA' in message
        assert 'Jiu-Jitsu Adultos' in message
        assert 'Waze' in message
        assert 'Qué traer' in message
