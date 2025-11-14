"""
Script de Testing para el Sistema de Recordatorios
Verifica que todos los componentes estén funcionando correctamente
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test 1: Verificar conexión a la base de datos"""
    print("\n" + "="*60)
    print("TEST 1: Conexión a Base de Datos")
    print("="*60)

    try:
        from app.utils.database import get_db_connection

        with get_db_connection(db_path='bjj_academy.db') as conn:
            cursor = conn.cursor()

            # Verificar que la tabla class_reminders existe
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='class_reminders'
            """)
            table_exists = cursor.fetchone()

            if table_exists:
                print("[OK] Tabla 'class_reminders' existe")

                # Contar recordatorios
                cursor.execute("SELECT COUNT(*) FROM class_reminders")
                count = cursor.fetchone()[0]
                print(f"[OK] Total de recordatorios en BD: {count}")

                return True
            else:
                print("[ERROR] Tabla 'class_reminders' no existe")
                print("   Ejecutar: python -c \"import sqlite3; conn = sqlite3.connect('bjj_academy.db'); cursor = conn.cursor(); cursor.executescript(open('backend/migrations/add_reminders_table.sql', encoding='utf-8').read()); conn.commit(); conn.close()\"")
                return False

    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        return False


def test_reminder_service():
    """Test 2: Verificar que ReminderService funciona"""
    print("\n" + "="*60)
    print("TEST 2: ReminderService")
    print("="*60)

    try:
        from app.services.reminder_service import ReminderService

        reminder_service = ReminderService()
        print("[OK] ReminderService inicializado correctamente")

        # Verificar que tiene acceso a horarios
        if reminder_service.horarios:
            print(f"[OK] Horarios cargados: {len(reminder_service.horarios)} tipos de clase")

        # Contar recordatorios pendientes
        count = reminder_service.get_pending_reminders_count()
        print(f"[OK] Recordatorios pendientes: {count}")

        return True

    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_notification_service():
    """Test 3: Verificar configuración de NotificationService (Twilio)"""
    print("\n" + "="*60)
    print("TEST 3: NotificationService (Twilio)")
    print("="*60)

    try:
        from app.services.notification_service import NotificationService

        notifier = NotificationService()

        if notifier.twilio_available:
            print("[OK] Twilio configurado y disponible")
            print(f"   WhatsApp Number: {notifier.whatsapp_number}")
            return True
        else:
            print("[WARN]  Twilio NO disponible")
            print("   Revisar variables de entorno:")
            print("   - TWILIO_ACCOUNT_SID")
            print("   - TWILIO_AUTH_TOKEN")
            print("   - TWILIO_WHATSAPP_NUMBER")
            return False

    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        return False


def test_redis_connection():
    """Test 4: Verificar conexión a Redis"""
    print("\n" + "="*60)
    print("TEST 4: Conexión a Redis")
    print("="*60)

    try:
        import redis
        from dotenv import load_dotenv

        load_dotenv(override=True)

        redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
        print(f"   Redis URL: {redis_url}")

        r = redis.from_url(redis_url)
        r.ping()

        print("[OK] Redis conectado correctamente")
        return True

    except ImportError:
        print("[ERROR] ERROR: Redis library no instalada")
        print("   Instalar con: pip install redis")
        return False
    except Exception as e:
        print(f"[ERROR] ERROR: No se pudo conectar a Redis")
        print(f"   {e}")
        print("\n   Soluciones:")
        print("   1. Iniciar Redis con Docker: docker run -d -p 6379:6379 redis")
        print("   2. O instalar Redis localmente")
        return False


def test_celery_tasks():
    """Test 5: Verificar que las tareas de Celery se pueden importar"""
    print("\n" + "="*60)
    print("TEST 5: Tareas de Celery")
    print("="*60)

    try:
        from app.tasks.reminder_tasks import (
            check_and_send_reminders,
            cleanup_old_reminders,
            schedule_trial_reminders
        )

        print("[OK] Tareas de Celery importadas correctamente:")
        print("   - check_and_send_reminders")
        print("   - cleanup_old_reminders")
        print("   - schedule_trial_reminders")

        return True

    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_sample_reminder():
    """Test 6: Crear un recordatorio de prueba"""
    print("\n" + "="*60)
    print("TEST 6: Crear Recordatorio de Prueba")
    print("="*60)

    try:
        from app.services.reminder_service import ReminderService
        from app.utils.database import get_db_connection

        # Verificar si existe al menos un lead
        with get_db_connection(db_path='bjj_academy.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, phone_number FROM lead LIMIT 1")
            lead = cursor.fetchone()

        if not lead:
            print("[WARN]  No hay leads en la base de datos")
            print("   Crear un lead primero enviando un mensaje por WhatsApp")
            return False

        lead_id, lead_name, lead_phone = lead
        print(f"   Usando lead: {lead_name} (ID: {lead_id})")

        # Crear recordatorio de prueba para mañana
        reminder_service = ReminderService()

        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_6pm = tomorrow.replace(hour=18, minute=0, second=0)

        reminder_id = reminder_service._create_reminder(
            lead_id=lead_id,
            trial_week_id=None,
            clase_tipo='adultos_jiujitsu',
            class_datetime=tomorrow_6pm
        )

        if reminder_id:
            print(f"[OK] Recordatorio de prueba creado (ID: {reminder_id})")
            print(f"   Fecha/Hora clase: {tomorrow_6pm}")
            print(f"   Lead: {lead_name}")
            return True
        else:
            print("[ERROR] No se pudo crear el recordatorio")
            return False

    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schedule_trial_reminders():
    """Test 7: Programar recordatorios para una semana de prueba"""
    print("\n" + "="*60)
    print("TEST 7: Programar Recordatorios de Semana de Prueba")
    print("="*60)

    try:
        from app.services.reminder_service import ReminderService
        from app.utils.database import get_db_connection

        # Verificar si existe al menos un trial week
        with get_db_connection(db_path='bjj_academy.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tw.id, tw.lead_id, tw.clase_tipo, tw.start_date, l.name
                FROM trial_weeks tw
                JOIN lead l ON tw.lead_id = l.id
                WHERE tw.status = 'active'
                LIMIT 1
            """)
            trial = cursor.fetchone()

        if not trial:
            print("[WARN]  No hay trial weeks activas en la base de datos")
            print("   Crear una semana de prueba enviando un mensaje por WhatsApp")
            return False

        trial_id, lead_id, clase_tipo, start_date, lead_name = trial
        print(f"   Usando trial week: ID {trial_id}")
        print(f"   Lead: {lead_name}")
        print(f"   Clase: {clase_tipo}")
        print(f"   Start: {start_date}")

        # Programar recordatorios
        reminder_service = ReminderService()
        result = reminder_service.schedule_trial_week_reminders(
            lead_id=lead_id,
            trial_week_id=trial_id,
            clase_tipo=clase_tipo,
            start_date=start_date
        )

        if result['success']:
            print(f"[OK] {result['message']}")
            for reminder in result.get('reminders', []):
                print(f"   - {reminder['day']} {reminder['date']} a las {reminder['time']}")
            return True
        else:
            print(f"[ERROR] ERROR: {result['message']}")
            return False

    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n")
    print("=" * 60)
    print(" " * 15 + "SISTEMA DE RECORDATORIOS")
    print(" " * 20 + "BJJ MINGO - TESTS")
    print("=" * 60)

    results = {
        'Database': test_database_connection(),
        'ReminderService': test_reminder_service(),
        'NotificationService': test_notification_service(),
        'Redis': test_redis_connection(),
        'Celery Tasks': test_celery_tasks(),
        'Create Sample': test_create_sample_reminder(),
        'Schedule Trial': test_schedule_trial_reminders()
    }

    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE TESTS")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[ERROR] FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "="*60)
    print(f"Total: {passed}/{total} tests pasaron")
    print("="*60)

    if passed == total:
        print("\n¡Todos los tests pasaron! El sistema esta listo.")
        print("\nPróximos pasos:")
        print("1. Iniciar Redis (si no está corriendo)")
        print("2. Ejecutar: start_celery_worker.bat (Windows) o start_celery_worker.sh (Linux/Mac)")
        print("3. Ejecutar: start_celery_beat.bat (Windows) o start_celery_beat.sh (Linux/Mac)")
        print("4. Iniciar Flask app: python run.py")
    else:
        print("\nAlgunos tests fallaron. Revisar errores arriba.")

    print("\n")


if __name__ == '__main__':
    main()
