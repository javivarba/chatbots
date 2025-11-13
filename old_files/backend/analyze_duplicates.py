"""
Script de Diagnóstico de Tablas Duplicadas
Analiza las tablas duplicadas para decidir cómo consolidarlas
"""

import sqlite3
import os
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def analyze_table_pair(cursor, table1, table2, id_column='id'):
    """Analiza un par de tablas duplicadas"""
    
    print_header(f"ANALIZANDO: {table1.upper()} vs {table2.upper()}")
    
    # Obtener schemas
    cursor.execute(f"PRAGMA table_info({table1})")
    schema1 = cursor.fetchall()
    
    cursor.execute(f"PRAGMA table_info({table2})")
    schema2 = cursor.fetchall()
    
    # Contar registros
    cursor.execute(f"SELECT COUNT(*) FROM {table1}")
    count1 = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {table2}")
    count2 = cursor.fetchone()[0]
    
    # Obtener fechas de última actualización (si existe columna de timestamp)
    last_update1 = get_last_update(cursor, table1)
    last_update2 = get_last_update(cursor, table2)
    
    # Mostrar información
    print(f"\n{Colors.BOLD}TABLA: {table1}{Colors.ENDC}")
    print(f"  📊 Registros: {count1}")
    print(f"  📅 Última actividad: {last_update1 or 'Desconocido'}")
    print(f"  🏗️  Columnas: {len(schema1)}")
    
    print(f"\n{Colors.BOLD}TABLA: {table2}{Colors.ENDC}")
    print(f"  📊 Registros: {count2}")
    print(f"  📅 Última actividad: {last_update2 or 'Desconocido'}")
    print(f"  🏗️  Columnas: {len(schema2)}")
    
    # Comparar schemas
    print(f"\n{Colors.BOLD}COMPARACIÓN DE SCHEMAS:{Colors.ENDC}")
    
    cols1 = {col[1]: col for col in schema1}  # nombre: info_completa
    cols2 = {col[1]: col for col in schema2}
    
    # Columnas solo en tabla1
    only_in_1 = set(cols1.keys()) - set(cols2.keys())
    if only_in_1:
        print(f"  ⚠️  Solo en {table1}: {', '.join(only_in_1)}")
    
    # Columnas solo en tabla2
    only_in_2 = set(cols2.keys()) - set(cols1.keys())
    if only_in_2:
        print(f"  ⚠️  Solo en {table2}: {', '.join(only_in_2)}")
    
    # Columnas comunes
    common = set(cols1.keys()) & set(cols2.keys())
    print(f"  ✅ Columnas comunes: {len(common)}")
    
    # Determinar similitud de schemas
    total_cols = len(set(cols1.keys()) | set(cols2.keys()))
    similarity = len(common) / total_cols * 100 if total_cols > 0 else 0
    
    print(f"  📊 Similitud de schemas: {similarity:.1f}%")
    
    # Recomendación
    print(f"\n{Colors.BOLD}RECOMENDACIÓN:{Colors.ENDC}")
    
    if similarity < 50:
        print_warning(f"Schemas muy diferentes - revisar manualmente")
        return "manual_review"
    
    # Determinar cuál tabla es la "activa"
    if count1 == 0 and count2 == 0:
        print_info("Ambas tablas vacías - eliminar ambas o mantener la más completa")
        active_table = table1 if len(schema1) >= len(schema2) else table2
        return {"action": "keep_empty", "keep": active_table, "remove": table2 if active_table == table1 else table1}
    
    elif count1 == 0:
        print_success(f"Mantener: {table2} (tiene datos)")
        print_error(f"Eliminar: {table1} (vacía)")
        return {"action": "simple_delete", "keep": table2, "remove": table1}
    
    elif count2 == 0:
        print_success(f"Mantener: {table1} (tiene datos)")
        print_error(f"Eliminar: {table2} (vacía)")
        return {"action": "simple_delete", "keep": table1, "remove": table2}
    
    else:
        # Ambas tienen datos - determinar por última actividad
        if last_update1 and last_update2:
            if last_update1 > last_update2:
                print_success(f"Mantener: {table1} (más reciente: {last_update1})")
                print_warning(f"Migrar datos de: {table2} → {table1}")
                return {"action": "merge", "keep": table1, "merge_from": table2}
            else:
                print_success(f"Mantener: {table2} (más reciente: {last_update2})")
                print_warning(f"Migrar datos de: {table1} → {table2}")
                return {"action": "merge", "keep": table2, "merge_from": table1}
        else:
            # Si no hay timestamps, mantener la que tiene más registros
            if count1 >= count2:
                print_success(f"Mantener: {table1} ({count1} registros)")
                print_warning(f"Revisar: {table2} ({count2} registros)")
                return {"action": "review", "keep": table1, "review": table2}
            else:
                print_success(f"Mantener: {table2} ({count2} registros)")
                print_warning(f"Revisar: {table1} ({count1} registros)")
                return {"action": "review", "keep": table2, "review": table1}

def get_last_update(cursor, table):
    """Obtiene la fecha de última actualización de una tabla"""
    
    # Intentar varias columnas comunes de timestamp
    timestamp_columns = ['updated_at', 'last_message_at', 'created_at', 'timestamp']
    
    for col in timestamp_columns:
        try:
            cursor.execute(f"SELECT {col} FROM {table} ORDER BY {col} DESC LIMIT 1")
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
        except:
            continue
    
    return None

def check_foreign_keys(cursor, table):
    """Verifica si otras tablas tienen foreign keys a esta tabla"""
    
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='table' AND sql LIKE ?
    """, (f'%FOREIGN KEY%{table}%',))
    
    references = cursor.fetchall()
    
    if references:
        print_warning(f"  ⚠️  Otras tablas tienen foreign keys a '{table}':")
        for ref in references:
            # Extraer nombre de tabla del SQL
            sql = ref[0]
            table_name = sql.split('CREATE TABLE ')[1].split('(')[0].strip()
            print(f"      • {table_name}")
        return True
    
    return False

def analyze_all_duplicates(db_path='bjj_academy.db'):
    """Analiza todos los pares de tablas duplicadas"""
    
    print_header("🔍 DIAGNÓSTICO DE TABLAS DUPLICADAS")
    print_info(f"Base de datos: {db_path}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not os.path.exists(db_path):
        print_error(f"Base de datos no encontrada: {db_path}")
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Pares de tablas duplicadas
    duplicate_pairs = [
        ('academy', 'academies'),
        ('lead', 'leads'),
        ('conversation', 'conversations'),
        ('message', 'messages')
    ]
    
    recommendations = {}
    
    for table1, table2 in duplicate_pairs:
        recommendation = analyze_table_pair(cursor, table1, table2)
        recommendations[f"{table1}/{table2}"] = recommendation
        
        # Verificar foreign keys
        print(f"\n{Colors.BOLD}FOREIGN KEYS:{Colors.ENDC}")
        has_fk1 = check_foreign_keys(cursor, table1)
        has_fk2 = check_foreign_keys(cursor, table2)
        
        if not has_fk1 and not has_fk2:
            print_info(f"  ✅ Ninguna tabla tiene foreign keys - seguro eliminar")
    
    conn.close()
    
    # Resumen de recomendaciones
    print_header("📊 RESUMEN DE RECOMENDACIONES")
    
    for pair, rec in recommendations.items():
        if isinstance(rec, dict):
            print(f"\n{Colors.BOLD}{pair}:{Colors.ENDC}")
            
            if rec['action'] == 'simple_delete':
                print_success(f"  ✅ Acción: Eliminar '{rec['remove']}' (vacía)")
            
            elif rec['action'] == 'keep_empty':
                print_info(f"  ℹ️  Acción: Mantener '{rec['keep']}' (ambas vacías)")
            
            elif rec['action'] == 'merge':
                print_warning(f"  ⚠️  Acción: Migrar datos de '{rec['merge_from']}' → '{rec['keep']}'")
            
            elif rec['action'] == 'review':
                print_warning(f"  ⚠️  Acción: Revisar manualmente - ambas tienen datos")
        else:
            print(f"\n{Colors.BOLD}{pair}:{Colors.ENDC}")
            print_warning(f"  ⚠️  Requiere revisión manual")
    
    # Advertencias finales
    print_header("⚠️  ADVERTENCIAS IMPORTANTES")
    print_warning("Antes de eliminar tablas:")
    print("  1. Crear backup completo de la base de datos")
    print("  2. Detener la aplicación (si está corriendo)")
    print("  3. Verificar que no haya código usando las tablas a eliminar")
    print("  4. Probar en ambiente de desarrollo primero")
    
    return recommendations

def show_sample_data(db_path='bjj_academy.db'):
    """Muestra datos de ejemplo de cada tabla"""
    
    print_header("📋 MUESTRA DE DATOS")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ['academy', 'academies', 'lead', 'leads', 
              'conversation', 'conversations', 'message', 'messages']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            rows = cursor.fetchall()
            
            if rows:
                print(f"\n{Colors.BOLD}{table}:{Colors.ENDC}")
                for i, row in enumerate(rows, 1):
                    print(f"  {i}. {str(row)[:100]}...")
            else:
                print(f"\n{Colors.BOLD}{table}:{Colors.ENDC} (vacía)")
        except Exception as e:
            print_error(f"Error leyendo {table}: {e}")
    
    conn.close()

if __name__ == "__main__":
    recommendations = analyze_all_duplicates()
    
    print("\n")
    show_sample_data()
    
    print_header("🔧 PRÓXIMOS PASOS")
    print_info("1. Revisar las recomendaciones arriba")
    print_info("2. Crear backup: python backup_database.py")
    print_info("3. Ejecutar consolidación: python consolidate_tables.py")