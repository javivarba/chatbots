"""
Script para diagnosticar problemas con archivo .env
"""

import os
from pathlib import Path

def diagnose_env_file():
    print("🔍 DIAGNÓSTICO ARCHIVO .env")
    print("=" * 50)
    
    # 1. Verificar directorio actual
    current_dir = os.getcwd()
    print(f"📁 Directorio actual: {current_dir}")
    
    # 2. Buscar archivos .env
    possible_env_files = [
        ".env",
        "../.env", 
        "backend/.env",
        "../backend/.env"
    ]
    
    found_env_files = []
    for env_file in possible_env_files:
        if os.path.exists(env_file):
            found_env_files.append(os.path.abspath(env_file))
    
    print(f"\n📄 Archivos .env encontrados:")
    for env_file in found_env_files:
        print(f"   ✅ {env_file}")
    
    if not found_env_files:
        print("   ❌ No se encontró ningún archivo .env")
        return False
    
    # 3. Leer contenido de cada archivo .env
    for env_file in found_env_files:
        print(f"\n📖 Contenido de {env_file}:")
        print("-" * 40)
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith('OPENAI_API_KEY'):
                    # Mostrar solo parte de la key por seguridad
                    if '=' in line:
                        key_part = line.split('=', 1)[1].strip()
                        if key_part and key_part != 'sk-your-openai-api-key-here':
                            print(f"   Línea {i}: OPENAI_API_KEY={key_part[:15]}... ✅")
                        else:
                            print(f"   Línea {i}: OPENAI_API_KEY=<vacía o default> ❌")
                    else:
                        print(f"   Línea {i}: {line} ❌ (formato incorrecto)")
                elif line.startswith('TWILIO_'):
                    print(f"   Línea {i}: {line[:25]}... ✅")
                elif line and not line.startswith('#'):
                    print(f"   Línea {i}: {line}")
                    
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
    
    return True

def test_env_loading():
    print("\n🔧 PROBANDO CARGA DE VARIABLES")
    print("=" * 50)
    
    # Método 1: Sin python-dotenv
    print("1. Variables de entorno del sistema:")
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"   ✅ OPENAI_API_KEY: {openai_key[:15]}...")
    else:
        print("   ❌ OPENAI_API_KEY: No encontrada")
    
    # Método 2: Con python-dotenv
    try:
        from dotenv import load_dotenv
        
        # Intentar cargar desde diferentes ubicaciones
        env_files = ['.env', '../.env', 'backend/.env']
        
        for env_file in env_files:
            if os.path.exists(env_file):
                print(f"\n2. Cargando desde {env_file}:")
                load_dotenv(env_file, override=True)
                
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key and openai_key != 'sk-your-openai-api-key-here':
                    print(f"   ✅ OPENAI_API_KEY cargada: {openai_key[:15]}...")
                    return True
                else:
                    print(f"   ❌ OPENAI_API_KEY no válida")
                    
    except ImportError:
        print("   ❌ python-dotenv no instalado")
        print("   Instala con: pip install python-dotenv")
    
    return False

def test_manual_loading():
    print("\n🔧 CARGA MANUAL DEL ARCHIVO .env")
    print("=" * 50)
    
    # Buscar archivo .env
    env_paths = ['.env', '../.env', 'backend/.env']
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            print(f"📄 Cargando manualmente: {env_path}")
            
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Saltar comentarios y líneas vacías
                        if not line or line.startswith('#'):
                            continue
                            
                        # Parsear variable
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            
                            # Establecer variable de entorno
                            os.environ[key] = value
                            
                            if key == 'OPENAI_API_KEY':
                                print(f"   ✅ {key} establecida: {value[:15]}...")
                            else:
                                print(f"   ✅ {key} establecida")
                        else:
                            print(f"   ⚠ Línea {line_num} mal formateada: {line}")
                
                # Verificar que se cargó
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key:
                    print(f"\n🎉 SUCCESS: OPENAI_API_KEY disponible: {openai_key[:15]}...")
                    return True
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    return False

def create_proper_env():
    print("\n🔧 CREAR ARCHIVO .env CORRECTO")
    print("=" * 50)
    
    # Pedir la API key
    api_key = input("Pega tu OpenAI API Key (sk-...): ").strip()
    
    if not api_key.startswith('sk-'):
        print("❌ API Key debe empezar con 'sk-'")
        return False
    
    # Crear contenido .env
    env_content = f"""# BJJ Academy Bot - Environment Variables
FLASK_ENV=development
FLASK_DEBUG=True

# OpenAI Configuration
OPENAI_API_KEY={api_key}
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_NUMBER=+14155238886

# Database
DATABASE_URL=sqlite:///bjj_academy.db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
"""
    
    # Escribir archivo
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ Archivo .env creado en: {os.path.abspath('.env')}")
        
        # Verificar carga
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        test_key = os.getenv('OPENAI_API_KEY')
        if test_key == api_key:
            print("✅ API Key cargada correctamente")
            return True
        else:
            print("❌ Problema cargando API Key")
            
    except Exception as e:
        print(f"❌ Error creando .env: {e}")
    
    return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO COMPLETO - ARCHIVO .env")
    print("=" * 60)
    
    # 1. Diagnosticar archivos existentes
    diagnose_env_file()
    
    # 2. Probar carga
    loaded = test_env_loading()
    
    if not loaded:
        # 3. Intentar carga manual
        loaded = test_manual_loading()
    
    if not loaded:
        # 4. Crear nuevo archivo
        print("\n❌ No se pudo cargar .env existente")
        choice = input("\n¿Crear nuevo archivo .env? (y/n): ")
        if choice.lower() == 'y':
            create_proper_env()
    
    print("\n" + "="*60)
    print("🎯 SIGUIENTE PASO:")
    print("1. Asegúrate de ejecutar desde el directorio 'backend'")
    print("2. Reinicia Flask después de cualquier cambio")
    print("3. Ejecuta: python openai_debug_script.py")