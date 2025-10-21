"""
Script para arreglar el schema de la base de datos
Agrega las columnas faltantes a la tabla academy
"""

import sqlite3
import os

db_path = 'bjj_academy.db'

if not os.path.exists(db_path):
    print(f"❌ Base de datos no encontrada: {db_path}")
    exit(1)

print("🔧 Arreglando schema de la base de datos...")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver columnas actuales
cursor.execute("PRAGMA table_info(academy)")
current_columns = {row[1] for row in cursor.fetchall()}
print(f"\n📋 Columnas actuales en 'academy':")
for col in current_columns:
    print(f"   • {col}")

# Columnas que necesitamos
required_columns = {
    'description': 'TEXT',
    'instructor_name': 'TEXT',
    'instructor_belt': 'TEXT',
    'address_street': 'TEXT',
    'address_city': 'TEXT',
    'ai_context': 'TEXT'
}

# Agregar columnas faltantes
print(f"\n🔨 Agregando columnas faltantes...")
for col_name, col_type in required_columns.items():
    if col_name not in current_columns:
        try:
            cursor.execute(f"ALTER TABLE academy ADD COLUMN {col_name} {col_type}")
            print(f"   ✓ Agregada: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print(f"   - Ya existe: {col_name}")
            else:
                print(f"   ✗ Error: {col_name} - {e}")
    else:
        print(f"   - Ya existe: {col_name}")

# Actualizar datos de la academia con información completa
print(f"\n📝 Actualizando información de la academia...")
cursor.execute("""
    UPDATE academy 
    SET 
        description = COALESCE(description, 'Academia de Brazilian Jiu-Jitsu de alto nivel'),
        instructor_name = COALESCE(instructor_name, 'Instructor Profesional'),
        instructor_belt = COALESCE(instructor_belt, 'Black Belt'),
        address_street = COALESCE(address_street, 'Santo Domingo de Heredia'),
        address_city = COALESCE(address_city, 'Santo Domingo'),
        ai_context = COALESCE(ai_context, 'Somos una academia especializada en BJJ para todos los niveles')
    WHERE id = 1
""")

conn.commit()

# Verificar resultado final
cursor.execute("PRAGMA table_info(academy)")
final_columns = [row[1] for row in cursor.fetchall()]

print(f"\n✅ Columnas finales en 'academy':")
for col in final_columns:
    print(f"   • {col}")

# Mostrar datos de la academia
cursor.execute("SELECT id, name, description, instructor_name, phone FROM academy WHERE id = 1")
academy = cursor.fetchone()

if academy:
    print(f"\n📊 Datos de la academia:")
    print(f"   ID: {academy[0]}")
    print(f"   Nombre: {academy[1]}")
    print(f"   Descripción: {academy[2][:50]}..." if academy[2] else "   Descripción: None")
    print(f"   Instructor: {academy[3]}")
    print(f"   Teléfono: {academy[4]}")

conn.close()

print("\n" + "=" * 60)
print("✅ Base de datos actualizada exitosamente")
print("=" * 60)
print("\n💡 Ahora reinicia Flask: python run.py")