"""
Script para verificar que todas las dependencias están instaladas correctamente
Versión corregida para la estructura actual del proyecto
"""

import sys
import os

def check_import(module_name, package_name=None):
    """Verifica si un módulo se puede importar"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {package_name} instalado correctamente")
        return True
    except ImportError as e:
        print(f"❌ {package_name} NO instalado: {e}")
        return False

def main():
    print("=" * 50)
    print("Verificando instalación de dependencias")
    print("=" * 50)
    
    dependencies = [
        ("flask", "Flask"),
        ("flask_sqlalchemy", "Flask-SQLAlchemy"),
        ("flask_migrate", "Flask-Migrate"),
        ("flask_cors", "Flask-CORS"),
        ("dotenv", "python-dotenv"),
        ("psycopg2", "psycopg2-binary"),
        ("redis", "Redis"),
        ("celery", "Celery"),
        ("openai", "OpenAI"),
        ("twilio", "Twilio"),
        ("requests", "Requests"),
        ("pytest", "Pytest"),
    ]
    
    all_installed = True
    
    for module, package in dependencies:
        if not check_import(module, package):
            all_installed = False
    
    print("=" * 50)
    
    if all_installed:
        print("✅ Todas las dependencias están instaladas!")
        
        # Verificar versiones
        print("\nVersiones instaladas:")
        print("-" * 30)
        
        import flask
        from importlib.metadata import version
        print(f"Flask: {version('flask')}")
        
        import sqlalchemy
        print(f"SQLAlchemy: {sqlalchemy.__version__}")
        
        import celery
        print(f"Celery: {celery.__version__}")
        
        import openai
        print(f"OpenAI: {openai.__version__}")
        
    else:
        print("❌ Faltan dependencias por instalar")
        print("\nEjecuta:")
        print("pip install flask flask-sqlalchemy flask-migrate flask-cors")
        print("pip install python-dotenv psycopg2-binary redis celery")
        print("pip install openai twilio requests pytest")
    
    # Obtener el directorio actual del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"\nDirectorio del script: {script_dir}")
    
    # Verificar estructura de directorios
    print("\n" + "=" * 50)
    print("Verificando estructura de directorios")
    print("=" * 50)
    
    # Las rutas son relativas al directorio donde está el script
    required_dirs = [
        "backend",
        "backend/app",
        "backend/app/api",
        "backend/app/models",
        "backend/app/services",
        "backend/tests",
    ]
    
    for dir_path in required_dirs:
        # Construir la ruta completa
        full_path = os.path.join(script_dir, dir_path)
        if os.path.exists(full_path):
            print(f"✅ {dir_path} existe")
        else:
            print(f"❌ {dir_path} NO existe en {full_path}")
    
    # Verificar archivos importantes
    print("\n" + "=" * 50)
    print("Verificando archivos de configuración")
    print("=" * 50)
    
    required_files = [
        "backend/app/__init__.py",
        "backend/app/config.py",
        "backend/.env.example",
        "backend/.env",
        "backend/run.py",
        "docker-compose.yml",
    ]
    
    for file_path in required_files:
        # Construir la ruta completa
        full_path = os.path.join(script_dir, file_path)
        if os.path.exists(full_path):
            # Verificar si el archivo tiene contenido
            size = os.path.getsize(full_path)
            if size > 0:
                print(f"✅ {file_path} existe ({size} bytes)")
            else:
                print(f"⚠️  {file_path} existe pero está vacío")
        else:
            print(f"❌ {file_path} NO existe")
    
    # Verificar si podemos importar la aplicación
    print("\n" + "=" * 50)
    print("Verificando importación de la aplicación")
    print("=" * 50)
    
    # Añadir el directorio backend al path para poder importar
    backend_path = os.path.join(script_dir, 'backend')
    if os.path.exists(backend_path):
        sys.path.insert(0, backend_path)
        try:
            from app import create_app
            print("✅ La aplicación se puede importar correctamente")
            
            # Intentar crear la app
            app = create_app('default')
            print("✅ La aplicación se puede crear correctamente")
            
        except ImportError as e:
            print(f"❌ Error al importar la aplicación: {e}")
        except Exception as e:
            print(f"❌ Error al crear la aplicación: {e}")
    else:
        print(f"❌ No se encuentra el directorio backend en {backend_path}")

if __name__ == "__main__":
    main()