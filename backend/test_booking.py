"""
Script para probar la detección de agendamiento
"""

import sys
sys.path.append('.')

from app.services.appointment_scheduler import AppointmentScheduler
from datetime import datetime

print("=" * 60)
print("PRUEBA DE DETECCIÓN DE AGENDAMIENTO")
print("=" * 60)

scheduler = AppointmentScheduler()

# Test 1: Parsear diferentes mensajes
test_messages = [
    "Quiero agendar miércoles a las 12",
    "Mi nombre es Javier Vargas, miércoles a las 12 sin Gi",
    "Mañana a las 6pm",
    "Lunes 18:00",
    "clase el sábado a las 9am"
]

print("\n📝 Probando parseo de mensajes:")
print("-" * 60)

for msg in test_messages:
    parsed = scheduler.parse_appointment_request(msg)
    print(f"\nMensaje: '{msg}'")
    print(f"  ✓ Parseado: {parsed['parsed']}")
    if parsed['parsed']:
        print(f"  ✓ Fecha: {parsed['date']}")
        print(f"  ✓ Hora: {parsed['time']}")
        print(f"  ✓ DateTime: {parsed['datetime']}")
    else:
        print(f"  ✗ No se pudo parsear")

# Test 2: Ver slots disponibles
print("\n\n📅 Horarios disponibles:")
print("-" * 60)

try:
    slots = scheduler.get_available_slots(days_ahead=5)
    
    if not slots:
        print("⚠️ No hay slots disponibles")
        print("   Necesitas ejecutar el script de inicialización de horarios")
    else:
        for slot in slots[:10]:  # Primeros 10
            print(f"  {slot['display']} ({slot['available']} lugares)")
except Exception as e:
    print(f"❌ Error obteniendo slots: {e}")

# Test 3: Intentar crear una cita de prueba
print("\n\n🔧 Probando creación de cita:")
print("-" * 60)

# Buscar un lead de prueba
import sqlite3
conn = sqlite3.connect('bjj_academy.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name, phone_number FROM lead LIMIT 1")
lead = cursor.fetchone()

if lead:
    lead_id = lead[0]
    print(f"Lead encontrado: {lead[1]} ({lead[2]})")
    
    # Intentar agendar para mañana a las 12:00
    tomorrow = datetime.now()
    tomorrow = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    tomorrow = tomorrow + timedelta(days=1)
    
    appointment_datetime = tomorrow.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\nIntentando agendar para: {appointment_datetime}")
    
    result = scheduler.book_appointment(
        lead_id,
        appointment_datetime,
        "Test de agendamiento"
    )
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"📅 Link de calendario:")
        print(f"   {result['calendar_link'][:100]}...")
        
        # Limpiar - cancelar la cita de prueba
        cursor.execute("""
            UPDATE appointment 
            SET status = 'cancelled' 
            WHERE lead_id = ? AND status = 'scheduled'
            ORDER BY created_at DESC
            LIMIT 1
        """, (lead_id,))
        conn.commit()
        print("\n🧹 Cita de prueba cancelada")
    else:
        print(f"❌ {result['message']}")
else:
    print("⚠️ No hay leads en la base de datos")

conn.close()

print("\n" + "=" * 60)
print("PRUEBA COMPLETADA")
print("=" * 60)