"""
Test de Sistema de Notificaciones y Recordatorios
Verifica que cuando un lead agenda una clase:
1. Se envía notificación a la academia
2. Se programan recordatorios 24 horas antes de cada clase
3. Los recordatorios se envían correctamente al lead

INTEGRADO CON SQLALCHEMY + POSTGRESQL (usando SQLite en tests)
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app import create_app, db
from app.models import Academy, Lead, LeadStatus, ClassReminder, ReminderStatus
from app.services.appointment_scheduler import AppointmentScheduler
from app.services.notification_service import NotificationService
from app.services.reminder_service import ReminderService


class TestBookingNotifications:
    """
    Tests para verificar el flujo completo de notificaciones y recordatorios
    """

    @pytest.fixture
    def app(self):
        """Crear aplicación Flask de prueba con SQLite en memoria"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with app.app_context():
            db.create_all()

            # Crear academy de prueba
            academy = Academy(
                name='BJJ Mingo Test',
                slug='bjj-mingo-test',
                email='test@bjjmingo.com',
                phone='+50688888888',
                address_street='Test Street',
                address_city='Santo Domingo',
                instructor_name='Test Instructor',
                description='Test Academy'
            )
            db.session.add(academy)
            db.session.commit()

            yield app

            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def lead(self, app):
        """Crear lead de prueba"""
        with app.app_context():
            academy = Academy.query.first()
            lead = Lead(
                academy_id=academy.id,
                phone='+50688887777',
                name='Juan Pérez',
                source='whatsapp',
                status=LeadStatus.NEW,
                lead_score=5,
                created_at=datetime.now()
            )
            db.session.add(lead)
            db.session.commit()

            return lead.id

    # ========== Tests de AppointmentScheduler.book_trial_week() ==========

    @patch('app.services.appointment_scheduler.NotificationService')
    @patch('app.tasks.reminder_tasks.schedule_trial_reminders')
    def test_book_trial_week_notifica_academia(self, mock_celery_task, mock_notification_service, app, lead):
        """
        Debe enviar notificación a la academia cuando se agenda una clase de prueba
        """
        with app.app_context():
            # Mock del NotificationService
            mock_notifier_instance = Mock()
            mock_notifier_instance.notify_new_trial_booking.return_value = {
                'success': True,
                'message': 'Notificación enviada',
                'sid': 'SM1234567890'
            }
            mock_notification_service.return_value = mock_notifier_instance

            # Mock de Celery task
            mock_celery_task.delay.return_value = Mock(id='task-123')

            # Crear scheduler
            scheduler = AppointmentScheduler()
            scheduler.notifier = mock_notifier_instance

            # Agendar semana de prueba
            result = scheduler.book_trial_week(
                lead_id=lead,
                clase_tipo='adultos_jiujitsu',
                notes='Test booking'
            )

            # Verificar resultado
            assert result['success'] is True
            assert 'confirmada' in result['message']

            # Verificar que se llamó notify_new_trial_booking
            mock_notifier_instance.notify_new_trial_booking.assert_called_once()

            # Verificar argumentos de la llamada
            call_args = mock_notifier_instance.notify_new_trial_booking.call_args[0]
            lead_info = call_args[0]
            trial_info = call_args[1]

            assert lead_info['name'] == 'Juan Pérez'
            assert lead_info['phone'] == '+50688887777'
            assert trial_info['clase_nombre'] == 'Jiu-Jitsu Adultos'

    @patch('app.services.appointment_scheduler.NotificationService')
    @patch('app.tasks.reminder_tasks.schedule_trial_reminders')
    def test_book_trial_week_programa_recordatorios_celery(self, mock_celery_task, mock_notification_service, app, lead):
        """
        Debe programar recordatorios usando Celery cuando se agenda una clase
        """
        with app.app_context():
            # Mock del NotificationService
            mock_notifier_instance = Mock()
            mock_notifier_instance.notify_new_trial_booking.return_value = {
                'success': True,
                'message': 'Notificación enviada'
            }
            mock_notification_service.return_value = mock_notifier_instance

            # Mock de Celery task
            mock_celery_task.delay.return_value = Mock(id='task-123')

            # Crear scheduler
            scheduler = AppointmentScheduler()
            scheduler.notifier = mock_notifier_instance

            # Agendar semana de prueba
            result = scheduler.book_trial_week(
                lead_id=lead,
                clase_tipo='adultos_jiujitsu',
                notes='Test booking'
            )

            # Verificar resultado
            assert result['success'] is True

            # Verificar que se llamó a Celery task
            mock_celery_task.delay.assert_called_once()

            # Verificar argumentos del task
            call_kwargs = mock_celery_task.delay.call_args[1]
            assert call_kwargs['lead_id'] == lead
            assert call_kwargs['clase_tipo'] == 'adultos_jiujitsu'

    @patch('app.services.appointment_scheduler.NotificationService')
    @patch('app.tasks.reminder_tasks.schedule_trial_reminders', side_effect=ImportError("Celery not available"))
    @patch('app.services.reminder_service.ReminderService')
    def test_book_trial_week_fallback_sin_celery(self, mock_reminder_service, mock_celery_task, mock_notification_service, app, lead):
        """
        Debe usar ReminderService directamente si Celery no está disponible
        """
        with app.app_context():
            # Mock del NotificationService
            mock_notifier_instance = Mock()
            mock_notifier_instance.notify_new_trial_booking.return_value = {
                'success': True,
                'message': 'Notificación enviada'
            }
            mock_notification_service.return_value = mock_notifier_instance

            # Mock del ReminderService
            mock_reminder_instance = Mock()
            mock_reminder_instance.schedule_trial_week_reminders.return_value = {
                'success': True,
                'count': 5
            }
            mock_reminder_service.return_value = mock_reminder_instance

            # Crear scheduler
            scheduler = AppointmentScheduler()
            scheduler.notifier = mock_notifier_instance

            # Agendar semana de prueba
            result = scheduler.book_trial_week(
                lead_id=lead,
                clase_tipo='adultos_jiujitsu',
                notes='Test booking'
            )

            # Verificar resultado
            assert result['success'] is True

    @patch('app.services.appointment_scheduler.NotificationService')
    def test_book_trial_week_actualiza_lead_status(self, mock_notification_service, app, lead):
        """
        Debe actualizar el status del lead a SCHEDULED
        """
        with app.app_context():
            # Mock del NotificationService
            mock_notifier_instance = Mock()
            mock_notifier_instance.notify_new_trial_booking.return_value = {
                'success': True,
                'message': 'Notificación enviada'
            }
            mock_notification_service.return_value = mock_notifier_instance

            # Crear scheduler
            scheduler = AppointmentScheduler()
            scheduler.notifier = mock_notifier_instance

            # Verificar status inicial
            lead_obj = Lead.query.get(lead)
            assert lead_obj.status == LeadStatus.NEW

            # Agendar semana de prueba
            result = scheduler.book_trial_week(
                lead_id=lead,
                clase_tipo='adultos_jiujitsu'
            )

            # Verificar resultado
            assert result['success'] is True

            # Verificar que el status cambió
            lead_obj = Lead.query.get(lead)
            assert lead_obj.status == LeadStatus.SCHEDULED
            assert lead_obj.lead_score == 9
            assert lead_obj.trial_class_date is not None

    # ========== Tests de ReminderService.schedule_trial_week_reminders() ==========

    def test_schedule_trial_week_reminders_crea_recordatorios(self, app, lead):
        """
        Debe crear recordatorios en BD para cada clase de la semana
        """
        with app.app_context():
            reminder_service = ReminderService()

            # Programar recordatorios para Jiu-Jitsu adultos (Lunes a Viernes)
            start_date = datetime.now()
            result = reminder_service.schedule_trial_week_reminders(
                lead_id=lead,
                trial_week_id=lead,
                clase_tipo='adultos_jiujitsu',
                start_date=start_date.strftime('%Y-%m-%d')
            )

            # Verificar resultado
            assert result['success'] is True
            assert result['count'] >= 5  # Al menos 5 clases en una semana (Lun-Vie)

            # Verificar que se crearon en BD
            reminders = ClassReminder.query.filter_by(lead_id=lead).all()
            assert len(reminders) >= 5

            # Verificar que todos están PENDING
            assert all(r.status == ReminderStatus.PENDING for r in reminders)

            # Verificar que send_at es 24 horas antes de class_datetime
            for reminder in reminders:
                expected_send_at = reminder.class_datetime - timedelta(hours=24)
                assert reminder.send_at == expected_send_at

    def test_schedule_trial_week_reminders_kids_solo_martes_jueves(self, app, lead):
        """
        Debe crear solo 2 recordatorios para Kids (Martes y Jueves)
        """
        with app.app_context():
            reminder_service = ReminderService()

            start_date = datetime.now()
            result = reminder_service.schedule_trial_week_reminders(
                lead_id=lead,
                trial_week_id=lead,
                clase_tipo='kids',
                start_date=start_date.strftime('%Y-%m-%d')
            )

            # Verificar resultado
            assert result['success'] is True

            # Kids: Martes y Jueves = máximo 2 clases en 7 días
            reminders = ClassReminder.query.filter_by(lead_id=lead).all()
            assert len(reminders) <= 2

    def test_schedule_trial_week_reminders_lead_no_existe(self, app):
        """
        Debe fallar si el lead no existe
        """
        with app.app_context():
            reminder_service = ReminderService()

            result = reminder_service.schedule_trial_week_reminders(
                lead_id=999999,
                trial_week_id=1,
                clase_tipo='adultos_jiujitsu',
                start_date=datetime.now().strftime('%Y-%m-%d')
            )

            assert result['success'] is False
            assert 'no encontrado' in result['message']

    # ========== Tests de ReminderService.send_reminder() ==========

    @patch('app.services.notification_service.NotificationService')
    def test_send_reminder_envia_whatsapp(self, mock_notification_service, app, lead):
        """
        Debe enviar recordatorio por WhatsApp al lead
        """
        with app.app_context():
            # Crear recordatorio
            academy = Academy.query.first()
            reminder = ClassReminder(
                lead_id=lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(hours=24),
                send_at=datetime.now(),
                status=ReminderStatus.PENDING,
                notes='Test reminder'
            )
            db.session.add(reminder)
            db.session.commit()

            # Mock del NotificationService
            mock_notifier_instance = Mock()
            mock_notifier_instance.send_whatsapp.return_value = {
                'success': True,
                'sid': 'SM1234567890'
            }
            mock_notification_service.return_value = mock_notifier_instance

            # Crear ReminderService con mock
            reminder_service = ReminderService()
            reminder_service.notifier = mock_notifier_instance

            # Enviar recordatorio
            result = reminder_service.send_reminder(reminder.id)

            # Verificar resultado
            assert result['success'] is True
            assert 'sid' in result

            # Verificar que se llamó send_whatsapp
            mock_notifier_instance.send_whatsapp.assert_called_once()

            # Verificar argumentos
            call_args = mock_notifier_instance.send_whatsapp.call_args[1]
            assert call_args['to'] == '+50688887777'
            assert 'Recordatorio' in call_args['message']

            # Verificar que el reminder se marcó como SENT
            reminder = ClassReminder.query.get(reminder.id)
            assert reminder.status == ReminderStatus.SENT
            assert reminder.sent_at is not None
            assert reminder.twilio_message_sid == 'SM1234567890'

    @patch('app.services.notification_service.NotificationService')
    def test_send_reminder_marca_failed_si_falla(self, mock_notification_service, app, lead):
        """
        Debe marcar el recordatorio como FAILED si el envío falla
        """
        with app.app_context():
            # Crear recordatorio
            academy = Academy.query.first()
            reminder = ClassReminder(
                lead_id=lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(hours=24),
                send_at=datetime.now(),
                status=ReminderStatus.PENDING
            )
            db.session.add(reminder)
            db.session.commit()

            # Mock del NotificationService que falla
            mock_notifier_instance = Mock()
            mock_notifier_instance.send_whatsapp.return_value = {
                'success': False,
                'message': 'Twilio error'
            }
            mock_notification_service.return_value = mock_notifier_instance

            # Crear ReminderService con mock
            reminder_service = ReminderService()
            reminder_service.notifier = mock_notifier_instance

            # Enviar recordatorio
            result = reminder_service.send_reminder(reminder.id)

            # Verificar resultado
            assert result['success'] is False

            # Verificar que el reminder se marcó como FAILED
            reminder = ClassReminder.query.get(reminder.id)
            assert reminder.status == ReminderStatus.FAILED
            assert reminder.failed_at is not None
            assert 'Twilio error' in reminder.error_message

    def test_send_reminder_no_envia_si_no_pending(self, app, lead):
        """
        No debe enviar si el recordatorio ya no está PENDING
        """
        with app.app_context():
            academy = Academy.query.first()
            reminder = ClassReminder(
                lead_id=lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(hours=24),
                send_at=datetime.now(),
                status=ReminderStatus.SENT  # Ya enviado
            )
            db.session.add(reminder)
            db.session.commit()

            reminder_service = ReminderService()
            result = reminder_service.send_reminder(reminder.id)

            assert result['success'] is False
            assert 'no está pendiente' in result['message']

    # ========== Tests de NotificationService.notify_new_trial_booking() ==========

    @patch('app.services.notification_service.Client')
    def test_notify_new_trial_booking_construye_mensaje_correcto(self, mock_twilio_client, app):
        """
        Debe construir mensaje de notificación con toda la información
        """
        with app.app_context():
            # Mock de Twilio
            mock_client_instance = Mock()
            mock_message = Mock()
            mock_message.sid = 'SM1234567890'
            mock_client_instance.messages.create.return_value = mock_message
            mock_twilio_client.return_value = mock_client_instance

            # Crear NotificationService
            notification_service = NotificationService()
            notification_service.client = mock_client_instance
            notification_service.twilio_available = True
            notification_service.whatsapp_number = '+14155238886'

            # Datos de prueba
            lead_info = {
                'name': 'Juan Pérez',
                'phone': '+50688887777',
                'status': LeadStatus.SCHEDULED
            }

            trial_info = {
                'clase_nombre': 'Jiu-Jitsu Adultos',
                'start_date': '2025-01-15',
                'dias_texto': 'Lunes a Viernes',
                'hora': '18:00',
                'notes': 'Agendado vía WhatsApp'
            }

            # Mock de _get_notification_contacts
            with patch.object(notification_service, '_get_notification_contacts', return_value={
                'primary_whatsapp': '+50688888888'
            }):
                # Enviar notificación
                result = notification_service.notify_new_trial_booking(lead_info, trial_info)

            # Verificar resultado
            assert result['success'] is True

            # Verificar que se llamó messages.create
            mock_client_instance.messages.create.assert_called_once()

            # Verificar el mensaje
            call_kwargs = mock_client_instance.messages.create.call_args[1]
            mensaje = call_kwargs['body']

            assert 'Juan Pérez' in mensaje
            assert '+50688887777' in mensaje
            assert 'Jiu-Jitsu Adultos' in mensaje
            assert 'Lunes a Viernes' in mensaje
            assert '18:00' in mensaje

    # ========== Tests de get_pending_reminders() ==========

    def test_get_pending_reminders_solo_retorna_pending(self, app, lead):
        """
        Debe retornar solo recordatorios con status PENDING y send_at pasado
        """
        with app.app_context():
            academy = Academy.query.first()

            # Crear 3 recordatorios
            # 1. PENDING y debe enviarse (send_at en el pasado)
            reminder1 = ClassReminder(
                lead_id=lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(hours=1),
                send_at=datetime.now() - timedelta(hours=1),  # Pasado
                status=ReminderStatus.PENDING
            )

            # 2. SENT (no debe aparecer)
            reminder2 = ClassReminder(
                lead_id=lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(hours=2),
                send_at=datetime.now() - timedelta(hours=2),
                status=ReminderStatus.SENT
            )

            # 3. PENDING pero send_at futuro (no debe aparecer)
            reminder3 = ClassReminder(
                lead_id=lead,
                academy_id=academy.id,
                class_type='adultos_jiujitsu',
                class_datetime=datetime.now() + timedelta(hours=48),
                send_at=datetime.now() + timedelta(hours=24),  # Futuro
                status=ReminderStatus.PENDING
            )

            db.session.add_all([reminder1, reminder2, reminder3])
            db.session.commit()

            reminder_service = ReminderService()
            pending = reminder_service.get_pending_reminders()

            # Solo debe retornar reminder1
            assert len(pending) == 1
            assert pending[0].id == reminder1.id


# ========== Ejecutar tests ==========

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TESTS DE NOTIFICACIONES Y RECORDATORIOS")
    print("="*60 + "\n")

    # Ejecutar con pytest
    exit_code = pytest.main([
        __file__,
        '-v',  # Verbose
        '--color=yes',  # Colores
        '--tb=short',  # Traceback corto
    ])

    exit(exit_code)
