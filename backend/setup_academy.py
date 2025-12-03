"""
Script para crear la Academy en la base de datos
Uso: python setup_academy.py
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
from app.models import Academy


def setup_academy():
    """Crear Academy BJJ Mingo en la base de datos"""

    app = create_app()

    with app.app_context():
        # Verificar si ya existe una academy
        existing_academy = Academy.query.first()

        if existing_academy:
            print("Ya existe una Academy configurada:")
            print(f"  Nombre: {existing_academy.name}")
            print(f"  Telefono: {existing_academy.phone}")
            print(f"  Email: {existing_academy.email}")
            print(f"  ID: {existing_academy.id}")
            print()

            response = input("Deseas actualizarla? (s/n): ")
            if response.lower() != 's':
                print("Operacion cancelada.")
                return False

            # Actualizar existente
            academy = existing_academy
            print("\nActualizando Academy existente...")
        else:
            # Crear nueva
            academy = Academy()
            print("Creando nueva Academy...")

        # Configurar datos de BJJ Mingo
        academy.name = "BJJ Mingo"
        academy.slug = "bjj-mingo"  # Slug requerido
        academy.phone = "+506-7015-0369"
        academy.email = "info@bjjmingo.com"
        academy.address_city = "San Jose"
        academy.address_country = "Costa Rica"
        academy.timezone = "America/Costa_Rica"
        academy.schedule = {
            "lunes": "06:00-21:00",
            "martes": "06:00-21:00",
            "miercoles": "06:00-21:00",
            "jueves": "06:00-21:00",
            "viernes": "06:00-21:00",
            "sabado": "08:00-12:00"
        }
        academy.pricing_info = {
            "trial_week": "Gratis",
            "monthly": "Consultar",
            "classes_per_week": "Ilimitadas"
        }
        academy.about = """BJJ Mingo es una academia de Brazilian Jiu-Jitsu en San Jose, Costa Rica.
Ofrecemos clases para todos los niveles, desde principiantes hasta avanzados.
Primera semana de prueba GRATIS."""

        if not existing_academy:
            db.session.add(academy)

        db.session.commit()

        print("=" * 70)
        print("ACADEMY CONFIGURADA EXITOSAMENTE")
        print("=" * 70)
        print(f"ID: {academy.id}")
        print(f"Nombre: {academy.name}")
        print(f"Telefono: {academy.phone}")
        print(f"Email: {academy.email}")
        print(f"Ciudad: {academy.address_city}")
        print(f"Pais: {academy.address_country}")
        print()
        print("Horarios:")
        for dia, horario in academy.schedule.items():
            print(f"  {dia.capitalize()}: {horario}")
        print()
        print("Ahora puedes procesar mensajes de WhatsApp!")
        print()

        return True


if __name__ == '__main__':
    try:
        success = setup_academy()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
