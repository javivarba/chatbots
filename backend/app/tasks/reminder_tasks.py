"""
Tareas de Celery para gestión de recordatorios
Incluye tareas periódicas y bajo demanda
INTEGRADO CON SQLALCHEMY + POSTGRESQL + CLASSREMINDER MODEL

NOTA: Configuradas con autoretry para manejar desconexiones de Redis Cloud Free
"""

import logging
from datetime import datetime, timedelta
from app.celery_app import celery_app
from app.services.reminder_service import ReminderService
from app import db
from app.models import Lead
from redis.exceptions import ConnectionError as RedisConnectionError
from kombu.exceptions import OperationalError

logger = logging.getLogger(__name__)

# Excepciones que disparan retry automático
RETRY_EXCEPTIONS = (RedisConnectionError, OperationalError, ConnectionResetError)


@celery_app.task(
    name='app.tasks.reminder_tasks.check_and_send_reminders',
    bind=True,
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3
)
def check_and_send_reminders(self):
    """
    Tarea periódica (cada hora) que verifica recordatorios pendientes
    y los envía cuando llega la hora programada (send_at)

    Busca ClassReminder con status=PENDING y send_at <= now
    """
    logger.info("Ejecutando tarea: check_and_send_reminders")

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            reminder_service = ReminderService()

            # Obtener recordatorios pendientes que deben enviarse
            pending_reminders = reminder_service.get_pending_reminders(limit=100)

            logger.info(f"Recordatorios pendientes a procesar: {len(pending_reminders)}")

            sent_count = 0
            failed_count = 0

            for reminder in pending_reminders:
                try:
                    logger.info(f"Enviando recordatorio {reminder.id} a lead {reminder.lead_id}")

                    result = reminder_service.send_reminder(reminder.id)

                    if result['success']:
                        sent_count += 1
                        logger.info(f"OK: Recordatorio {reminder.id} enviado exitosamente")
                    else:
                        failed_count += 1
                        logger.error(f"ERROR: Recordatorio {reminder.id} falló: {result.get('message')}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"ERROR: Excepción enviando recordatorio {reminder.id}: {e}")
                    continue

            logger.info(f"Tarea completada: {sent_count} enviados, {failed_count} fallidos")

            return {
                'success': True,
                'pending': len(pending_reminders),
                'sent': sent_count,
                'failed': failed_count,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    except Exception as e:
        logger.error(f"ERROR en tarea check_and_send_reminders: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@celery_app.task(
    name='app.tasks.reminder_tasks.cleanup_old_reminders',
    bind=True,
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    max_retries=3
)
def cleanup_old_reminders(self, days_to_keep=30):
    """
    Tarea de limpieza que elimina recordatorios antiguos
    Por defecto mantiene los últimos 30 días

    Elimina recordatorios con status SENT/FAILED/CANCELLED y class_datetime antiguo
    """
    logger.info(f"Ejecutando tarea: cleanup_old_reminders (mantener últimos {days_to_keep} días)")

    try:
        from app import create_app
        from app.models import ClassReminder
        app = create_app()

        with app.app_context():
            # Calcular fecha de corte
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Eliminar recordatorios antiguos que no son PENDING
            deleted = ClassReminder.query.filter(
                ClassReminder.class_datetime < cutoff_date,
                ClassReminder.status.in_(['sent', 'failed', 'cancelled'])
            ).delete(synchronize_session=False)

            db.session.commit()

            logger.info(f"Limpieza completada: {deleted} recordatorios eliminados")

            return {
                'success': True,
                'deleted_count': deleted,
                'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    except Exception as e:
        db.session.rollback()
        logger.error(f"ERROR en tarea cleanup_old_reminders: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@celery_app.task(
    name='app.tasks.reminder_tasks.update_expired_trials',
    bind=True,
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    max_retries=3
)
def update_expired_trials(self):
    """
    Tarea que actualiza el estado de trial weeks que ya expiraron
    Marca leads con trial_class_date en el pasado

    MIGRADO A SQLALCHEMY
    """
    logger.info("📅 Ejecutando tarea: update_expired_trials")

    try:
        # Obtener leads con trial_class_date en el pasado que siguen como 'scheduled'
        now = datetime.now()

        # Necesitamos usar Flask app context para queries
        from app import create_app
        app = create_app()

        with app.app_context():
            expired_leads = Lead.query.filter(
                Lead.status == 'scheduled',
                Lead.trial_class_date < now
            ).all()

            updated_count = 0
            for lead in expired_leads:
                # Cambiar status a 'contacted' (o crear nuevo status 'trial_expired')
                lead.status = 'contacted'
                updated_count += 1

            if updated_count > 0:
                db.session.commit()

            logger.info(f"✅ Actualización completada: {updated_count} trial weeks marcadas como expiradas")

            return {
                'success': True,
                'updated_count': updated_count,
                'date': now.strftime('%Y-%m-%d')
            }

    except Exception as e:
        logger.error(f"❌ Error en tarea update_expired_trials: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(
    name='app.tasks.reminder_tasks.send_immediate_reminder',
    bind=True,
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    max_retries=3
)
def send_immediate_reminder(self, reminder_id):
    """
    Tarea bajo demanda para enviar un recordatorio específico inmediatamente
    Útil para recordatorios manuales o re-envíos

    Args:
        reminder_id: ID del ClassReminder a enviar
    """
    logger.info(f"Ejecutando tarea: send_immediate_reminder para reminder {reminder_id}")

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            reminder_service = ReminderService()
            result = reminder_service.send_reminder(reminder_id)

            if result['success']:
                logger.info(f"OK: Recordatorio {reminder_id} enviado exitosamente")
            else:
                logger.error(f"ERROR: Recordatorio {reminder_id} falló: {result.get('message')}")

            return result

    except Exception as e:
        logger.error(f"ERROR en tarea send_immediate_reminder: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@celery_app.task(
    name='app.tasks.reminder_tasks.schedule_trial_reminders',
    bind=True,
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    max_retries=3
)
def schedule_trial_reminders(self, lead_id, trial_week_id, clase_tipo, start_date):
    """
    Tarea bajo demanda para programar todos los recordatorios de una semana de prueba
    Se ejecuta cuando se confirma un agendamiento

    Args:
        lead_id: ID del prospecto
        trial_week_id: ID de la semana de prueba
        clase_tipo: Tipo de clase
        start_date: Fecha de inicio en formato 'YYYY-MM-DD'
    """
    logger.info(f"Programando recordatorios para lead {lead_id}")

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            reminder_service = ReminderService()
            result = reminder_service.schedule_trial_week_reminders(
                lead_id=lead_id,
                trial_week_id=trial_week_id,
                clase_tipo=clase_tipo,
                start_date=start_date
            )

            logger.info(f"OK: Recordatorios programados: {result}")
            return result

    except Exception as e:
        logger.error(f"ERROR en tarea schedule_trial_reminders: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
