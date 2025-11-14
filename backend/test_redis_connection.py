"""
Script de Test Rápido para Verificar Conexión a Redis Cloud
Ejecutar: python test_redis_connection.py
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(override=True)

def test_redis_connection():
    """Prueba la conexión a Redis Cloud"""
    print("\n" + "="*60)
    print("TEST DE CONEXIÓN A REDIS CLOUD")
    print("="*60)

    # Verificar que las variables existen
    print("\n[1/4] Verificando variables de entorno...")

    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT')
    redis_password = os.getenv('REDIS_PASSWORD')
    celery_broker = os.getenv('CELERY_BROKER_URL')

    if not celery_broker:
        print("❌ ERROR: CELERY_BROKER_URL no configurada en .env")
        print("\nAgrega a tu .env:")
        print("CELERY_BROKER_URL=redis://default:tu_password@tu-host:tu-port/0")
        return False

    print(f"✅ Variables encontradas:")
    if redis_host:
        print(f"   Host: {redis_host}")
    if redis_port:
        print(f"   Port: {redis_port}")
    if redis_password:
        print(f"   Password: {'*' * len(redis_password[:10])}...")
    print(f"   Broker URL: {celery_broker[:30]}...")

    # Intentar importar redis
    print("\n[2/4] Verificando librería redis...")
    try:
        import redis
        print("✅ Librería redis instalada")
    except ImportError:
        print("❌ ERROR: Librería redis no instalada")
        print("\nInstalar con: pip install redis")
        return False

    # Intentar conectar
    print("\n[3/4] Intentando conectar a Redis Cloud...")
    try:
        r = redis.from_url(celery_broker)
        print(f"   Conectando a: {celery_broker.split('@')[1].split('/')[0] if '@' in celery_broker else 'localhost'}")

        # Hacer ping
        response = r.ping()

        if response:
            print("✅ CONEXIÓN EXITOSA!")
            print("   Respuesta: PONG")
        else:
            print("❌ Redis no respondió correctamente")
            return False

    except redis.exceptions.ConnectionError as e:
        print(f"❌ ERROR DE CONEXIÓN: {e}")
        print("\nPosibles causas:")
        print("1. Endpoint incorrecto en .env")
        print("2. Password incorrecto")
        print("3. Firewall bloqueando la conexión")
        print("4. IP no whitelisted en Redis Cloud")
        print("\nSolución:")
        print("- Ve a Redis Cloud → Database → Security → Source IP/Subnet")
        print("- Agrega tu IP o 0.0.0.0/0 (solo desarrollo)")
        return False

    except redis.exceptions.AuthenticationError as e:
        print(f"❌ ERROR DE AUTENTICACIÓN: {e}")
        print("\nPosibles causas:")
        print("1. Password incorrecto en .env")
        print("2. Username incorrecto (prueba con 'default' o vacío)")
        print("\nVerifica el password en:")
        print("https://cloud.redis.io → Database → Configuration → Default user password")
        return False

    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Probar operaciones básicas
    print("\n[4/4] Probando operaciones básicas...")
    try:
        # Set
        test_key = 'bjj_mingo_test'
        test_value = 'Sistema de recordatorios funcionando!'
        r.set(test_key, test_value, ex=60)  # Expira en 60 segundos
        print(f"✅ SET: {test_key} = {test_value}")

        # Get
        retrieved = r.get(test_key)
        if retrieved:
            print(f"✅ GET: {test_key} = {retrieved.decode('utf-8')}")

        # Delete
        r.delete(test_key)
        print(f"✅ DEL: {test_key} eliminado")

        # Info
        info = r.info('server')
        redis_version = info.get('redis_version', 'unknown')
        print(f"✅ Redis Version: {redis_version}")

    except Exception as e:
        print(f"⚠️  Advertencia en operaciones básicas: {e}")

    # Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print("✅ Redis Cloud está configurado correctamente!")
    print("\nPróximos pasos:")
    print("1. Ejecutar: python test_reminders_system.py")
    print("2. Iniciar Celery Worker: start_celery_worker.bat")
    print("3. Iniciar Celery Beat: start_celery_beat.bat")
    print("="*60 + "\n")

    return True


def show_redis_info():
    """Muestra información detallada de Redis"""
    try:
        import redis
        from dotenv import load_dotenv

        load_dotenv(override=True)
        celery_broker = os.getenv('CELERY_BROKER_URL')

        r = redis.from_url(celery_broker)

        print("\n" + "="*60)
        print("INFORMACIÓN DE REDIS CLOUD")
        print("="*60)

        info = r.info()

        print(f"\nServidor:")
        print(f"  Redis Version: {info.get('redis_version', 'N/A')}")
        print(f"  OS: {info.get('os', 'N/A')}")
        print(f"  Uptime: {info.get('uptime_in_days', 'N/A')} días")

        print(f"\nMemoria:")
        used_memory = info.get('used_memory_human', 'N/A')
        max_memory = info.get('maxmemory_human', 'N/A')
        print(f"  Usado: {used_memory}")
        print(f"  Máximo: {max_memory}")

        print(f"\nEstadísticas:")
        print(f"  Clientes conectados: {info.get('connected_clients', 'N/A')}")
        print(f"  Total keys: {r.dbsize()}")
        print(f"  Comandos procesados: {info.get('total_commands_processed', 'N/A')}")

        print("\n" + "="*60 + "\n")

    except Exception as e:
        print(f"No se pudo obtener info detallada: {e}")


if __name__ == '__main__':
    success = test_redis_connection()

    if success:
        # Mostrar info adicional si la conexión fue exitosa
        try:
            show_redis_info()
        except:
            pass

        sys.exit(0)
    else:
        print("\n❌ La conexión a Redis Cloud falló.")
        print("Revisa los pasos en: REDIS_CLOUD_SETUP.md\n")
        sys.exit(1)
