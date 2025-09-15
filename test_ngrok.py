import requests

ngrok_url = input("Pega tu URL de ngrok (sin /webhooks...): ").strip()

# Test el health endpoint
try:
    response = requests.get(f"{ngrok_url}/health")
    if response.status_code == 200:
        print(f"✅ Conexión exitosa!")
        print(f"   Response: {response.json()}")
    else:
        print(f"⚠️ Respuesta inesperada: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test el webhook endpoint
try:
    response = requests.get(f"{ngrok_url}/webhooks/whatsapp/test")
    if response.status_code == 200:
        print(f"✅ Webhook endpoint accesible!")
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ Error en webhook: {e}")
