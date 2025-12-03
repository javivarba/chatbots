"""
Script para verificar el estado de conexiones a Redis
"""
import os
from dotenv import load_dotenv
import redis

load_dotenv()

redis_url = os.getenv('REDIS_URL')

print("\n" + "="*70)
print("  VERIFICACION DE CONEXIONES A REDIS")
print("="*70 + "\n")

try:
    # Conectar a Redis
    r = redis.from_url(redis_url, decode_responses=True)

    # Obtener información del servidor
    info = r.info('clients')

    print(f"Conexiones actuales: {info['connected_clients']}")
    print(f"Conexiones bloqueadas: {info.get('blocked_clients', 0)}")

    # Obtener información de memoria
    memory_info = r.info('memory')
    print(f"\nMemoria usada: {memory_info['used_memory_human']}")
    print(f"Memoria pico: {memory_info['used_memory_peak_human']}")

    # Obtener lista de clientes conectados
    print("\n" + "-"*70)
    print("CLIENTES CONECTADOS:")
    print("-"*70)

    clients = r.client_list()

    # Agrupar por nombre
    client_groups = {}
    for client in clients:
        name = client.get('name', 'unnamed')
        if name not in client_groups:
            client_groups[name] = 0
        client_groups[name] += 1

    print(f"\nTotal de conexiones: {len(clients)}")
    print("\nPor tipo:")
    for name, count in sorted(client_groups.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {count} conexiones")

    print("\n" + "="*70)
    print("  LIMITE DEL PLAN GRATUITO: 30 CONEXIONES")
    print("="*70)

    percentage = (len(clients) / 30) * 100
    print(f"\nUso actual: {len(clients)}/30 ({percentage:.1f}%)")

    if percentage > 80:
        print("\n⚠️  ALERTA: Cerca del limite!")
        print("Acciones recomendadas:")
        print("  1. Matar procesos duplicados")
        print("  2. Verificar que solo hay 1 Flask + 1 Worker + 1 Beat corriendo")
        print("  3. Considerar upgrade a plan de pago ($7/mes, 256 conexiones)")
    elif percentage > 60:
        print("\n⚠️  Uso moderado - monitorear")
    else:
        print("\n✅ Uso normal")

    # Cerrar la conexión de prueba
    r.close()

except Exception as e:
    print(f"❌ Error conectando a Redis: {e}")

print("\n")
