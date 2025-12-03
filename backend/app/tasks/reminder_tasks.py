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
    start_time = datetime.now()
    logger.info("="*70)
    logger.info("📬 INICIANDO VERIFICACIÓN DE RECORDATORIOS")
    logger.info(f"   Hora de ejecución: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   Task ID: {self.request.id}")
    logger.info("="*70)

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            reminder_service = ReminderService()

            # Obtener recordatorios pendientes que deben enviarse
            logger.info("📋 Buscando recordatorios pendientes en BD...")
            pending_reminders = reminder_service.get_pending_reminders(limit=100)

            if len(pending_reminders) == 0:
                logger.info("ℹ️  No hay recordatorios pendientes por enviar en este momento")
                return {
                    'success': True,
                    'pending': 0,
                    'sent': 0,
                    'failed': 0,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

            logger.info(f"📊 Encontrados {len(pending_reminders)} recordatorios pendientes:")
            for reminder in pending_reminders:
                logger.info(f"   • Reminder {reminder.id} - Lead {reminder.lead_id} - Clase: {reminder.class_datetime.strftime('%Y-%m-%d %H:%M')}")

            sent_count = 0
            failed_count = 0

            logger.info("─"*70)
            logger.info("📤 PROCESANDO RECORDATORIOS...")
            logger.info("─"*70)

            for idx, reminder in enumerate(pending_reminders, 1):
                try:
                    logger.info(f"[{idx}/{len(pending_reminders)}] Procesando recordatorio {reminder.id}")
                    logger.info(f"   Lead ID: {reminder.lead_id}")
                    logger.info(f"   Clase: {reminder.class_type}")
                    logger.info(f"   Fecha clase: {reminder.class_datetime.strftime('%Y-%m-%d %H:%M')}")
                    logger.info(f"   Programado para: {reminder.send_at.strftime('%Y-%m-%d %H:%M')}")

                    result = reminder_service.send_reminder(reminder.id)

                    if result['success']:
                        sent_count += 1
                        message_sid = result.get('sid', 'N/A')
                        logger.info(f"   ✅ ENVIADO - SID: {message_sid}")
                    else:
                        failed_count += 1
                        error_msg = result.get('message', 'Error desconocido')
                        logger.error(f"   ❌ FALLÓ - {error_msg}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"   ❌ EXCEPCIÓN - {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue

            # Resumen final
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info("="*70)
            logger.info("📊 RESUMEN DE EJECUCIÓN")
            logger.info("="*70)
            logger.info(f"   Recordatorios encontrados: {len(pending_reminders)}")
            logger.info(f"   ✅ Enviados exitosamente: {sent_count}")
            logger.info(f"   ❌ Fallidos: {failed_count}")
            logger.info(f"   ⏱️  Duración: {duration:.2f} segundos")
            logger.info(f"   🕐 Finalizado: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*70)

            return {
                'success': True,
                'pending': len(pending_reminders),
                'sent': sent_count,
                'failed': failed_count,
                'duration_seconds': duration,
                'timestamp': end_time.strftime('%Y-%m-%d %H:%M:%S')
            }

    except Exception as e:
        logger.error("="*70)
        logger.error("❌ ERROR CRÍTICO EN TAREA check_and_send_reminders")
        logger.error("="*70)
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("="*70)
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
    logger.info("="*70)
    logger.info("🧹 INICIANDO LIMPIEZA DE RECORDATORIOS ANTIGUOS")
    logger.info(f"   Mantener últimos: {days_to_keep} días")
    logger.info(f"   Task ID: {self.request.id}")
    logger.info("="*70)

    try:
        from app import create_app
        from app.models import ClassReminder
        app = create_app()

        with app.app_context():
            # Calcular fecha de corte
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            logger.info(f"📅 Fecha de corte: {cutoff_date.strftime('%Y-%m-%d')}")
            logger.info(f"   Se eliminarán recordatorios anteriores a esta fecha con status: sent/failed/cancelled")

            # Contar antes de eliminar
            count_before = ClassReminder.query.filter(
                ClassReminder.class_datetime < cutoff_date,
                ClassReminder.status.in_(['sent', 'failed', 'cancelled'])
            ).count()

            logger.info(f"📊 Recordatorios a eliminar: {count_before}")

            if count_before == 0:
                logger.info("ℹ️  No hay recordatorios antiguos para eliminar")
                return {
                    'success': True,
                    'deleted_count': 0,
                    'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

            # Eliminar recordatorios antiguos que no son PENDING
            deleted = ClassReminder.query.filter(
                ClassReminder.class_datetime < cutoff_date,
                ClassReminder.status.in_(['sent', 'failed', 'cancelled'])
            ).delete(synchronize_session=False)

            db.session.commit()

            logger.info("="*70)
            logger.info("✅ LIMPIEZA COMPLETADA")
            logger.info("="*70)
            logger.info(f"   Recordatorios eliminados: {deleted}")
            logger.info(f"   Fecha de corte: {cutoff_date.strftime('%Y-%m-%d')}")
            logger.info("="*70)

            return {
                'success': True,
                'deleted_count': deleted,
                'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    except Exception as e:
        db.session.rollback()
        logger.error("="*70)
        logger.error("❌ ERROR EN TAREA cleanup_old_reminders")
        logger.error("="*70)
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("="*70)
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
    now = datetime.now()
    logger.info("="*70)
    logger.info("📅 ACTUALIZANDO TRIAL WEEKS EXPIRADAS")
    logger.info(f"   Fecha actual: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   Task ID: {self.request.id}")
    logger.info("="*70)

    try:
        # Necesitamos usar Flask app context para queries
        from app import create_app
        app = create_app()

        with app.app_context():
            # Obtener leads con trial_class_date en el pasado que siguen como 'scheduled'
            logger.info("🔍 Buscando trial weeks expiradas en BD...")
            expired_leads = Lead.query.filter(
                Lead.status == 'scheduled',
                Lead.trial_class_date < now
            ).all()

            if len(expired_leads) == 0:
                logger.info("ℹ️  No hay trial weeks expiradas por actualizar")
                return {
                    'success': True,
                    'updated_count': 0,
                    'date': now.strftime('%Y-%m-%d')
                }

            logger.info(f"📊 Encontrados {len(expired_leads)} leads con trial expirada:")
            for lead in expired_leads:
                trial_date = lead.trial_class_date.strftime('%Y-%m-%d') if lead.trial_class_date else 'N/A'
                logger.info(f"   • Lead {lead.id} - {lead.name} - Trial: {trial_date}")

            updated_count = 0
            for lead in expired_leads:
                old_status = lead.status
                lead.status = 'contacted'
                updated_count += 1
                logger.info(f"   ✅ Lead {lead.id}: {old_status} → contacted")

            if updated_count > 0:
                db.session.commit()

            logger.info("="*70)
            logger.info("✅ ACTUALIZACIÓN COMPLETADA")
            logger.info("="*70)
            logger.info(f"   Trial weeks actualizadas: {updated_count}")
            logger.info(f"   Fecha: {now.strftime('%Y-%m-%d')}")
            logger.info("="*70)

            return {
                'success': True,
                'updated_count': updated_count,
                'date': now.strftime('%Y-%m-%d')
            }

    except Exception as e:
        db.session.rollback()
        logger.error("="*70)
        logger.error("❌ ERROR EN TAREA update_expired_trials")
        logger.error("="*70)
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("="*70)
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
    logger.info("="*70)
    logger.info("📤 ENVÍO INMEDIATO DE RECORDATORIO")
    logger.info(f"   Reminder ID: {reminder_id}")
    logger.info(f"   Task ID: {self.request.id}")
    logger.info("="*70)

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            reminder_service = ReminderService()

            logger.info(f"🔍 Buscando recordatorio {reminder_id}...")
            result = reminder_service.send_reminder(reminder_id)

            if result['success']:
                message_sid = result.get('sid', 'N/A')
                logger.info("="*70)
                logger.info("✅ RECORDATORIO ENVIADO EXITOSAMENTE")
                logger.info("="*70)
                logger.info(f"   Reminder ID: {reminder_id}")
                logger.info(f"   Message SID: {message_sid}")
                logger.info("="*70)
            else:
                error_msg = result.get('message', 'Error desconocido')
                logger.error("="*70)
                logger.error("❌ FALLO AL ENVIAR RECORDATORIO")
                logger.error("="*70)
                logger.error(f"   Reminder ID: {reminder_id}")
                logger.error(f"   Error: {error_msg}")
                logger.error("="*70)

            return result

    except Exception as e:
        logger.error("="*70)
        logger.error("❌ ERROR EN TAREA send_immediate_reminder")
        logger.error("="*70)
        logger.error(f"Reminder ID: {reminder_id}")
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("="*70)
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
    logger.info("="*70)
    logger.info("📅 PROGRAMANDO RECORDATORIOS DE TRIAL WEEK")
    logger.info(f"   Lead ID: {lead_id}")
    logger.info(f"   Clase tipo: {clase_tipo}")
    logger.info(f"   Fecha inicio: {start_date}")
    logger.info(f"   Task ID: {self.request.id}")
    logger.info("="*70)

    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            reminder_service = ReminderService()

            logger.info("🔧 Creando recordatorios en BD...")
            result = reminder_service.schedule_trial_week_reminders(
                lead_id=lead_id,
                trial_week_id=trial_week_id,
                clase_tipo=clase_tipo,
                start_date=start_date
            )

            if result['success']:
                count = result.get('count', 0)
                logger.info("="*70)
                logger.info("✅ RECORDATORIOS PROGRAMADOS EXITOSAMENTE")
                logger.info("="*70)
                logger.info(f"   Total recordatorios creados: {count}")
                logger.info(f"   Lead ID: {lead_id}")

                if 'reminders' in result:
                    logger.info("\n   Recordatorios creados:")
                    for reminder in result['reminders']:
                        logger.info(f"      • {reminder['day']} {reminder['class_datetime']}")
                        logger.info(f"        Envío programado: {reminder['send_at']}")

                logger.info("="*70)
            else:
                error_msg = result.get('message', 'Error desconocido')
                logger.error("="*70)
                logger.error("❌ FALLO AL PROGRAMAR RECORDATORIOS")
                logger.error("="*70)
                logger.error(f"   Lead ID: {lead_id}")
                logger.error(f"   Error: {error_msg}")
                logger.error("="*70)

            return result

    except Exception as e:
        logger.error("="*70)
        logger.error("❌ ERROR EN TAREA schedule_trial_reminders")
        logger.error("="*70)
        logger.error(f"Lead ID: {lead_id}")
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("="*70)
        return {'success': False, 'error': str(e)}
