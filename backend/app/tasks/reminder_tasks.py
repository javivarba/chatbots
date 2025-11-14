"""
Tareas de Celery para gestión de recordatorios
Incluye tareas periódicas y bajo demanda
"""

import logging
from datetime import datetime, timedelta
from app.celery_app import celery_app
from app.services.reminder_service import ReminderService
from app.utils.database import get_db_connection, get_db_cursor

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.reminder_tasks.check_and_send_reminders')
def check_and_send_reminders():
    """
    Tarea periódica (cada hora) que verifica clases próximas
    y envía recordatorios 24 horas antes
    """
    logger.info("🔍 Ejecutando tarea: check_and_send_reminders")

    try:
        reminder_service = ReminderService()
        result = reminder_service.check_and_send_reminders()

        logger.info(f"✅ Tarea completada: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Error en tarea check_and_send_reminders: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.reminder_tasks.cleanup_old_reminders')
def cleanup_old_reminders(days_to_keep=30):
    """
    Tarea de limpieza que elimina recordatorios antiguos
    Por defecto mantiene los últimos 30 días
    """
    logger.info(f"🧹 Ejecutando tarea: cleanup_old_reminders (mantener últimos {days_to_keep} días)")

    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        with get_db_cursor(db_path='bjj_academy.db') as cursor:
            # Eliminar recordatorios antiguos que ya fueron enviados o fallaron
            cursor.execute("""
                DELETE FROM class_reminders
                WHERE class_datetime < ?
                AND reminder_status IN ('sent', 'failed')
            """, (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))

            deleted_count = cursor.rowcount

        logger.info(f"✅ Limpieza completada: {deleted_count} recordatorios antiguos eliminados")

        return {
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d')
        }

    except Exception as e:
        logger.error(f"❌ Error en tarea cleanup_old_reminders: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.reminder_tasks.update_expired_trials')
def update_expired_trials():
    """
    Tarea que actualiza el estado de trial weeks que ya expiraron
    Marca como 'expired' las que pasaron su end_date
    """
    logger.info("📅 Ejecutando tarea: update_expired_trials")

    try:
        today = datetime.now().strftime('%Y-%m-%d')

        with get_db_cursor(db_path='bjj_academy.db') as cursor:
            # Actualizar trial weeks expiradas
            cursor.execute("""
                UPDATE trial_weeks
                SET status = 'expired'
                WHERE status = 'active'
                AND end_date < ?
            """, (today,))

            updated_count = cursor.rowcount

        logger.info(f"✅ Actualización completada: {updated_count} trial weeks marcadas como expiradas")

        return {
            'success': True,
            'updated_count': updated_count,
            'date': today
        }

    except Exception as e:
        logger.error(f"❌ Error en tarea update_expired_trials: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.reminder_tasks.send_immediate_reminder')
def send_immediate_reminder(lead_id, clase_tipo, class_datetime_str):
    """
    Tarea bajo demanda para enviar un recordatorio inmediato
    Útil para recordatorios manuales o re-envíos

    Args:
        lead_id: ID del prospecto
        clase_tipo: Tipo de clase
        class_datetime_str: Fecha/hora de la clase en formato 'YYYY-MM-DD HH:MM:SS'
    """
    logger.info(f"📨 Ejecutando tarea: send_immediate_reminder para lead {lead_id}")

    try:
        reminder_service = ReminderService()

        # Obtener información del lead
        with get_db_connection(db_path='bjj_academy.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, phone_number FROM lead WHERE id = ?
            """, (lead_id,))
            lead_data = cursor.fetchone()

        if not lead_data:
            logger.error(f"Lead {lead_id} no encontrado")
            return {'success': False, 'error': f'Lead {lead_id} no encontrado'}

        lead_name, phone = lead_data

        # Enviar recordatorio
        result = reminder_service._send_reminder(
            reminder_id=0,  # ID temporal
            lead_name=lead_name,
            phone=phone,
            clase_tipo=clase_tipo,
            class_datetime_str=class_datetime_str
        )

        logger.info(f"✅ Recordatorio enviado: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Error en tarea send_immediate_reminder: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.reminder_tasks.schedule_trial_reminders')
def schedule_trial_reminders(lead_id, trial_week_id, clase_tipo, start_date):
    """
    Tarea bajo demanda para programar todos los recordatorios de una semana de prueba
    Se ejecuta cuando se confirma un agendamiento

    Args:
        lead_id: ID del prospecto
        trial_week_id: ID de la semana de prueba
        clase_tipo: Tipo de clase
        start_date: Fecha de inicio en formato 'YYYY-MM-DD'
    """
    logger.info(f"📅 Programando recordatorios para trial_week {trial_week_id}")

    try:
        reminder_service = ReminderService()
        result = reminder_service.schedule_trial_week_reminders(
            lead_id=lead_id,
            trial_week_id=trial_week_id,
            clase_tipo=clase_tipo,
            start_date=start_date
        )

        logger.info(f"✅ Recordatorios programados: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Error en tarea schedule_trial_reminders: {e}")
        return {'success': False, 'error': str(e)}
