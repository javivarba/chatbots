import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('bjj_academy.db')
cursor = conn.cursor()

print("=== DIAGNÓSTICO DE LA BASE DE DATOS ===\n")

# Verificar si la tabla existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='academy'")
tabla_existe = cursor.fetchone()

if not tabla_existe:
    print("❌ La tabla 'academy' no existe")
    print("Creando tabla academy...")
    cursor.execute("""
        CREATE TABLE academy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100),
            phone VARCHAR(20),
            email VARCHAR(100),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            instructor_name TEXT,
            instructor_belt TEXT,
            address_street TEXT,
            address_city TEXT,
            ai_context TEXT
        )
    """)
    conn.commit()
    print("✅ Tabla creada")

# Contar registros
cursor.execute("SELECT COUNT(*) FROM academy")
count = cursor.fetchone()[0]
print(f"\nRegistros en academy: {count}")

if count == 0:
    print("\n📝 Insertando datos de BJJ Mingo...")
    cursor.execute("""
        INSERT INTO academy (
            name, phone, address_street, address_city, 
            description, instructor_name, instructor_belt, ai_context
        ) VALUES (
            'BJJ Mingo',
            '+506-8888-8888',
            'Santo Domingo de Heredia',
            'Heredia',
            'Academia de Jiu-Jitsu brasileño ubicada en Santo Domingo de Heredia, Costa Rica. Ofrecemos clases de Jiu-Jitsu y Striking para niños, adolescentes y adultos en un ambiente familiar, respetuoso y profesional.',
            'Juan Carlos, Michael, Joaquín, César',
            'Instructores certificados',
            'BJJ Mingo es una academia familiar donde hombres y mujeres entrenan juntos en un ambiente de respeto. Los padres pueden entrenar mientras sus hijos toman clases. Ofrecemos una semana de prueba completamente gratis. Usamos voseo costarricense en todas las comunicaciones.'
        )
    """)
    conn.commit()
    print("✅ Datos insertados")
else:
    print("\n📝 Actualizando datos existentes...")
    cursor.execute("""
        UPDATE academy 
        SET 
            name = 'BJJ Mingo',
            phone = '+506-8888-8888',
            address_street = 'Santo Domingo de Heredia',
            address_city = 'Heredia',
            description = 'Academia de Jiu-Jitsu brasileño ubicada en Santo Domingo de Heredia, Costa Rica. Ofrecemos clases de Jiu-Jitsu y Striking para niños, adolescentes y adultos en un ambiente familiar, respetuoso y profesional.',
            instructor_name = 'Juan Carlos, Michael, Joaquín, César',
            instructor_belt = 'Instructores certificados',
            ai_context = 'BJJ Mingo es una academia familiar donde hombres y mujeres entrenan juntos en un ambiente de respeto. Los padres pueden entrenar mientras sus hijos toman clases. Ofrecemos una semana de prueba completamente gratis. Usamos voseo costarricense en todas las comunicaciones.'
        WHERE id = 1
    """)
    conn.commit()
    print("✅ Datos actualizados")

# Verificar resultado final
cursor.execute("SELECT name, phone, instructor_name, address_street FROM academy WHERE id = 1")
result = cursor.fetchone()

if result:
    print("\n=== DATOS FINALES ===")
    print(f"Nombre: {result[0]}")
    print(f"Teléfono: {result[1]}")
    print(f"Instructores: {result[2]}")
    print(f"Dirección: {result[3]}")
    print("\n✅ ¡Base de datos configurada correctamente!")
else:
    print("\n❌ Error: No se pudo configurar la base de datos")

conn.close()