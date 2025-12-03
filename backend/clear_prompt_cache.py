"""
Script para limpiar el caché del system prompt
Ejecutar después de actualizar academy_info.py
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from app import create_app
from app.services.cache_service import cache

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("LIMPIANDO CACHÉ DEL SYSTEM PROMPT")
    print("="*60)

    # Limpiar el caché del system prompt
    try:
        # CORREGIDO: Usar la clave correcta "ai:system_prompt"
        result = cache.delete('ai:system_prompt')
        if result:
            print("✅ Caché del system prompt eliminado exitosamente")
        else:
            print("⚠️ No había caché de system prompt para eliminar")

        # Limpiar también todas las respuestas de AI cacheadas
        ai_responses_deleted = cache.delete_pattern('ai:response:*')
        if ai_responses_deleted > 0:
            print(f"✅ {ai_responses_deleted} respuestas de AI eliminadas del caché")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("="*60)
    print("El próximo mensaje usará el prompt actualizado")
    print("="*60 + "\n")
