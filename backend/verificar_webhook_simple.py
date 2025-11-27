"""
Script para verificar que el webhook de WhatsApp está configurado correctamente
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*70)
print("  VERIFICACIÓN DE CONFIGURACIÓN WEBHOOK WHATSAPP")
print("="*70 + "\n")

# 1. Verificar que Flask está corriendo
print("[1] Verificando Flask Server...")
try:
    response = requests.get("http://localhost:5000/", timeout=5)
    if response.status_code in [200, 405]:  # 405 es normal para GET en endpoint POST
        print("    Flask está corriendo en http://localhost:5000")
    else:
        print(f"     Flask respondió con status {response.status_code}")
except Exception as e:
    print(f"    Flask NO está corriendo: {e}")
    print("    Solución: Ejecuta 'python run.py' en otra terminal")
    exit(1)

# 2. Verificar Ngrok
print("\n2  Verificando Ngrok...")
try:
    response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
    if response.status_code == 200:
        tunnels = response.json()
        if tunnels.get('tunnels'):
            public_url = tunnels['tunnels'][0]['public_url']
            print(f"    Ngrok está corriendo")
            print(f"    URL pública: {public_url}")
        else:
            print("     Ngrok corriendo pero sin túneles activos")
    else:
        print(f"     Ngrok respondió con status {response.status_code}")
except Exception as e:
    print(f"    Ngrok NO está corriendo: {e}")
    print("    Solución: Ejecuta 'ngrok http 5000' en otra terminal")
    exit(1)

# 3. Probar el webhook localmente
print("\n3  Probando webhook localmente...")
try:
    test_data = {
        'Body': 'Test de verificación',
        'From': 'whatsapp:+50688887777',
        'ProfileName': 'Test User'
    }
    response = requests.post("http://localhost:5000/", data=test_data, timeout=10)
    if response.status_code == 200:
        print("    Webhook local funciona correctamente")
        if '<Message>' in response.text:
            print("    Bot está respondiendo (encontró tag <Message>)")
        else:
            print("     Respuesta sin formato esperado")
    else:
        print(f"    Webhook falló con status {response.status_code}")
except Exception as e:
    print(f"    Error probando webhook: {e}")

# 4. Verificar credenciales de Twilio
print("\n4  Verificando credenciales de Twilio...")
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')

if account_sid and auth_token and twilio_phone:
    print(f"    TWILIO_ACCOUNT_SID: {account_sid[:8]}...")
    print(f"    TWILIO_AUTH_TOKEN: {auth_token[:8]}...")
    print(f"    TWILIO_PHONE_NUMBER: {twilio_phone}")
else:
    print("    Faltan credenciales de Twilio en .env")
    if not account_sid:
        print("      - Falta TWILIO_ACCOUNT_SID")
    if not auth_token:
        print("      - Falta TWILIO_AUTH_TOKEN")
    if not twilio_phone:
        print("      - Falta TWILIO_PHONE_NUMBER")

print("\n" + "="*70)
print("  PRÓXIMOS PASOS PARA CONFIGURAR TWILIO")
print("="*70 + "\n")

print(" PASO 1: Configurar Webhook en Twilio Console")
print("-" * 70)
print(f"1. Ve a: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox")
print(f"2. En 'When a message comes in', pega esta URL:")
print(f"    {public_url}/")
print(f"3. Método: POST")
print(f"4. Click en 'Save'")

print("\n PASO 2: Unirse al Sandbox de WhatsApp")
print("-" * 70)
print("1. Desde tu celular, abre WhatsApp")
print("2. Envía mensaje a: +1 415 523 8886")
print("3. Envía el código que te dio Twilio (algo como: 'join palabra-clave')")
print("    Búscalo en: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox")
print("4. Deberías recibir: 'You are all set!'")

print("\n PASO 3: Probar enviando mensaje")
print("-" * 70)
print("1. Envía 'Hola' al número de WhatsApp (+1 415 523 8886)")
print("2. Deberías recibir respuesta del bot")
print("3. En los logs de Flask (Terminal 1) deberías ver:")
print("   127.0.0.1 - - [fecha] \"POST / HTTP/1.1\" 200 -")

print("\n PASO 4: Verificar si llegó el mensaje")
print("-" * 70)
print("Si NO ves el log del POST en Flask:")
print("  a) Verifica que la URL en Twilio sea exactamente:")
print(f"     {public_url}/")
print("  b) Verifica que el método sea POST (no GET)")
print("  c) Revisa los logs de Ngrok en http://localhost:4040")
print("  d) Asegúrate de haberte unido al sandbox con 'join'")

print("\n Si TODO está configurado, prueba enviando 'Hola' por WhatsApp")
print("="*70 + "\n")
