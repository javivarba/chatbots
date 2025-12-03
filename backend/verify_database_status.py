"""
Script para verificar el estado actual de la base de datos
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Academy, Lead, Conversation, Message, ClassReminder, TeamMember
from colorama import Fore, Style, init

init(autoreset=True)

def print_header(title):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{title}")
    print(f"{'='*60}{Style.RESET_ALL}\n")


def verify_database():
    """Verifica el estado actual de la base de datos"""
    print_header("ESTADO ACTUAL DE LA BASE DE DATOS")

    app = create_app()

    with app.app_context():
        # Conteo de registros
        counts = {
            'Academies': Academy.query.count(),
            'Leads': Lead.query.count(),
            'Conversations': Conversation.query.count(),
            'Messages': Message.query.count(),
            'ClassReminders': ClassReminder.query.count(),
            'TeamMembers': TeamMember.query.count(),
        }

        total = sum(counts.values())

        print(f"{Fore.YELLOW}TABLAS:{Style.RESET_ALL}\n")

        for table, count in counts.items():
            if count > 0:
                color = Fore.GREEN
                status = "✓"
            else:
                color = Fore.WHITE
                status = "○"

            print(f"  {color}{status} {table:20} {count:>5} registros{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}TOTAL:{' '*20} {total:>5} registros{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─'*60}{Style.RESET_ALL}\n")

        # Mostrar detalles de Academy si existe
        if counts['Academies'] > 0:
            print_header("ACADEMIAS REGISTRADAS")
            academies = Academy.query.all()
            for academy in academies:
                print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {academy.name}")
                print(f"    - Slug: {academy.slug}")
                print(f"    - Email: {academy.email}")
                print(f"    - Phone: {academy.phone}")
                print(f"    - Trial enabled: {'Sí' if academy.trial_class_enabled else 'No'}")
                print()

        # Status general
        if total == 0:
            print(f"{Fore.GREEN}{'='*60}")
            print("✓ BASE DE DATOS VACÍA")
            print(f"{'='*60}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}La base de datos está lista para testing manual.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Todos los mensajes de WhatsApp crearán nuevos registros.{Style.RESET_ALL}\n")
        elif counts['Leads'] == 0 and counts['Conversations'] == 0 and counts['Messages'] == 0:
            print(f"{Fore.GREEN}{'='*60}")
            print("✓ BASE DE DATOS LISTA PARA TESTING")
            print(f"{'='*60}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}No hay leads, conversaciones ni mensajes.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}La base de datos está lista para testing manual.{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.YELLOW}{'='*60}")
            print(f"⚠ BASE DE DATOS CONTIENE {total} REGISTROS")
            print(f"{'='*60}{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}Si querés resetear, ejecutá: python reset_database.py{Style.RESET_ALL}\n")


if __name__ == '__main__':
    verify_database()
