"""
Test rapido de configuracion de Celery
Verifica que Redis Cloud este accesible con la nueva configuracion
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

print("\n" + "="*60)
print("TEST DE CONFIGURACION CELERY")
print("="*60)

# Mostrar configuracion
broker_url = os.getenv('CELERY_BROKER_URL', 'No configurado')
backend_url = os.getenv('CELERY_RESULT_BACKEND', 'No configurado')

print("\nConfiguracion actual:")
print(f"BROKER:  {broker_url}")
print(f"BACKEND: {backend_url}")

# Extraer el numero de DB de las URLs
if broker_url != 'No configurado':
    broker_db = broker_url.split('/')[-1]
    print(f"\nBase de datos BROKER: /{broker_db}")

if backend_url != 'No configurado':
    backend_db = backend_url.split('/')[-1]
    print(f"Base de datos BACKEND: /{backend_db}")

# Verificar que ambos usen DB 0
if broker_db == '0' and backend_db == '0':
    print("\nOK: Ambos usan DB 0 (compatible con Redis Cloud Free)")
elif broker_db == backend_db:
    print(f"\nADVERTENCIA: Ambos usan DB {broker_db}, pueden colisionar datos")
else:
    print(f"\nERROR: Broker usa DB {broker_db}, Backend usa DB {backend_db}")
    print("Redis Cloud Free solo permite DB 0!")

# Intentar conectar
print("\n" + "="*60)
print("Intentando conectar a Redis...")
print("="*60)

try:
    import redis

    # Probar broker
    print("\n[1/2] Probando BROKER...")
    r_broker = redis.from_url(broker_url)
    r_broker.ping()
    print("  OK: BROKER conectado")

    # Probar backend
    print("\n[2/2] Probando BACKEND...")
    r_backend = redis.from_url(backend_url)
    r_backend.ping()
    print("  OK: BACKEND conectado")

    print("\n" + "="*60)
    print("EXITO: Celery puede conectarse a Redis Cloud")
    print("="*60)
    print("\nPuedes ejecutar:")
    print("  .\\start_celery_beat.bat")
    print("  .\\start_celery_worker.bat")
    print("="*60 + "\n")

except redis.exceptions.ResponseError as e:
    print(f"\nERROR: {e}")
    print("\nEsto indica que la base de datos especificada no existe.")
    print("Redis Cloud Free solo permite DB 0.")
    print("\nSolucion:")
    print("1. Verifica que .env tenga:")
    print("   CELERY_BROKER_URL=...../0")
    print("   CELERY_RESULT_BACKEND=...../0")
    print("2. Reinicia el script")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
