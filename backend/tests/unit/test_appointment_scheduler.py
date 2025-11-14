"""
Unit tests for AppointmentScheduler service.
"""

import pytest
from datetime import datetime, timedelta
from app.services.appointment_scheduler import AppointmentScheduler
from app.utils.database import execute_query, execute_insert


class TestAppointmentSchedulerInit:
    """Test AppointmentScheduler initialization."""

    def test_init_sets_db_path(self, test_db):
        """Test that initialization sets the database path."""
        scheduler = AppointmentScheduler()
        assert scheduler.db_path == 'bjj_academy.db'

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
        scheduler.db_path = test_db
        scheduler.notifier = None  # Disable notifications for test

        result = scheduler.book_trial_week(
            sample_lead,
            'adultos_jiujitsu',
            'Test booking notes'
        )

        assert result['success'] is True
        assert 'message' in result
        assert 'trial_id' in result

        # Verify trial was created in database
        trials = execute_query(
            "SELECT * FROM trial_weeks WHERE lead_id = ?",
            (sample_lead,),
            db_path=test_db
        )
        assert len(trials) == 1
        assert trials[0]['clase_tipo'] == 'adultos_jiujitsu'
        assert trials[0]['status'] == 'active'
        assert trials[0]['notes'] == 'Test booking notes'

    def test_book_trial_week_duplicate_prevention(self, test_db, sample_lead):
        """Test that duplicate trial weeks are prevented."""
        scheduler = AppointmentScheduler()
        scheduler.db_path = test_db
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
        scheduler.db_path = test_db

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
        scheduler.db_path = test_db

        phone = scheduler._get_phone()
        # Should get from test DB or return default
        assert phone is not None
        assert '+' in phone

    def test_get_phone_default(self, test_db):
        """Test getting default phone when DB has none."""
        scheduler = AppointmentScheduler()
        scheduler.db_path = test_db

        # Clear academies table to test default
        import sqlite3
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM academies")
        conn.commit()
        conn.close()

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
                'day_name': 'Lunes',
                'time': '18:00',
                'clase_tipo': 'adultos_jiujitsu'
            },
            {
                'datetime': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d 18:00'),
                'day_name': 'Martes',
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
        # Create lead in both tables
        lead_id = execute_insert(
            "INSERT INTO lead (phone_number, name, status) VALUES (?, ?, ?)",
            ('+50644444444', 'Flow Test User', 'new'),
            db_path=test_db
        )

        # Also insert in 'leads' table for appointment_scheduler
        execute_insert(
            "INSERT INTO leads (id, phone, name, status) VALUES (?, ?, ?, ?)",
            (lead_id, '+50644444444', 'Flow Test User', 'new'),
            db_path=test_db
        )

        # Book trial
        scheduler = AppointmentScheduler()
        scheduler.db_path = test_db
        scheduler.notifier = None

        result = scheduler.book_trial_week(lead_id, 'adultos_jiujitsu', 'Integration test')

        # Verify everything
        assert result['success'] is True

        # Check trial in DB
        trials = execute_query(
            "SELECT * FROM trial_weeks WHERE lead_id = ?",
            (lead_id,),
            db_path=test_db
        )
        assert len(trials) == 1

        # Verify message has key information
        message = result['message']
        assert 'SEMANA DE PRUEBA CONFIRMADA' in message
        assert 'Jiu-Jitsu Adultos' in message
        assert 'Waze' in message
        assert 'Qué traer' in message
