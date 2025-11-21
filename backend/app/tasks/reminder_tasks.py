"""
Tareas de Celery para gestión de recordatorios
Incluye tareas periódicas y bajo demanda
MIGRADO A SQLALCHEMY + POSTGRESQL (SIMPLIFICADO)
NOTA: Funcionalidad completa requiere modelo ClassReminder
"""

import logging
from datetime import datetime, timedelta
from app.celery_app import celery_app
from app.services.reminder_service import ReminderService
from app import db
from app.models import Lead

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.reminder_tasks.check_and_send_reminders')
def check_and_send_reminders():
    """
    Tarea periódica (cada hora) que verifica clases próximas
    y envía recordatorios 24 horas antes

    NOTA: Versión simplificada - requiere modelo ClassReminder para funcionar completamente
    """
    logger.info("🔍 Ejecutando tarea: check_and_send_reminders")
    logger.warning("⚠️ Funcionalidad simplificada - requiere modelo ClassReminder")

    try:
        # Por ahora solo registra en logs
        pending_reminders = []  # En versión completa: obtener de ClassReminder

        logger.info(f"📋 Recordatorios pendientes: {len(pending_reminders)}")

        return {
            'success': True,
            'pending': len(pending_reminders),
            'sent': 0,
            'message': 'Funcionalidad simplificada - requiere modelo ClassReminder'
        }

    except Exception as e:
        logger.error(f"❌ Error en tarea check_and_send_reminders: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.reminder_tasks.cleanup_old_reminders')
def cleanup_old_reminders(days_to_keep=30):
    """
    Tarea de limpieza que elimina recordatorios antiguos
    Por defecto mantiene los últimos 30 días

    NOTA: Versión simplificada - requiere modelo ClassReminder
    """
    logger.info(f"🧹 Ejecutando tarea: cleanup_old_reminders (mantener últimos {days_to_keep} días)")
    logger.warning("⚠️ Funcionalidad simplificada - requiere modelo ClassReminder")

    try:
        # En versión completa: eliminar recordatorios viejos de ClassReminder
        deleted_count = 0

        logger.info(f"✅ Limpieza completada: {deleted_count} recordatorios eliminados (simulado)")

        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': 'Funcionalidad simplificada - requiere modelo ClassReminder'
        }

    except Exception as e:
        logger.error(f"❌ Error en tarea cleanup_old_reminders: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='app.tasks.reminder_tasks.update_expired_trials')
def update_expired_trials():
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


@celery_app.task(name='app.tasks.reminder_tasks.send_immediate_reminder')
def send_immediate_reminder(lead_id, clase_tipo, class_datetime_str):
    """
    Tarea bajo demanda para enviar un recordatorio inmediato
    Útil para recordatorios manuales o re-envíos

    MIGRADO A SQLALCHEMY

    Args:
        lead_id: ID del prospecto
        clase_tipo: Tipo de clase
        class_datetime_str: Fecha/hora de la clase en formato 'YYYY-MM-DD HH:%M:%S'
    """
    logger.info(f"📨 Ejecutando tarea: send_immediate_reminder para lead {lead_id}")

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            # Obtener lead
            lead = Lead.query.get(lead_id)

            if not lead:
                logger.error(f"Lead {lead_id} no encontrado")
                return {'success': False, 'error': f'Lead {lead_id} no encontrado'}

            # Enviar recordatorio
            reminder_service = ReminderService()
            class_datetime = datetime.strptime(class_datetime_str, '%Y-%m-%d %H:%M:%S')

            result = reminder_service.send_reminder(
                lead_id=lead_id,
                class_datetime=class_datetime,
                clase_tipo=clase_tipo
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

    MIGRADO A SQLALCHEMY

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
