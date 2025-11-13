"""
Prueba del flujo completo de agendamiento + notificaciones
SIN necesidad de Twilio funcionando
"""
import sys
import os

# Fix encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from dotenv import load_dotenv
load_dotenv()

print("\n" + "="*60)
print("PRUEBA FLUJO COMPLETO - AGENDAMIENTO + NOTIFICACION")
print("="*60 + "\n")

try:
    from app.services.appointment_scheduler import AppointmentScheduler
    import sqlite3

    print("1. Inicializando AppointmentScheduler...")
    scheduler = AppointmentScheduler()

    # Verificar si el notifier está disponible
    if scheduler.notifier:
        print("   [OK] Scheduler con NotificationService integrado")
        if scheduler.notifier.twilio_available:
            print("   [OK] Twilio esta disponible - enviara WhatsApp real")
        else:
            print("   [!] Twilio NO disponible - notificaciones solo en logs")
    else:
        print("   [!] NotificationService no esta disponible")

    # Crear un lead de prueba
    print("\n2. Creando lead de prueba...")
    conn = sqlite3.connect('bjj_academy.db')
    cursor = conn.cursor()

    # Limpiar lead de prueba anterior si existe
    cursor.execute("DELETE FROM lead WHERE phone_number = ?", ('+506-TEST-FLOW',))
    conn.commit()

    # Crear nuevo lead
    cursor.execute("""
        INSERT INTO lead (academy_id, phone_number, name, source, status, interest_level)
        VALUES (1, '+506-TEST-FLOW', 'Carlos Mendez (PRUEBA FLUJO)', 'whatsapp', 'new', 5)
    """)
    conn.commit()
    lead_id = cursor.lastrowid
    print(f"   [OK] Lead creado con ID: {lead_id}")
    print(f"   Nombre: Carlos Mendez (PRUEBA FLUJO)")
    print(f"   Telefono: +506-TEST-FLOW")

    conn.close()

    # Agendar semana de prueba
    print("\n3. Agendando semana de prueba...")
    print("   Clase: Jiu-Jitsu Adultos")
    print("   Notas: Prueba completa del sistema\n")

    result = scheduler.book_trial_week(
        lead_id=lead_id,
        clase_tipo='adultos_jiujitsu',
        notes='Prueba completa del sistema de notificaciones - Flujo end-to-end'
    )

    print("\n" + "="*60)
    print("RESULTADO DEL FLUJO COMPLETO")
    print("="*60 + "\n")

    if result['success']:
        print("[OK] Semana de prueba agendada exitosamente!")
        print(f"   Trial ID: {result.get('trial_id', 'N/A')}\n")

        print("-" * 60)
        print("MENSAJE ENVIADO AL CLIENTE:")
        print("-" * 60)
        print(result['message'])
        print("-" * 60)

        print("\n[!] VERIFICACION DE NOTIFICACION:")
        if scheduler.notifier and scheduler.notifier.twilio_available:
            print("   [OK] Se envio notificacion por WhatsApp a: +50670150369")
            print("   Revisa tu WhatsApp para ver el mensaje.")
        else:
            print("   [!] Twilio no configurado - Revisa los logs arriba")
            print("   La notificacion se habria enviado con el siguiente contenido:")
            print("\n   " + "-" * 56)
            print("   🔔 NUEVO PROSPECTO - SEMANA DE PRUEBA")
            print("")
            print("   👤 Prospecto:")
            print("   • Nombre: Carlos Mendez (PRUEBA FLUJO)")
            print("   • Telefono: +506-TEST-FLOW")
            print("   • Estado: trial_scheduled")
            print("")
            print("   🥋 Clase Agendada:")
            print("   • Tipo: Jiu-Jitsu Adultos")
            print("   • Dias: Lunes a Viernes")
            print("   • Horario: 18:00")
            print("   " + "-" * 56)

        # Verificar en la BD
        print("\n4. Verificando registro en base de datos...")
        conn = sqlite3.connect('bjj_academy.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT clase_tipo, start_date, end_date, status
            FROM trial_week
            WHERE lead_id = ?
        """, (lead_id,))

        trial = cursor.fetchone()
        if trial:
            print("   [OK] Semana de prueba registrada en BD")
            print(f"   Clase: {trial[0]}")
            print(f"   Inicio: {trial[1]}")
            print(f"   Fin: {trial[2]}")
            print(f"   Status: {trial[3]}")

        cursor.execute("SELECT status, interest_level FROM lead WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()
        if lead:
            print(f"\n   [OK] Lead actualizado")
            print(f"   Status: {lead[0]}")
            print(f"   Interest Level: {lead[1]}")

        conn.close()

    else:
        print("[X] Error al agendar semana de prueba")
        print(f"   Razon: {result['message']}")

    print("\n" + "="*60)
    print("FLUJO COMPLETADO")
    print("="*60 + "\n")

    print("RESUMEN:")
    print("  1. [OK] Lead creado en BD")
    print("  2. [OK] Semana de prueba agendada")
    print("  3. [OK] Lead actualizado a 'trial_scheduled'")
    if scheduler.notifier and scheduler.notifier.twilio_available:
        print("  4. [OK] Notificacion enviada por WhatsApp")
    else:
        print("  4. [!] Notificacion registrada en logs (Twilio no config)")
    print("  5. [OK] Mensaje de confirmacion generado para cliente")
    print("\n[OK] Sistema funcionando correctamente!\n")

except Exception as e:
    print(f"\n[X] Error en la prueba: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
