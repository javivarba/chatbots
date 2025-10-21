"""
Script para arreglar los horarios reales de BJJ Mingo
"""

import sqlite3

db_path = 'bjj_academy.db'

print("=" * 60)
print("ARREGLANDO HORARIOS DE BJJ MINGO")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Limpiar horarios existentes
print("\n1️⃣ Limpiando horarios anteriores...")
cursor.execute("DELETE FROM schedule_slots")
print("   ✓ Horarios anteriores eliminados")

# 2. Insertar horarios REALES de BJJ Mingo
print("\n2️⃣ Insertando horarios reales...")

horarios = [
    # LUNES (day_of_week = 1)
    (1, '12:00', 10, 1),  # With Gi
    (1, '17:00', 10, 1),  # Junior
    (1, '19:15', 15, 1),  # With Gi
    
    # MARTES (day_of_week = 2)
    (2, '12:00', 10, 1),  # Without Gi
    (2, '17:00', 10, 1),  # Kids
    (2, '18:00', 15, 1),  # Open
    (2, '19:15', 15, 1),  # Without Gi
    
    # MIÉRCOLES (day_of_week = 3)
    (3, '12:00', 10, 1),  # With Gi
    (3, '17:00', 10, 1),  # Junior
    (3, '19:15', 15, 1),  # With Gi
    
    # JUEVES (day_of_week = 4)
    (4, '12:00', 10, 1),  # Without Gi
    (4, '17:00', 10, 1),  # Kids
    (4, '18:00', 15, 1),  # Open
    (4, '19:15', 15, 1),  # Without Gi
    
    # VIERNES (day_of_week = 5)
    (5, '12:00', 15, 1),  # Open
    (5, '18:00', 15, 1),  # Open
    (5, '19:00', 15, 1),  # Open
]

day_names = ['', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
descriptions = {
    (1, '12:00'): 'With Gi',
    (1, '17:00'): 'Junior (11-15 años)',
    (1, '19:15'): 'With Gi',
    (2, '12:00'): 'Without Gi',
    (2, '17:00'): 'Kids (5-10 años)',
    (2, '18:00'): 'Open',
    (2, '19:15'): 'Without Gi',
    (3, '12:00'): 'With Gi',
    (3, '17:00'): 'Junior (11-15 años)',
    (3, '19:15'): 'With Gi',
    (4, '12:00'): 'Without Gi',
    (4, '17:00'): 'Kids (5-10 años)',
    (4, '18:00'): 'Open',
    (4, '19:15'): 'Without Gi',
    (5, '12:00'): 'Open',
    (5, '18:00'): 'Open',
    (5, '19:00'): 'Open',
}

for day, time, capacity, is_active in horarios:
    cursor.execute("""
        INSERT INTO schedule_slots 
        (day_of_week, time_slot, max_capacity, is_active)
        VALUES (?, ?, ?, ?)
    """, (day, time, capacity, is_active))
    
    desc = descriptions.get((day, time), '')
    print(f"   ✓ {day_names[day]} {time} - {desc} ({capacity} lugares)")

conn.commit()

# 3. Verificar resultado
print("\n3️⃣ Verificando horarios insertados...")
cursor.execute("""
    SELECT day_of_week, time_slot, max_capacity 
    FROM schedule_slots 
    ORDER BY day_of_week, time_slot
""")
conn.commit()

slots = cursor.fetchall()
print(f"\n   Total de horarios: {len(slots)}")

current_day = None

for day, time, capacity in slots:
    if day != current_day:
        print(f"\n   {day_names[day]}:")
        current_day = day
    desc = descriptions.get((day, time), '')
    print(f"      • {time} - {desc} ({capacity} lugares)")

# 4. Limpiar citas de prueba
print("\n4️⃣ Limpiando citas antiguas/de prueba...")
cursor.execute("SELECT COUNT(*) FROM appointment")
total_appointments = cursor.fetchone()[0]
print(f"   Citas existentes: {total_appointments}")

if total_appointments > 0:
    response = input("\n   ¿Quieres eliminar TODAS las citas? (sí/no): ")
    if response.lower() in ['sí', 'si', 's', 'yes', 'y']:
        cursor.execute("DELETE FROM appointment")
        conn.commit()
        print("   ✓ Todas las citas eliminadas")
    else:
        print("   - Citas conservadas")

conn.close()

print("\n" + "=" * 60)
print("✅ HORARIOS ACTUALIZADOS CORRECTAMENTE")
print("=" * 60)
print("\n💡 Ahora ejecuta de nuevo: python test_booking.py")
print("   Los horarios deben coincidir con BJJ Mingo")