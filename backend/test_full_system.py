"""
TEST COMPLETO DEL SISTEMA BJJ MINGO BOT
========================================
Prueba todas las capacidades del chatbot:
1. Conexion a base de datos (PostgreSQL)
2. Conexion a Redis Cloud
3. Procesamiento de mensajes con GPT-4o-mini
4. Agendamiento de clases de prueba
5. Sistema de recordatorios
6. Notificaciones al staff
7. Dashboard API endpoints

Ejecutar: python test_full_system.py
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)

# Colores para output
class Colors:
    OK = '\033[92m'
    FAIL = '\033[91m'
    WARN = '\033[93m'
    INFO = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{'='*60}")
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    print('='*60)

def print_ok(msg):
    print(f"{Colors.OK}[OK]{Colors.RESET} {msg}")

def print_fail(msg):
    print(f"{Colors.FAIL}[FAIL]{Colors.RESET} {msg}")

def print_warn(msg):
    print(f"{Colors.WARN}[WARN]{Colors.RESET} {msg}")

def print_info(msg):
    print(f"{Colors.INFO}[INFO]{Colors.RESET} {msg}")

results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0
}

def test_passed(name):
    results['passed'] += 1
    print_ok(name)

def test_failed(name, error=None):
    results['failed'] += 1
    print_fail(f"{name}: {error}" if error else name)

def test_warning(name, msg):
    results['warnings'] += 1
    print_warn(f"{name}: {msg}")

# ============================================================
# TEST 1: VARIABLES DE ENTORNO
# ============================================================
def test_environment():
    print_header("1. VARIABLES DE ENTORNO")

    required = [
        'DATABASE_URL',
        'OPENAI_API_KEY',
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_WHATSAPP_NUMBER',
    ]

    optional = [
        'CELERY_BROKER_URL',
        'CELERY_RESULT_BACKEND',
        'FLASK_ENV',
    ]

    for var in required:
        value = os.getenv(var)
        if value:
            # Ocultar valores sensibles
            display = value[:10] + '...' if len(value) > 10 else value
            test_passed(f"{var} = {display}")
        else:
            test_failed(f"{var} no configurada")

    for var in optional:
        value = os.getenv(var)
        if value:
            display = value[:30] + '...' if len(value) > 30 else value
            print_info(f"{var} = {display}")
        else:
            test_warning(var, "no configurada (opcional)")

# ============================================================
# TEST 2: CONEXION A POSTGRESQL
# ============================================================
def test_database():
    print_header("2. CONEXION A POSTGRESQL")

    try:
        from app import create_app, db
        from app.models import Lead, Conversation, Message, ClassReminder, Academy

        app = create_app()

        with app.app_context():
            # Test conexion
            db.engine.connect()
            test_passed("Conexion a PostgreSQL establecida")

            # Contar registros
            leads = Lead.query.count()
            conversations = Conversation.query.count()
            messages = Message.query.count()
            reminders = ClassReminder.query.count()

            print_info(f"Leads: {leads}")
            print_info(f"Conversaciones: {conversations}")
            print_info(f"Mensajes: {messages}")
            print_info(f"Recordatorios: {reminders}")

            # Verificar Academy info
            academy = Academy.query.first()
            if academy:
                test_passed(f"Academia encontrada: {academy.name}")
            else:
                test_warning("Academy", "No hay info de academia en BD")

    except Exception as e:
        test_failed("Conexion a PostgreSQL", str(e))

# ============================================================
# TEST 3: CONEXION A REDIS CLOUD
# ============================================================
def test_redis():
    print_header("3. CONEXION A REDIS CLOUD")

    broker_url = os.getenv('CELERY_BROKER_URL')

    if not broker_url:
        test_warning("Redis", "CELERY_BROKER_URL no configurada")
        return

    try:
        import redis

        r = redis.from_url(broker_url)
        response = r.ping()

        if response:
            test_passed("Conexion a Redis Cloud establecida")

            # Info del servidor
            info = r.info('server')
            print_info(f"Redis version: {info.get('redis_version', 'N/A')}")
            print_info(f"Keys en DB: {r.dbsize()}")
        else:
            test_failed("Redis no respondio PONG")

    except Exception as e:
        test_failed("Conexion a Redis", str(e))

# ============================================================
# TEST 4: OPENAI GPT-4o-mini
# ============================================================
def test_openai():
    print_header("4. OPENAI GPT-4o-mini")

    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        test_failed("OPENAI_API_KEY no configurada")
        return

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

        # Test simple
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Responde solo 'OK' si funcionas"}],
            max_tokens=10
        )

        result = response.choices[0].message.content.strip()

        if 'OK' in result.upper():
            test_passed(f"OpenAI {model} funcionando")
        else:
            test_passed(f"OpenAI respondio: {result}")

        # Mostrar uso de tokens
        usage = response.usage
        print_info(f"Tokens usados: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

    except Exception as e:
        test_failed("OpenAI", str(e))

# ============================================================
# TEST 5: MESSAGE HANDLER (Procesamiento de mensajes)
# ============================================================
def test_message_handler():
    print_header("5. MESSAGE HANDLER")

    try:
        from app import create_app
        from app.services.message_handler import MessageHandler

        app = create_app()

        with app.app_context():
            handler = MessageHandler()
            test_passed("MessageHandler inicializado")

            # Simular un mensaje de prueba
            test_phone = '+50699999999'
            test_message = 'Hola, quiero info sobre clases'
            test_name = 'Test User'

            print_info(f"Enviando mensaje de prueba: '{test_message}'")

            response = handler.process_message(
                phone_number=test_phone,
                message=test_message,
                name=test_name
            )

            if response:
                test_passed("Mensaje procesado correctamente")
                # Mostrar respuesta truncada
                display_response = response[:150] + '...' if len(response) > 150 else response
                print_info(f"Respuesta: {display_response}")
            else:
                test_failed("No se obtuvo respuesta")

    except Exception as e:
        test_failed("MessageHandler", str(e))

# ============================================================
# TEST 6: APPOINTMENT SCHEDULER
# ============================================================
def test_appointment_scheduler():
    print_header("6. APPOINTMENT SCHEDULER")

    try:
        from app import create_app
        from app.services.appointment_scheduler import AppointmentScheduler

        app = create_app()

        with app.app_context():
            scheduler = AppointmentScheduler()
            test_passed("AppointmentScheduler inicializado")

            # Verificar horarios cargados
            horarios = scheduler.horarios
            print_info(f"Horarios configurados: {list(horarios.keys())}")

            # Obtener slots disponibles
            slots = scheduler.get_available_slots(clase_tipo='adultos_jiujitsu', days_ahead=7)
            print_info(f"Slots disponibles proxima semana: {len(slots)}")

            if slots:
                test_passed(f"Primer slot: {slots[0]['display']}")

    except Exception as e:
        test_failed("AppointmentScheduler", str(e))

# ============================================================
# TEST 7: REMINDER SERVICE
# ============================================================
def test_reminder_service():
    print_header("7. REMINDER SERVICE")

    try:
        from app import create_app
        from app.services.reminder_service import ReminderService

        app = create_app()

        with app.app_context():
            reminder_service = ReminderService()
            test_passed("ReminderService inicializado")

            # Verificar recordatorios pendientes
            pending = reminder_service.get_pending_reminders(limit=10)
            print_info(f"Recordatorios pendientes: {len(pending)}")

            for r in pending[:3]:  # Mostrar primeros 3
                print_info(f"  - Lead {r.lead_id}: {r.class_type} @ {r.class_datetime}")

    except Exception as e:
        test_failed("ReminderService", str(e))

# ============================================================
# TEST 8: NOTIFICATION SERVICE
# ============================================================
def test_notification_service():
    print_header("8. NOTIFICATION SERVICE (Twilio)")

    try:
        from app.services.notification_service import NotificationService

        notifier = NotificationService()
        test_passed("NotificationService inicializado")

        # Solo verificar que Twilio client existe
        if hasattr(notifier, 'twilio_client') and notifier.twilio_client:
            test_passed("Twilio client configurado")
        else:
            test_warning("Twilio", "Client no disponible")

    except Exception as e:
        test_failed("NotificationService", str(e))

# ============================================================
# TEST 9: CELERY TASKS (sin ejecutar)
# ============================================================
def test_celery_tasks():
    print_header("9. CELERY TASKS")

    try:
        from app.celery_app import celery_app
        from app.tasks import reminder_tasks

        test_passed("Celery app importada")

        # Verificar tareas registradas
        tasks = [
            'app.tasks.reminder_tasks.check_and_send_reminders',
            'app.tasks.reminder_tasks.cleanup_old_reminders',
            'app.tasks.reminder_tasks.update_expired_trials',
            'app.tasks.reminder_tasks.send_immediate_reminder',
            'app.tasks.reminder_tasks.schedule_trial_reminders',
        ]

        for task_name in tasks:
            if task_name in celery_app.tasks:
                test_passed(f"Tarea registrada: {task_name.split('.')[-1]}")
            else:
                test_warning("Celery", f"Tarea no encontrada: {task_name}")

        # Verificar beat schedule
        schedule = celery_app.conf.beat_schedule
        print_info(f"Tareas programadas en Beat: {len(schedule)}")
        for name, config in schedule.items():
            print_info(f"  - {name}: {config['schedule']}")

    except Exception as e:
        test_failed("Celery Tasks", str(e))

# ============================================================
# TEST 10: DASHBOARD API
# ============================================================
def test_dashboard_api():
    print_header("10. DASHBOARD API")

    try:
        from app import create_app

        app = create_app()
        client = app.test_client()

        # Test endpoints
        endpoints = [
            ('/api/dashboard/stats', 'Stats'),
            ('/api/dashboard/leads', 'Leads'),
            ('/api/dashboard/conversations', 'Conversations'),
            ('/health', 'Health'),
        ]

        for endpoint, name in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                test_passed(f"GET {endpoint} -> 200 OK")
            else:
                test_warning(name, f"GET {endpoint} -> {response.status_code}")

    except Exception as e:
        test_failed("Dashboard API", str(e))

# ============================================================
# TEST 11: FLUJO COMPLETO DE CONVERSACION
# ============================================================
def test_full_conversation_flow():
    print_header("11. FLUJO COMPLETO DE CONVERSACION")

    try:
        from app import create_app, db
        from app.services.message_handler import MessageHandler
        from app.models import Lead, Conversation, Message

        app = create_app()

        with app.app_context():
            handler = MessageHandler()

            # Usar numero unico para este test
            test_phone = f'+5069999{datetime.now().strftime("%H%M%S")}'

            # Conversacion simulada
            messages = [
                ("Hola", "Saludo inicial"),
                ("Quiero info sobre clases de BJJ", "Consulta de clases"),
                ("Cuanto cuesta?", "Consulta de precios"),
            ]

            print_info(f"Simulando conversacion con {test_phone}")

            for msg, desc in messages:
                print_info(f"  Usuario: {msg}")
                response = handler.process_message(
                    phone_number=test_phone,
                    message=msg,
                    name='Test Flow'
                )
                # Truncar respuesta para display
                short_response = response[:80] + '...' if len(response) > 80 else response
                print_info(f"  Bot: {short_response}")

            # Verificar que se creo el lead
            lead = Lead.query.filter_by(phone=test_phone).first()
            if lead:
                test_passed(f"Lead creado: ID={lead.id}, Status={lead.status.value if hasattr(lead.status, 'value') else lead.status}")

                # Verificar conversacion
                conv = Conversation.query.filter_by(lead_id=lead.id).first()
                if conv:
                    msg_count = Message.query.filter_by(conversation_id=conv.id).count()
                    test_passed(f"Conversacion creada con {msg_count} mensajes")
                else:
                    test_failed("No se creo conversacion")
            else:
                test_failed("No se creo el lead")

            # Limpiar datos de test
            if lead:
                # Borrar mensajes
                if conv:
                    Message.query.filter_by(conversation_id=conv.id).delete()
                    Conversation.query.filter_by(id=conv.id).delete()
                Lead.query.filter_by(id=lead.id).delete()
                db.session.commit()
                print_info("Datos de test limpiados")

    except Exception as e:
        test_failed("Flujo de conversacion", str(e))
        import traceback
        traceback.print_exc()

# ============================================================
# RESUMEN FINAL
# ============================================================
def print_summary():
    print_header("RESUMEN DE TESTS")

    total = results['passed'] + results['failed']

    print(f"\n{Colors.OK}Pasados: {results['passed']}{Colors.RESET}")
    print(f"{Colors.FAIL}Fallidos: {results['failed']}{Colors.RESET}")
    print(f"{Colors.WARN}Advertencias: {results['warnings']}{Colors.RESET}")
    print(f"\nTotal: {total} tests")

    if results['failed'] == 0:
        print(f"\n{Colors.OK}{Colors.BOLD}TODOS LOS TESTS PASARON!{Colors.RESET}")
        print("El sistema esta listo para produccion.")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}HAY {results['failed']} TESTS FALLIDOS{Colors.RESET}")
        print("Revisa los errores antes de continuar.")

    print('='*60 + '\n')

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print(f"\n{Colors.BOLD}{'='*60}")
    print("TEST COMPLETO DEL SISTEMA BJJ MINGO BOT")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{Colors.RESET}")

    # Ejecutar todos los tests
    test_environment()
    test_database()
    test_redis()
    test_openai()
    test_message_handler()
    test_appointment_scheduler()
    test_reminder_service()
    test_notification_service()
    test_celery_tasks()
    test_dashboard_api()
    test_full_conversation_flow()

    # Mostrar resumen
    print_summary()

    # Exit code
    sys.exit(0 if results['failed'] == 0 else 1)
