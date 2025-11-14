"""
Configuración de Celery para BJJ Mingo
Gestiona tareas asíncronas y programadas como:
- Envío de recordatorios 24 horas antes de clases
- Actualizaciones de estado de leads
- Limpieza de datos antiguos
"""

import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv(override=True)

# Crear instancia de Celery
celery_app = Celery(
    'bjj_mingo',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
)

# Configuración
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Costa_Rica',  # Zona horaria de Costa Rica
    enable_utc=True,
    result_expires=3600,  # Los resultados expiran después de 1 hora
    task_track_started=True,
    task_time_limit=300,  # 5 minutos máximo por tarea
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
