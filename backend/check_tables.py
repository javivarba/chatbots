"""
Script para ver la estructura de las tablas
"""

import sqlite3

db_path = 'bjj_academy.db'

print("=" * 60)
print("ESTRUCTURA DE TABLAS")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\nTablas en la base de datos:")
for table in tables:
    print(f"  • {table[0]}")

# Ver estructura de schedule_slots
print("\n" + "=" * 60)
print("ESTRUCTURA DE 'schedule_slots'")
print("=" * 60)

cursor.execute("PRAGMA table_info(schedule_slots)")
columns = cursor.fetchall()

if columns:
    print("\nColumnas existentes:")
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"  {col_id}. {name} ({col_type}){' NOT NULL' if not_null else ''}{' PRIMARY KEY' if pk else ''}")
else:
    print("\n⚠️ Tabla 'schedule_slots' NO existe")

# Ver estructura de appointment
print("\n" + "=" * 60)
print("ESTRUCTURA DE 'appointment'")
print("=" * 60)

cursor.execute("PRAGMA table_info(appointment)")
columns = cursor.fetchall()

if columns:
    print("\nColumnas existentes:")
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"  {col_id}. {name} ({col_type}){' NOT NULL' if not_null else ''}{' PRIMARY KEY' if pk else ''}")
else:
    print("\n⚠️ Tabla 'appointment' NO existe")

conn.close()

print("\n" + "=" * 60)