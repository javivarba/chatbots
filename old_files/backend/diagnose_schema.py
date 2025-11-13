"""
Script de Diagnóstico del Schema de Base de Datos
Verifica el schema actual de todas las tablas en bjj_academy.db
"""

import sqlite3
import os

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def diagnose_database(db_path='bjj_academy.db'):
    """Diagnostica el schema completo de la base de datos"""
    
    if not os.path.exists(db_path):
        print_warning(f"Base de datos no encontrada: {db_path}")
        return
    
    print_header("🔍 DIAGNÓSTICO DEL SCHEMA DE BASE DE DATOS")
    print_info(f"Base de datos: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print_success(f"Tablas encontradas: {len(tables)}")
    print(f"  {', '.join(tables)}\n")
    
    # Para cada tabla, mostrar su schema
    for table in tables:
        print_header(f"TABLA: {table}")
        
        # Obtener información de las columnas
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print(f"{Colors.BOLD}Columnas:{Colors.ENDC}")
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            pk_mark = f"{Colors.GREEN}[PK]{Colors.ENDC}" if pk else ""
            null_mark = f"{Colors.RED}NOT NULL{Colors.ENDC}" if notnull else "NULL"
            default_mark = f"DEFAULT {default}" if default else ""
            
            print(f"  {col_id}. {Colors.BOLD}{name}{Colors.ENDC} {pk_mark}")
            print(f"     Tipo: {type_}, {null_mark} {default_mark}")
        
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"\n{Colors.BLUE}Registros: {count}{Colors.ENDC}\n")
    
    # Verificar columnas críticas faltantes
    print_header("🔍 VERIFICACIÓN DE COLUMNAS CRÍTICAS")
    
    issues_found = []
    
    # Verificar tabla conversation
    cursor.execute("PRAGMA table_info(conversation)")
    conv_columns = [col[1] for col in cursor.fetchall()]
    
    if 'created_at' not in conv_columns:
        issues_found.append("❌ Tabla 'conversation' NO tiene columna 'created_at'")
    else:
        print_success("Tabla 'conversation' tiene columna 'created_at'")
    
    if 'last_message_at' not in conv_columns:
        issues_found.append("❌ Tabla 'conversation' NO tiene columna 'last_message_at'")
    else:
        print_success("Tabla 'conversation' tiene columna 'last_message_at'")
    
    # Verificar tabla lead
    cursor.execute("PRAGMA table_info(lead)")
    lead_columns = [col[1] for col in cursor.fetchall()]
    
    if 'academy_id' not in lead_columns:
        issues_found.append("⚠️  Tabla 'lead' NO tiene columna 'academy_id' (puede ser opcional)")
    else:
        print_success("Tabla 'lead' tiene columna 'academy_id'")
    
    if 'created_at' not in lead_columns:
        issues_found.append("❌ Tabla 'lead' NO tiene columna 'created_at'")
    else:
        print_success("Tabla 'lead' tiene columna 'created_at'")
    
    # Resumen de problemas
    if issues_found:
        print_header("⚠️ PROBLEMAS ENCONTRADOS")
        for issue in issues_found:
            print(f"  {issue}")
        print(f"\n{Colors.YELLOW}Se necesita ejecutar migración de schema{Colors.ENDC}")
    else:
        print_header("✅ TODO EN ORDEN")
        print_success("El schema de la base de datos está completo")
    
    conn.close()
    
    return len(issues_found) == 0

if __name__ == "__main__":
    diagnose_database()