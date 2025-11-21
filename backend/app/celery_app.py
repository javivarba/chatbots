"""
Configuración de Celery para BJJ Mingo
Gestiona tareas asíncronas y programadas como:
- Envío de recordatorios 24 horas antes de clases
- Actualizaciones de estado de leads
- Limpieza de datos antiguos

NOTA: Redis Cloud Free tier cierra conexiones inactivas.
Se configuran retries y health checks para manejar esto.
"""

import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv(override=True)

# Crear instancia de Celery
celery_app = Celery(
    'bjj_mingo',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configuración optimizada para Redis Cloud Free tier
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Costa_Rica',
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=300,

    # === CONFIGURACIÓN PARA REDIS CLOUD FREE (conexiones inestables) ===

    # Retry automático de tareas que fallan por conexión
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Reconexión automática del broker
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Health check y timeouts del broker
    broker_heartbeat=10,
    broker_pool_limit=1,  # Usar una sola conexión (Free tier limit)

    # Configuración del transport Redis
    broker_transport_options={
        'visibility_timeout': 3600,
        'socket_timeout': 30,
        'socket_connect_timeout': 30,
        'retry_on_timeout': True,
        'health_check_interval': 10,
    },

    # Backend Redis también necesita configuración
    redis_backend_health_check_interval=10,
    result_backend_transport_options={
        'socket_timeout': 30,
        'socket_connect_timeout': 30,
        'retry_on_timeout': True,
    },

    # Retry de tareas fallidas
    task_default_retry_delay=60,  # 1 minuto entre retries
    task_max_retries=3,
)

# Configurar tareas periódicas (Celery Beat)
celery_app.conf.beat_schedule = {
    # Verificar y enviar recordatorios cada hora
    'check-and-send-reminders': {
        'task': 'app.tasks.reminder_tasks.check_and_send_reminders',
        'schedule': crontab(minute=0),  # Cada hora en punto (xx:00)
    },

    # Limpiar recordatorios antiguos cada día a las 2 AM
    'cleanup-old-reminders': {
        'task': 'app.tasks.reminder_tasks.cleanup_old_reminders',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2:00 AM
    },

    # Actualizar estado de trial weeks expiradas cada día a las 3 AM
    'update-expired-trials': {
        'task': 'app.tasks.reminder_tasks.update_expired_trials',
        'schedule': crontab(hour=3, minute=0),  # Diario a las 3:00 AM
    },
}

# Auto-descubrir tareas en el módulo app.tasks
celery_app.autodiscover_tasks(['app.tasks'])

if __name__ == '__main__':
    celery_app.start()
