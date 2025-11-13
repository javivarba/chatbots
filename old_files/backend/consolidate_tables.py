"""
Script de Consolidación de Tablas Duplicadas
Elimina tablas duplicadas de forma segura después de migrar datos
"""

import sqlite3
import os
import shutil
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

def create_backup(db_path):
    """Crea backup de la base de datos"""
    
    print_header("📦 CREANDO BACKUP")
    
    if not os.path.exists(db_path):
        print_error(f"Base de datos no encontrada: {db_path}")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.consolidation_backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print_success(f"Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        print_error(f"Error creando backup: {e}")
        return None

def table_exists(cursor, table_name):
    """Verifica si una tabla existe"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def get_table_count(cursor, table_name):
    """Obtiene el número de registros en una tabla"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    except:
        return 0

def consolidate_tables(db_path='bjj_academy.db', dry_run=False):
    """
    Consolida tablas duplicadas
    
    ESTRATEGIA:
    - academy/academies: Mantener 'academy' (singular), eliminar 'academies'
    - lead/leads: Mantener 'lead' (singular), eliminar 'leads'
    - conversation/conversations: Mantener 'conversation' (singular), eliminar 'conversations'
    - message/messages: Mantener 'message' (singular), eliminar 'messages'
    
    Las tablas singulares son las que usa la aplicación actualmente.
    """
    
    print_header("🔄 CONSOLIDACIÓN DE TABLAS DUPLICADAS")
    
    if dry_run:
        print_warning("MODO DRY RUN - No se aplicarán cambios")
    
    # Crear backup
    if not dry_run:
        backup_path = create_backup(db_path)
        if not backup_path:
            print_error("No se pudo crear backup, abortando")
            return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Definir las tablas a consolidar
    # Formato: (tabla_a_mantener, tabla_a_eliminar)
    consolidations = [
        ('academy', 'academies'),
        ('lead', 'leads'),
        ('conversation', 'conversations'),
        ('message', 'messages')
    ]
    
    results = {
        'removed': [],
        'kept': [],
        'errors': []
    }
    
    for keep_table, remove_table in consolidations:
        print_header(f"PROCESANDO: {keep_table} / {remove_table}")
        
        # Verificar si ambas existen
        keep_exists = table_exists(cursor, keep_table)
        remove_exists = table_exists(cursor, remove_table)
        
        if not remove_exists:
            print_info(f"Tabla '{remove_table}' no existe - saltando")
            continue
        
        if not keep_exists:
            print_error(f"Tabla '{keep_table}' no existe - no se puede consolidar")
            results['errors'].append(f"{keep_table} no existe")
            continue
        
        # Contar registros
        keep_count = get_table_count(cursor, keep_table)
        remove_count = get_table_count(cursor, remove_table)
        
        print_info(f"Registros en '{keep_table}': {keep_count}")
        print_info(f"Registros en '{remove_table}': {remove_count}")
        
        # Decisión de qué hacer
        if remove_count == 0:
            # Tabla vacía - eliminar directamente
            print_success(f"'{remove_table}' está vacía - se puede eliminar")
            
            if not dry_run:
                try:
                    cursor.execute(f"DROP TABLE {remove_table}")
                    conn.commit()
                    print_success(f"✅ Tabla '{remove_table}' eliminada")
                    results['removed'].append(remove_table)
                    results['kept'].append(keep_table)
                except Exception as e:
                    print_error(f"Error eliminando '{remove_table}': {e}")
                    results['errors'].append(f"{remove_table}: {str(e)}")
            else:
                print_info(f"[DRY RUN] Se eliminaría '{remove_table}'")
        
        else:
            # Tabla tiene datos - advertencia
            print_warning(f"'{remove_table}' tiene {remove_count} registros")
            print_warning("⚠️  NO SE ELIMINARÁ AUTOMÁTICAMENTE")
            print_info("Revisar manualmente si estos datos son necesarios")
            print_info(f"Comando para ver datos: SELECT * FROM {remove_table} LIMIT 10;")
            results['errors'].append(f"{remove_table} tiene datos ({remove_count} registros)")
    
    conn.close()
    
    # Resumen
    print_header("📊 RESUMEN DE CONSOLIDACIÓN")
    
    if results['removed']:
        print_success(f"Tablas eliminadas: {len(results['removed'])}")
        for table in results['removed']:
            print(f"  ✅ {table}")
    
    if results['kept']:
        print_success(f"Tablas mantenidas: {len(results['kept'])}")
        for table in results['kept']:
            print(f"  ✅ {table}")
    
    if results['errors']:
        print_warning(f"Advertencias/Errores: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  ⚠️  {error}")
    
    if not dry_run and backup_path:
        print_info(f"\n💾 Backup disponible en: {backup_path}")
    
    return len(results['errors']) == 0

def verify_application_tables(db_path='bjj_academy.db'):
    """Verifica que las tablas que usa la aplicación existan"""
    
    print_header("✅ VERIFICANDO TABLAS DE LA APLICACIÓN")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tablas que la aplicación necesita (singulares)
    required_tables = [
        'academy',
        'lead', 
        'conversation',
        'message',
        'appointment',
        'trial_week'
    ]
    
    all_good = True
    
    for table in required_tables:
        if table_exists(cursor, table):
            count = get_table_count(cursor, table)
            print_success(f"'{table}': ✅ ({count} registros)")
        else:
            print_error(f"'{table}': ❌ NO EXISTE")
            all_good = False
    
    conn.close()
    
    if all_good:
        print_success("\n✅ Todas las tablas necesarias existen")
    else:
        print_error("\n❌ Faltan tablas requeridas")
    
    return all_good

def show_duplicate_tables(db_path='bjj_academy.db'):
    """Muestra qué tablas duplicadas aún existen"""
    
    print_header("🔍 VERIFICANDO TABLAS DUPLICADAS")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    duplicates = [
        ('academy', 'academies'),
        ('lead', 'leads'),
        ('conversation', 'conversations'),
        ('message', 'messages')
    ]
    
    found_duplicates = []
    
    for singular, plural in duplicates:
        singular_exists = table_exists(cursor, singular)
        plural_exists = table_exists(cursor, plural)
        
        if singular_exists and plural_exists:
            singular_count = get_table_count(cursor, singular)
            plural_count = get_table_count(cursor, plural)
            print_warning(f"Duplicado: '{singular}' ({singular_count}) y '{plural}' ({plural_count})")
            found_duplicates.append((singular, plural))
        elif not singular_exists and plural_exists:
            print_error(f"Solo existe '{plural}' - falta '{singular}'")
        elif singular_exists and not plural_exists:
            print_success(f"Solo existe '{singular}' ✅")
    
    conn.close()
    
    if not found_duplicates:
        print_success("\n✅ No hay tablas duplicadas")
    else:
        print_warning(f"\n⚠️  Encontradas {len(found_duplicates)} tablas duplicadas")
    
    return found_duplicates

if __name__ == "__main__":
    import sys
    
    print_header("🚀 INICIANDO CONSOLIDACIÓN DE TABLAS")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar argumentos
    dry_run = '--dry-run' in sys.argv
    force = '--force' in sys.argv
    
    if dry_run:
        print_warning("Modo DRY RUN activado")
    
    # Paso 1: Mostrar estado actual
    duplicates = show_duplicate_tables()
    
    if not duplicates:
        print_success("\n✅ No hay tablas duplicadas para consolidar")
        sys.exit(0)
    
    # Paso 2: Verificar tablas de la aplicación
    print("\n")
    verify_application_tables()
    
    # Paso 3: Confirmar antes de proceder (si no es dry-run)
    if not dry_run and not force:
        print_header("⚠️  CONFIRMACIÓN")
        print_warning("Esta operación:")
        print("  • Creará un backup automático")
        print("  • Eliminará tablas duplicadas VACÍAS")
        print("  • NO eliminará tablas con datos (requiere revisión manual)")
        
        response = input(f"\n{Colors.YELLOW}¿Continuar? (sí/no): {Colors.ENDC}")
        if response.lower() not in ['si', 'sí', 'yes', 'y', 's']:
            print_info("Operación cancelada")
            sys.exit(0)
    
    # Paso 4: Ejecutar consolidación
    print("\n")
    success = consolidate_tables(dry_run=dry_run)
    
    # Paso 5: Verificar resultado
    print("\n")
    show_duplicate_tables()
    
    print("\n")
    verify_application_tables()
    
    # Resultado final
    if success:
        print_header("✅ CONSOLIDACIÓN COMPLETADA")
        if not dry_run:
            print_success("Base de datos consolidada exitosamente")
        else:
            print_info("Revisión completada (DRY RUN)")
    else:
        print_header("⚠️  CONSOLIDACIÓN CON ADVERTENCIAS")
        print_warning("Algunas tablas requieren revisión manual")
    
    sys.exit(0 if success else 1)