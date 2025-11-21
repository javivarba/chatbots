"""
Unit tests for ReminderService - SQLALCHEMY + POSTGRESQL + CLASSREMINDER
"""

import pytest
from datetime import datetime, timedelta
from app.services.reminder_service import ReminderService
from app.models import Lead, ClassReminder, ReminderStatus, Academy
from app import db


class TestReminderServiceInit:
    """Test ReminderService initialization."""

    def test_init_loads_horarios(self, test_db):
        """Test that initialization loads schedule data."""
        service = ReminderService()
        assert hasattr(service, 'horarios')
        assert 'adultos_jiujitsu' in service.horarios
        assert 'adultos_striking' in service.horarios
        assert 'kids' in service.horarios
        assert 'juniors' in service.horarios

    def test_init_loads_notifier(self, test_db):
        """Test that notifier is initialized (may be None in tests)."""
        service = ReminderService()
        assert hasattr(service, 'notifier')


class TestScheduleTrialWeekReminders:
    """Test schedule_trial_week_reminders method."""

    def test_schedule_reminders_success(self, test_db, sample_lead):
        """Test successfully scheduling reminders for a trial week."""
        service = ReminderService()

        # Schedule for next week
        start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        result = service.schedule_trial_week_reminders(
            lead_id=sample_lead,
            trial_week_id=None,
            clase_tipo='adultos_jiujitsu',
            start_date=start_date
        )

        assert result['success'] is True
        assert 'count' in result
        assert result['count'] > 0
        assert 'reminders' in result

        # Verify reminders were created in database
        reminders = ClassReminder.query.filter_by(lead_id=sample_lead).all()
        assert len(reminders) == result['count']

        # Verify all reminders are PENDING
        for reminder in reminders:
            assert reminder.status == ReminderStatus.PENDING
            assert reminder.class_type == 'adultos_jiujitsu'
            assert reminder.send_at is not None
            assert reminder.class_datetime is not None

    def test_schedule_reminders_invalid_lead(self, test_db):
        """Test scheduling reminders with invalid lead ID."""
        service = ReminderService()

        result = service.schedule_trial_week_reminders(
            lead_id=99999,  # Non-existent lead
            trial_week_id=None,
            clase_tipo='adultos_jiujitsu',
            start_date='2025-12-01'
        )

        assert result['success'] is False
        assert 'Lead no encontrado' in result['message']

    def test_schedule_reminders_invalid_class_type(self, test_db, sample_lead):
        """Test scheduling reminders with invalid class type."""
        service = ReminderService()

        result = service.schedule_trial_week_reminders(
            lead_id=sample_lead,
            trial_week_id=None,
            clase_tipo='invalid_class_type',
            start_date='2025-12-01'
        )

        assert result['success'] is False
        assert 'Tipo de clase no' in result['message']

    def test_reminders_sent_24_hours_before(self, test_db, sample_lead):
        """Test that reminders are scheduled 24 hours before each class."""
        service = ReminderService()

        # Use a specific date for predictable testing
        start_date = '2025-12-01'  # Monday

        result = service.schedule_trial_week_reminders(
            lead_id=sample_lead,
            trial_week_id=None,
            clase_tipo='adultos_jiujitsu',  # Mon-Fri at 18:00
            start_date=start_date
        )

        assert result['success'] is True

        reminders = ClassReminder.query.filter_by(lead_id=sample_lead).all()

        # Verify 24-hour gap between send_at and class_datetime
        for reminder in reminders:
            time_diff = reminder.class_datetime - reminder.send_at
            # Should be exactly 24 hours
            assert time_diff == timedelta(hours=24)


class TestSendReminder:
    """Test send_reminder method."""

    def test_send_reminder_not_found(self, test_db):
        """Test sending a non-existent reminder."""
        service = ReminderService()

        result = service.send_reminder(99999)

        assert result['success'] is False
        assert 'no encontrado' in result['message']

    def test_send_reminder_not_pending(self, test_db, sample_lead):
        """Test sending a reminder that's already been sent."""
        service = ReminderService()

        # Create a reminder that's already sent
        academy = Academy.query.first()
        reminder = ClassReminder(
            lead_id=sample_lead,
            academy_id=academy.id,
            class_type='adultos_jiujitsu',
            class_datetime=datetime.now() + timedelta(days=1),
            send_at=datetime.now(),
            status=ReminderStatus.SENT
        )
        db.session.add(reminder)
        db.session.commit()

        result = service.send_reminder(reminder.id)

        assert result['success'] is False
        assert 'no está pendiente' in result['message']

    def test_send_reminder_without_notifier(self, test_db, sample_lead):
        """Test sending reminder when notifier is not available."""
        service = ReminderService()
        service.notifier = None  # Disable notifier

        # Create a pending reminder
        academy = Academy.query.first()
        reminder = ClassReminder(
            lead_id=sample_lead,
            academy_id=academy.id,
            class_type='adultos_jiujitsu',
            class_datetime=datetime.now() + timedelta(days=1),
            send_at=datetime.now() - timedelta(hours=1),
            status=ReminderStatus.PENDING
        )
        db.session.add(reminder)
        db.session.commit()

        result = service.send_reminder(reminder.id)

        assert result['success'] is False
        assert 'no disponible' in result['message']

        # Verify reminder was marked as failed
        reminder = ClassReminder.query.get(reminder.id)
        assert reminder.status == ReminderStatus.FAILED


class TestGetPendingReminders:
    """Test get_pending_reminders method."""

    def test_get_pending_reminders_empty(self, test_db):
        """Test getting pending reminders when none exist."""
        service = ReminderService()

        reminders = service.get_pending_reminders()

        assert reminders == []

    def test_get_pending_reminders_with_data(self, test_db, sample_lead):
        """Test getting pending reminders."""
        service = ReminderService()
        academy = Academy.query.first()

        # Create pending reminders
        for i in range(3):
            reminder = ClassReminder(
                lead_id=sample_lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(days=i+1),
                send_at=datetime.now() - timedelta(hours=1),  # Ready to send
                status=ReminderStatus.PENDING
            )
            db.session.add(reminder)

        # Create a future reminder (not ready to send)
        future_reminder = ClassReminder(
            lead_id=sample_lead,
            academy_id=academy.id,
            class_type='adultos_jiujitsu',
            class_datetime=datetime.now() + timedelta(days=10),
            send_at=datetime.now() + timedelta(days=9),  # Not ready yet
            status=ReminderStatus.PENDING
        )
        db.session.add(future_reminder)

        db.session.commit()

        # Get pending reminders
        reminders = service.get_pending_reminders()

        # Should only get the 3 that are ready to send
        assert len(reminders) == 3


class TestCancelReminder:
    """Test cancel_reminder method."""

    def test_cancel_reminder_success(self, test_db, sample_lead):
        """Test successfully canceling a reminder."""
        service = ReminderService()
        academy = Academy.query.first()

        reminder = ClassReminder(
            lead_id=sample_lead,
            academy_id=academy.id,
            class_type='adultos_jiujitsu',
            class_datetime=datetime.now() + timedelta(days=1),
            send_at=datetime.now(),
            status=ReminderStatus.PENDING
        )
        db.session.add(reminder)
        db.session.commit()

        result = service.cancel_reminder(reminder.id)

        assert result['success'] is True

        # Verify reminder was cancelled
        reminder = ClassReminder.query.get(reminder.id)
        assert reminder.status == ReminderStatus.CANCELLED

    def test_cancel_reminder_not_found(self, test_db):
        """Test canceling a non-existent reminder."""
        service = ReminderService()

        result = service.cancel_reminder(99999)

        assert result['success'] is False
        assert 'no encontrado' in result['message']


class TestCancelLeadFutureReminders:
    """Test cancel_lead_future_reminders method."""

    def test_cancel_future_reminders(self, test_db, sample_lead):
        """Test canceling all future reminders for a lead."""
        service = ReminderService()
        academy = Academy.query.first()

        # Create future pending reminders
        for i in range(3):
            reminder = ClassReminder(
                lead_id=sample_lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(days=i+1),
                send_at=datetime.now() + timedelta(days=i),
                status=ReminderStatus.PENDING
            )
            db.session.add(reminder)

        # Create a past reminder
        past_reminder = ClassReminder(
            lead_id=sample_lead,
            academy_id=academy.id,
            class_type='adultos_jiujitsu',
            class_datetime=datetime.now() - timedelta(days=1),
            send_at=datetime.now() - timedelta(days=2),
            status=ReminderStatus.SENT
        )
        db.session.add(past_reminder)

        db.session.commit()

        result = service.cancel_lead_future_reminders(sample_lead)

        assert result['success'] is True
        assert result['count'] == 3

        # Verify only future pending reminders were cancelled
        cancelled = ClassReminder.query.filter_by(
            lead_id=sample_lead,
            status=ReminderStatus.CANCELLED
        ).count()
        assert cancelled == 3

        # Verify past reminder was not affected
        past = ClassReminder.query.get(past_reminder.id)
        assert past.status == ReminderStatus.SENT


class TestGetLeadReminders:
    """Test get_lead_reminders method."""

    def test_get_lead_reminders_all(self, test_db, sample_lead):
        """Test getting all reminders for a lead."""
        service = ReminderService()
        academy = Academy.query.first()

        # Create various reminders
        statuses = [ReminderStatus.PENDING, ReminderStatus.SENT, ReminderStatus.FAILED]
        for status in statuses:
            reminder = ClassReminder(
                lead_id=sample_lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(days=1),
                send_at=datetime.now(),
                status=status
            )
            db.session.add(reminder)

        db.session.commit()

        reminders = service.get_lead_reminders(sample_lead)

        assert len(reminders) == 3

    def test_get_lead_reminders_filtered(self, test_db, sample_lead):
        """Test getting filtered reminders for a lead."""
        service = ReminderService()
        academy = Academy.query.first()

        # Create various reminders
        statuses = [ReminderStatus.PENDING, ReminderStatus.SENT, ReminderStatus.FAILED]
        for status in statuses:
            reminder = ClassReminder(
                lead_id=sample_lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(days=1),
                send_at=datetime.now(),
                status=status
            )
            db.session.add(reminder)

        db.session.commit()

        # Get only pending
        pending = service.get_lead_reminders(sample_lead, status=ReminderStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].status == ReminderStatus.PENDING
