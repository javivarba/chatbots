"""
Script de Migración del Schema de Base de Datos - VERSIÓN CORREGIDA
Maneja limitaciones de SQLite con DEFAULT CURRENT_TIMESTAMP
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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def backup_database(db_path):
    """Crea un backup de la base de datos antes de migrar"""
    if not os.path.exists(db_path):
        print_error(f"Base de datos no encontrada: {db_path}")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print_success(f"Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        print_error(f"Error creando backup: {e}")
        return None

def column_exists(cursor, table, column):
    """Verifica si una columna existe en una tabla"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    return column in columns

def migrate_database(db_path='bjj_academy.db', dry_run=False):
    """Ejecuta las migraciones necesarias"""
    
    print_header("🔄 MIGRACIÓN DE SCHEMA DE BASE DE DATOS (v2)")
    
    if not os.path.exists(db_path):
        print_error(f"Base de datos no encontrada: {db_path}")
        return False
    
    if dry_run:
        print_warning("MODO DRY RUN - No se aplicarán cambios")
    else:
        # Crear backup
        backup_path = backup_database(db_path)
        if not backup_path:
            print_error("No se pudo crear backup, abortando migración")
            return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        migrations_applied = []
        migrations_skipped = []
        
        # Migración 1: Agregar created_at a conversation
        print_header("Migración 1: conversation.created_at")
        if not column_exists(cursor, 'conversation', 'created_at'):
            print_info("Agregando columna 'created_at' a tabla 'conversation'")
            if not dry_run:
                # CORRECCIÓN: Agregar columna sin DEFAULT, luego actualizar valores
                cursor.execute("""
                    ALTER TABLE conversation 
                    ADD COLUMN created_at TEXT
                """)
                
                # Actualizar registros existentes con la fecha actual
                current_time = datetime.now().isoformat()
                cursor.execute("""
                    UPDATE conversation 
                    SET created_at = ?
                    WHERE created_at IS NULL
                """, (current_time,))
                
                conn.commit()
                
                rows_updated = cursor.rowcount
                print_success(f"Columna 'created_at' agregada y {rows_updated} registros actualizados")
            else:
                print_info("Se agregaría columna 'created_at' y se actualizarían registros existentes")
            
            migrations_applied.append("conversation.created_at")
        else:
            migrations_skipped.append("conversation.created_at (ya existe)")
            print_info("Columna 'created_at' ya existe, saltando")
        
        # Migración 2: Verificar last_message_at en conversation
        print_header("Migración 2: conversation.last_message_at")
        if not column_exists(cursor, 'conversation', 'last_message_at'):
            print_info("Agregando columna 'last_message_at' a tabla 'conversation'")
            if not dry_run:
                cursor.execute("""
                    ALTER TABLE conversation 
                    ADD COLUMN last_message_at TEXT
                """)
                conn.commit()
            migrations_applied.append("conversation.last_message_at")
            print_success("Columna 'last_message_at' agregada")
        else:
            migrations_skipped.append("conversation.last_message_at (ya existe)")
            print_info("Columna 'last_message_at' ya existe, saltando")
        
        # Migración 3: Verificar academy_id en lead
        print_header("Migración 3: lead.academy_id")
        if not column_exists(cursor, 'lead', 'academy_id'):
            print_info("Agregando columna 'academy_id' a tabla 'lead'")
            if not dry_run:
                cursor.execute("""
                    ALTER TABLE lead 
                    ADD COLUMN academy_id INTEGER DEFAULT 1
                """)
                conn.commit()
            migrations_applied.append("lead.academy_id")
            print_success("Columna 'academy_id' agregada")
        else:
            migrations_skipped.append("lead.academy_id (ya existe)")
            print_info("Columna 'academy_id' ya existe, saltando")
        
        # Migración 4: Verificar created_at en lead
        print_header("Migración 4: lead.created_at")
        if not column_exists(cursor, 'lead', 'created_at'):
            print_info("Agregando columna 'created_at' a tabla 'lead'")
            if not dry_run:
                # Agregar sin DEFAULT no constante
                cursor.execute("""
                    ALTER TABLE lead 
                    ADD COLUMN created_at TEXT
                """)
                
                # Actualizar registros existentes
                current_time = datetime.now().isoformat()
                cursor.execute("""
                    UPDATE lead 
                    SET created_at = ?
                    WHERE created_at IS NULL
                """, (current_time,))
                
                conn.commit()
                rows_updated = cursor.rowcount
                print_success(f"Columna 'created_at' agregada y {rows_updated} registros actualizados")
            else:
                print_info("Se agregaría columna 'created_at' y se actualizarían registros existentes")
            
            migrations_applied.append("lead.created_at")
        else:
            migrations_skipped.append("lead.created_at (ya existe)")
            print_info("Columna 'created_at' ya existe, saltando")
        
        # Migración 5: Verificar updated_at en lead
        print_header("Migración 5: lead.updated_at")
        if not column_exists(cursor, 'lead', 'updated_at'):
            print_info("Agregando columna 'updated_at' a tabla 'lead'")
            if not dry_run:
                cursor.execute("""
                    ALTER TABLE lead 
                    ADD COLUMN updated_at TEXT
                """)
                
                # Actualizar registros existentes
                current_time = datetime.now().isoformat()
                cursor.execute("""
                    UPDATE lead 
                    SET updated_at = ?
                    WHERE updated_at IS NULL
                """, (current_time,))
                
                conn.commit()
                rows_updated = cursor.rowcount
                print_success(f"Columna 'updated_at' agregada y {rows_updated} registros actualizados")
            else:
                print_info("Se agregaría columna 'updated_at' y se actualizarían registros existentes")
            
            migrations_applied.append("lead.updated_at")
        else:
            migrations_skipped.append("lead.updated_at (ya existe)")
            print_info("Columna 'updated_at' ya existe, saltando")
        
        conn.close()
        
        # Resumen
        print_header("📊 RESUMEN DE MIGRACIÓN")
        
        if migrations_applied:
            print_success(f"Migraciones aplicadas: {len(migrations_applied)}")
            for migration in migrations_applied:
                print(f"  ✅ {migration}")
        
        if migrations_skipped:
            print_info(f"\nMigraciones saltadas: {len(migrations_skipped)}")
            for migration in migrations_skipped:
                print(f"  ℹ️  {migration}")
        
        if not migrations_applied and not migrations_skipped:
            print_warning("No se encontraron migraciones para aplicar")
        
        if not dry_run:
            print_success("\n✅ Migración completada exitosamente")
            print_info(f"Backup disponible en: {backup_path}")
        else:
            print_warning("\nMODO DRY RUN - Ningún cambio fue aplicado")
        
        return True
        
    except Exception as e:
        print_error(f"Error durante migración: {e}")
        import traceback
        print_error(f"Detalles: {traceback.format_exc()}")
        if not dry_run:
            print_warning("Si algo salió mal, restaura el backup")
        return False

if __name__ == "__main__":
    import sys
    
    # Verificar si se pasó el flag --dry-run
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print_info("Ejecutando en modo DRY RUN (sin aplicar cambios)")
    
    success = migrate_database(dry_run=dry_run)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)