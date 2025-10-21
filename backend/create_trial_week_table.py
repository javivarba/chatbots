import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('bjj_academy.db')
cursor = conn.cursor()

print("=== CREANDO TABLA trial_week ===\n")

# Verificar si la tabla ya existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trial_week'")
tabla_existe = cursor.fetchone()

if tabla_existe:
    print("⚠️  La tabla 'trial_week' ya existe")
    print("¿Querés recrearla? (se perderán los datos existentes)")
    respuesta = input("Escribí 'si' para continuar: ")
    
    if respuesta.lower() == 'si':
        cursor.execute("DROP TABLE trial_week")
        print("✅ Tabla anterior eliminada")
    else:
        print("❌ Operación cancelada")
        conn.close()
        exit()

# Crear la tabla trial_week
cursor.execute("""
    CREATE TABLE trial_week (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        clase_tipo VARCHAR(50) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES lead(id)
    )
""")

print("✅ Tabla 'trial_week' creada exitosamente")

# Crear índices para mejorar el rendimiento
cursor.execute("""
    CREATE INDEX idx_trial_week_lead_id ON trial_week(lead_id)
""")

cursor.execute("""
    CREATE INDEX idx_trial_week_status ON trial_week(status)
""")

print("✅ Índices creados")

conn.commit()

# Verificar la estructura de la tabla
cursor.execute("PRAGMA table_info(trial_week)")
columnas = cursor.fetchall()

print("\n=== ESTRUCTURA DE LA TABLA trial_week ===")
for columna in columnas:
    print(f"{columna[1]} ({columna[2]})")

print("\n=== RESUMEN ===")
print("✅ Tabla trial_week lista para usar")
print("✅ Campos:")
print("   - id: ID único de la semana de prueba")
print("   - lead_id: Referencia al prospecto")
print("   - clase_tipo: adultos_jiujitsu, adultos_striking, kids, juniors")
print("   - start_date: Fecha de inicio de la semana")
print("   - end_date: Fecha de fin de la semana")
print("   - status: active, completed, cancelled")
print("   - notes: Notas adicionales")
print("   - created_at: Fecha de creación del registro")

conn.close()
print("\n✅ ¡Base de datos actualizada correctamente!")