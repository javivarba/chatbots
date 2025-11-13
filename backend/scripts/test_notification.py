"""
Script de prueba para el sistema de notificaciones
Verifica que las notificaciones se envíen correctamente al staff
"""

import sys
import os

# Agregar el directorio backend al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.notification_service import NotificationService
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_notification_service():
    """Prueba el servicio de notificaciones"""

    print("\n" + "="*60)
    print("PRUEBA DEL SISTEMA DE NOTIFICACIONES - BJJ MINGO")
    print("="*60 + "\n")

    # Inicializar servicio
    print("1. Inicializando NotificationService...")
    notifier = NotificationService()

    if not notifier.twilio_available:
        print("\n⚠️  ADVERTENCIA: Twilio no está disponible")
        print("   Verifica que:")
        print("   - Twilio esté instalado: pip install twilio")
        print("   - Las credenciales estén en .env:")
        print("     TWILIO_ACCOUNT_SID=...")
        print("     TWILIO_AUTH_TOKEN=...")
        print("     TWILIO_WHATSAPP_NUMBER=whatsapp:+...")
        print("\n   La notificación solo se registrará en logs.")
        input("\n   Presiona ENTER para continuar con la prueba...")
    else:
        print("   ✅ Twilio configurado correctamente\n")

    # Datos de prueba
    print("2. Preparando datos de prueba...")
    test_lead = {
        'name': 'Juan Pérez (PRUEBA)',
        'phone': '+506-1234-5678',
        'status': 'trial_scheduled'
    }

    test_trial = {
        'clase_nombre': 'Jiu-Jitsu Adultos',
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'dias_texto': 'Lunes a Viernes',
        'hora': '18:00',
        'notes': 'Mensaje de prueba del sistema de notificaciones'
    }

    print(f"   Prospecto: {test_lead['name']}")
    print(f"   Teléfono: {test_lead['phone']}")
    print(f"   Clase: {test_trial['clase_nombre']}")
    print(f"   Horario: {test_trial['dias_texto']} a las {test_trial['hora']}\n")

    # Enviar notificación de prueba
    print("3. Enviando notificación de prueba...")
    print("   Número destino: +50670150369\n")

    result = notifier.notify_new_trial_booking(test_lead, test_trial)

    print("\n" + "="*60)
    print("RESULTADO DE LA PRUEBA")
    print("="*60)

    if result['success']:
        print("✅ ¡Notificación enviada exitosamente!")
        print(f"   SID de Twilio: {result.get('sid', 'N/A')}")
        print("\n🔔 Verifica tu WhatsApp (+50670150369)")
        print("   Deberías recibir un mensaje con los detalles del prospecto.")
    else:
        print("❌ No se pudo enviar la notificación")
        print(f"   Razón: {result['message']}")

        if not notifier.twilio_available:
            print("\n💡 La notificación fue registrada en los logs del sistema.")
            print("   En producción, con Twilio configurado, se enviaría por WhatsApp.")

    print("\n" + "="*60 + "\n")


def test_full_flow():
    """Prueba el flujo completo: scheduler + notificaciones"""

    print("\n" + "="*60)
    print("PRUEBA DEL FLUJO COMPLETO - AGENDAMIENTO + NOTIFICACIÓN")
    print("="*60 + "\n")

    try:
        from app.services.appointment_scheduler import AppointmentScheduler
        import sqlite3

        print("1. Inicializando AppointmentScheduler...")
        scheduler = AppointmentScheduler()
        print("   ✅ Scheduler inicializado\n")

        # Crear un lead de prueba
        print("2. Creando lead de prueba en la base de datos...")
        conn = sqlite3.connect('bjj_academy.db')
        cursor = conn.cursor()

        # Verificar si ya existe
        cursor.execute("SELECT id FROM lead WHERE phone_number = ?", ('+506-TEST-9999',))
        existing = cursor.fetchone()

        if existing:
            lead_id = existing[0]
            print(f"   ℹ️  Lead de prueba ya existe (ID: {lead_id})")
        else:
            cursor.execute("""
                INSERT INTO lead (academy_id, phone_number, name, source, status, interest_level)
                VALUES (1, '+506-TEST-9999', 'María González (PRUEBA SISTEMA)', 'whatsapp', 'new', 5)
            """)
            conn.commit()
            lead_id = cursor.lastrowid
            print(f"   ✅ Lead de prueba creado (ID: {lead_id})")

        conn.close()

        # Agendar semana de prueba
        print("\n3. Agendando semana de prueba...")
        result = scheduler.book_trial_week(
            lead_id=lead_id,
            clase_tipo='adultos_jiujitsu',
            notes='Prueba completa del sistema de notificaciones'
        )

        print("\n" + "="*60)
        print("RESULTADO DEL FLUJO COMPLETO")
        print("="*60)

        if result['success']:
            print("✅ ¡Semana de prueba agendada exitosamente!")
            print(f"   Trial ID: {result.get('trial_id', 'N/A')}")
            print("\n📧 Mensaje enviado al cliente:")
            print("-" * 60)
            print(result['message'])
            print("-" * 60)
            print("\n🔔 Verifica tu WhatsApp (+50670150369)")
            print("   Deberías haber recibido una notificación sobre María González.")
        else:
            print("❌ Error al agendar semana de prueba")
            print(f"   Razón: {result['message']}")

        print("\n" + "="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error en la prueba del flujo completo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n🥋 SISTEMA DE PRUEBAS - BJJ MINGO")
    print("   Sistema de Notificaciones para Nuevos Prospectos\n")

    while True:
        print("Selecciona una opción:")
        print("1. Probar solo el servicio de notificaciones")
        print("2. Probar el flujo completo (agendamiento + notificación)")
        print("3. Salir")

        choice = input("\nOpción: ").strip()

        if choice == '1':
            test_notification_service()
        elif choice == '2':
            test_full_flow()
        elif choice == '3':
            print("\n¡Hasta luego! 🥋\n")
            break
        else:
            print("\n⚠️  Opción inválida. Intenta de nuevo.\n")
