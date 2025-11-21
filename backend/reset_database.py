"""
Script para resetear la base de datos de testing
ADVERTENCIA: Esto borrará TODOS los datos de testing
Solo usar en desarrollo/testing, NUNCA en producción
"""

import sys
import os
from colorama import init, Fore, Style

# Inicializar colorama para colores en Windows
init()

def confirm_reset():
    """Confirmar que el usuario quiere borrar los datos"""
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.RED}ADVERTENCIA: RESETEO DE BASE DE DATOS{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")

    print("Este script borrara TODOS los datos de:")
    print(f"{Fore.CYAN}  - Leads{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  - Conversaciones{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  - Mensajes{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  - Recordatorios (ClassReminder){Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}CONSERVARA:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  - Informacion de la Academia{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  - Configuracion de horarios{Style.RESET_ALL}")

    # Verificar si estamos en producción
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        print(f"\n{Fore.RED}ERROR: Estas en modo PRODUCCION{Style.RESET_ALL}")
        print("Este script solo debe ejecutarse en desarrollo/testing")
        sys.exit(1)

    print(f"\n{Fore.YELLOW}Entorno actual: {env}{Style.RESET_ALL}")

    response = input(f"\n{Fore.YELLOW}Estas seguro de que queres borrar TODOS los datos? (si/no): {Style.RESET_ALL}")

    if response.lower() not in ['si', 'yes', 's', 'y']:
        print(f"\n{Fore.GREEN}Operacion cancelada. No se borraron datos.{Style.RESET_ALL}")
        sys.exit(0)

    # Segunda confirmación
    response2 = input(f"\n{Fore.RED}Confirma nuevamente escribiendo 'BORRAR': {Style.RESET_ALL}")

    if response2 != 'BORRAR':
        print(f"\n{Fore.GREEN}Operacion cancelada. No se borraron datos.{Style.RESET_ALL}")
        sys.exit(0)

def reset_database():
    """Borrar todos los datos de testing manteniendo la estructura"""
    from app import create_app, db
    from app.models import Lead, Conversation, Message, ClassReminder

    app = create_app()

    with app.app_context():
        try:
            print(f"\n{Fore.CYAN}Conteo antes del borrado:{Style.RESET_ALL}")

            # Contar registros antes
            leads_count = Lead.query.count()
            conversations_count = Conversation.query.count()
            messages_count = Message.query.count()
            reminders_count = ClassReminder.query.count()

            print(f"  - Leads: {leads_count}")
            print(f"  - Conversaciones: {conversations_count}")
            print(f"  - Mensajes: {messages_count}")
            print(f"  - Recordatorios: {reminders_count}")

            total = leads_count + conversations_count + messages_count + reminders_count
            print(f"\n  {Fore.YELLOW}TOTAL: {total} registros{Style.RESET_ALL}")

            if total == 0:
                print(f"\n{Fore.GREEN}La base de datos ya esta vacia.{Style.RESET_ALL}")
                return

            print(f"\n{Fore.CYAN}Borrando datos...{Style.RESET_ALL}")

            # Borrar en orden (respetando foreign keys)
            # 1. Recordatorios (dependen de Leads)
            if reminders_count > 0:
                ClassReminder.query.delete()
                print(f"  > {reminders_count} recordatorios borrados")

            # 2. Mensajes (dependen de Conversations)
            if messages_count > 0:
                Message.query.delete()
                print(f"  > {messages_count} mensajes borrados")

            # 3. Conversaciones (dependen de Leads)
            if conversations_count > 0:
                Conversation.query.delete()
                print(f"  > {conversations_count} conversaciones borradas")

            # 4. Leads (tabla principal)
            if leads_count > 0:
                Lead.query.delete()
                print(f"  > {leads_count} leads borrados")

            # Commit de todos los cambios
            db.session.commit()

            print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Base de datos reseteada exitosamente{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")

            print(f"\n{Fore.CYAN}La base de datos esta limpia y lista para nuevos datos.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Los proximos mensajes de WhatsApp crearan nuevos registros.{Style.RESET_ALL}\n")

        except Exception as e:
            db.session.rollback()
            print(f"\n{Fore.RED}ERROR durante el borrado:{Style.RESET_ALL}")
            print(f"{Fore.RED}{str(e)}{Style.RESET_ALL}")
            sys.exit(1)

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}Script de Reseteo de Base de Datos{Style.RESET_ALL}")
    print(f"{Fore.CYAN}BJJ Academy Bot - Version de Desarrollo{Style.RESET_ALL}")

    # Confirmar con el usuario
    confirm_reset()

    # Ejecutar el reseteo
    reset_database()
