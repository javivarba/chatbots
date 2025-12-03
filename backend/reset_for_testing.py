"""
Script para Resetear DB y Caché para Testing desde Cero
Limpia toda la data de testing y deja el sistema listo para pruebas
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import logging
from datetime import datetime
from app import create_app, db
from app.models import Lead, Message, ClassReminder, Academy, Conversation
from app.services.cache_service import cache

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def reset_database():
    """Limpia todas las tablas de la base de datos"""

    print("\n" + "="*70)
    print("🗑️  LIMPIANDO BASE DE DATOS")
    print("="*70)

    try:
        # Contar registros antes de eliminar
        leads_count = Lead.query.count()
        messages_count = Message.query.count()
        reminders_count = ClassReminder.query.count()
        conversations_count = Conversation.query.count()

        print(f"\n📊 Registros actuales:")
        print(f"   • Leads: {leads_count}")
        print(f"   • Messages: {messages_count}")
        print(f"   • ClassReminders: {reminders_count}")
        print(f"   • Conversations: {conversations_count}")

        if leads_count + messages_count + reminders_count + conversations_count == 0:
            print("\nℹ️  Base de datos ya está vacía")
            return

        print(f"\n⚠️  ADVERTENCIA: Se eliminarán TODOS los registros")
        response = input("¿Continuar? (yes/no): ")

        if response.lower() != 'yes':
            print("❌ Operación cancelada")
            return

        print("\n🗑️  Eliminando registros...")

        # Eliminar en orden (para respetar foreign keys)

        # 1. ClassReminders (depende de Lead)
        deleted_reminders = ClassReminder.query.delete()
        print(f"   ✅ ClassReminders eliminados: {deleted_reminders}")

        # 2. Messages (depende de Conversation)
        deleted_messages = Message.query.delete()
        print(f"   ✅ Messages eliminados: {deleted_messages}")

        # 3. Conversations (depende de Lead)
        deleted_conversations = Conversation.query.delete()
        print(f"   ✅ Conversations eliminados: {deleted_conversations}")

        # 4. Leads (depende de Academy)
        deleted_leads = Lead.query.delete()
        print(f"   ✅ Leads eliminados: {deleted_leads}")

        # Commit cambios
        db.session.commit()

        print("\n✅ Base de datos limpiada exitosamente")

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Error limpiando base de datos: {e}")
        import traceback
        traceback.print_exc()


def reset_cache():
    """Limpia todo el caché de Redis"""

    print("\n" + "="*70)
    print("🗑️  LIMPIANDO CACHÉ DE REDIS")
    print("="*70)

    try:
        # Obtener todas las keys del caché
        print("\n🔍 Buscando keys en Redis...")

        # Limpiar caché de system prompt
        system_prompt_deleted = cache.delete('ai:system_prompt')
        print(f"   {'✅' if system_prompt_deleted else 'ℹ️ '} System prompt: {'eliminado' if system_prompt_deleted else 'no existía'}")

        # Limpiar todas las respuestas de AI cacheadas usando delete_pattern
        # El patron de keys de respuestas AI es: ai:response:{hash}
        try:
            ai_responses_deleted = cache.delete_pattern('ai:response:*')
            if ai_responses_deleted > 0:
                print(f"   ✅ AI response cache eliminado: {ai_responses_deleted} keys")
            else:
                print(f"   ℹ️  No habia respuestas de AI en cache")
        except Exception as e:
            print(f"   ℹ️  No se pudo limpiar cache de AI responses: {e}")
            print(f"   ℹ️  System prompt limpiado correctamente (suficiente para testing)")

        print("\n✅ Caché limpiado exitosamente")

    except Exception as e:
        logger.error(f"❌ Error limpiando caché: {e}")
        import traceback
        traceback.print_exc()


def verify_academy():
    """Verifica que existe al menos una academy en la BD"""

    print("\n" + "="*70)
    print("🏫 VERIFICANDO ACADEMY")
    print("="*70)

    try:
        academies = Academy.query.all()

        if len(academies) == 0:
            print("\n⚠️  ADVERTENCIA: No hay academies en la base de datos")
            print("   Para testing necesitas crear una academy primero")
            print("\n   Contacta al administrador para crear una academy")
        else:
            print(f"\n✅ Academies existentes: {len(academies)}")
            for academy in academies:
                location = academy.address_city if academy.address_city else 'Sin ubicación'
                print(f"   • ID: {academy.id} - {academy.name} ({location})")

    except Exception as e:
        logger.error(f"❌ Error verificando academies: {e}")


def show_summary():
    """Muestra resumen del estado actual"""

    print("\n" + "="*70)
    print("📊 ESTADO ACTUAL DE LA BASE DE DATOS")
    print("="*70)

    try:
        leads_count = Lead.query.count()
        messages_count = Message.query.count()
        reminders_count = ClassReminder.query.count()
        conversations_count = Conversation.query.count()
        academies_count = Academy.query.count()

        print(f"\n   • Academies: {academies_count}")
        print(f"   • Leads: {leads_count}")
        print(f"   • Messages: {messages_count}")
        print(f"   • ClassReminders: {reminders_count}")
        print(f"   • Conversations: {conversations_count}")

        if leads_count + messages_count + reminders_count + conversations_count == 0:
            print("\n✅ Sistema listo para testing desde cero")
        else:
            print("\n⚠️  Aún hay registros en la base de datos")

    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen: {e}")


def main():
    """Función principal"""

    print("\n" + "="*70)
    print("🔄 RESET COMPLETO PARA TESTING")
    print("="*70)
    print("\nEste script limpiará:")
    print("  1. Todos los Leads, Messages, ClassReminders y Conversations")
    print("  2. Caché de Redis (system prompt y AI responses)")
    print("\nNOTA: Las Academies NO se eliminarán (se necesitan para testing)")

    app = create_app()

    with app.app_context():
        # 1. Verificar academy
        verify_academy()

        # 2. Limpiar base de datos
        reset_database()

        # 3. Limpiar caché
        reset_cache()

        # 4. Mostrar resumen
        show_summary()

        print("\n" + "="*70)
        print("✅ RESET COMPLETADO")
        print("="*70)
        print("\n🚀 Ahora puedes ejecutar:")
        print("   • python test_complete_flow.py")
        print("   • python test_problema_original.py")
        print("   • O iniciar el chatbot para testing manual\n")


if __name__ == '__main__':
    main()
