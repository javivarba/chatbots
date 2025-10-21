"""
Script para limpiar datos de prueba y empezar desde cero
Mantiene la estructura de la BD pero elimina conversaciones y citas
"""

import sqlite3

db_path = 'bjj_academy.db'

print("=" * 60)
print("LIMPIEZA DE DATOS DE PRUEBA")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver estado actual
cursor.execute("SELECT COUNT(*) FROM lead")
lead_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM conversation")
conv_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM message")
msg_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM appointment")
apt_count = cursor.fetchone()[0]

print(f"\n📊 Estado actual:")
print(f"   Leads: {lead_count}")
print(f"   Conversaciones: {conv_count}")
print(f"   Mensajes: {msg_count}")
print(f"   Citas: {apt_count}")

# Confirmar
print("\n⚠️  ADVERTENCIA: Esto eliminará TODOS los datos excepto:")
print("   • Tabla 'academy' (info de la academia)")
print("   • Tabla 'schedule_slots' (horarios)")
print()
response = input("¿Continuar? (sí/no): ")

if response.lower() not in ['sí', 'si', 's', 'yes', 'y']:
    print("\n❌ Operación cancelada")
    conn.close()
    exit()

print("\n🧹 Limpiando datos...")

# Orden correcto para evitar errores de foreign key
try:
    # 1. Primero mensajes (dependen de conversations)
    cursor.execute("DELETE FROM message")
    deleted_msg = cursor.rowcount
    print(f"   ✓ {deleted_msg} mensajes eliminados")
    
    # 2. Luego appointments (dependen de leads)
    cursor.execute("DELETE FROM appointment")
    deleted_apt = cursor.rowcount
    print(f"   ✓ {deleted_apt} citas eliminadas")
    
    # 3. Luego conversations (dependen de leads)
    cursor.execute("DELETE FROM conversation")
    deleted_conv = cursor.rowcount
    print(f"   ✓ {deleted_conv} conversaciones eliminadas")
    
    # 4. Finalmente leads
    cursor.execute("DELETE FROM lead")
    deleted_lead = cursor.rowcount
    print(f"   ✓ {deleted_lead} leads eliminados")
    
    # Resetear los auto-increment IDs
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('lead', 'conversation', 'message', 'appointment')")
    
    conn.commit()
    
    print("\n✅ Base de datos limpiada exitosamente")
    
    # Verificar horarios se mantuvieron
    cursor.execute("SELECT COUNT(*) FROM schedule_slots")
    slots_count = cursor.fetchone()[0]
    print(f"\n📅 Horarios mantenidos: {slots_count} slots disponibles")
    
    cursor.execute("SELECT COUNT(*) FROM academy")
    academy_count = cursor.fetchone()[0]
    print(f"🏢 Academia mantenida: {academy_count} registro(s)")
    
except Exception as e:
    print(f"\n❌ Error durante la limpieza: {e}")
    conn.rollback()

conn.close()

print("\n" + "=" * 60)
print("✅ LISTO PARA EMPEZAR DESDE CERO")
print("=" * 60)
print("\n💡 Ahora puedes:")
print("   1. Reiniciar Flask: python run.py")
print("   2. Probar el sistema desde cero con WhatsApp")