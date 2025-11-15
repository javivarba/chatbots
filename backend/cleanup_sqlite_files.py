"""
Script para eliminar archivos SQLite obsoletos después de la migración a PostgreSQL
"""

import os
import shutil

def main():
    print("\n" + "="*70)
    print("  LIMPIEZA DE ARCHIVOS SQLITE OBSOLETOS")
    print("="*70)

    # Archivos y directorios a eliminar
    files_to_delete = [
        # Archivos .db SQLite
        'bjj_academy.db',
        'instance/bjj_academy.db',
        '../bjj_academy.db',
        '../old_files/bjj_academy.db',
        '../old_files/bjj_academy_test.db',
    ]

    # Archivos de utilidades SQLite obsoletos (DEPRECATED pero no eliminamos aún)
    deprecated_utils = [
        'app/utils/database.py',  # Mantener por si acaso, pero marcar como deprecated
    ]

    deleted_count = 0
    not_found_count = 0

    print("\n[1] Eliminando archivos .db SQLite...")

    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"  [OK] Eliminado: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"  [ERROR] No se pudo eliminar {file_path}: {e}")
        else:
            print(f"  [SKIP] No existe: {file_path}")
            not_found_count += 1

    print(f"\n[2] Archivos deprecados (NO eliminados, solo FYI)...")
    for util_file in deprecated_utils:
        if os.path.exists(util_file):
            print(f"  [DEPRECATED] {util_file}")
            print(f"               Este archivo ya no se usa pero se mantiene por compatibilidad")

    # Resumen
    print("\n" + "="*70)
    print("  RESUMEN DE LIMPIEZA")
    print("="*70)
    print(f"\n  Archivos eliminados: {deleted_count}")
    print(f"  Archivos no encontrados: {not_found_count}")
    print(f"\n  Base de datos activa: PostgreSQL")
    print(f"  Archivos SQLite: ELIMINADOS")
    print(f"  Utilidades SQLite: DEPRECATED (mantenidas por compatibilidad)")
    print("\n  NOTA: Si algo falla, podes restaurar de Git")
    print("="*70 + "\n")

if __name__ == '__main__':
    response = input("\nEstas seguro de que queres eliminar los archivos SQLite? (si/no): ")
    if response.lower() in ['si', 's', 'yes', 'y']:
        main()
    else:
        print("\nOperacion cancelada.")
