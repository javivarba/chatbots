"""
Simulador de WhatsApp para testing local
"""
import requests
import json
from datetime import datetime

# URL del webhook local
WEBHOOK_URL = "http://localhost:5000/webhook/whatsapp"

def simulate_whatsapp_message(message, from_number="+50670036654", name="BJJ Mingo"):
    """
    Simula un mensaje de WhatsApp enviado al webhook
    """
    # Datos que enviaría Twilio
    data = {
        'MessageSid': f'SM{datetime.now().timestamp()}',
        'From': f'whatsapp:{from_number}',
        'To': 'whatsapp:+14155238886',
        'Body': message,
        'ProfileName': name,
        'NumMedia': '0'
    }
    
    print(f"\n[PHONE] Enviando mensaje: '{message}'")
    print(f"   De: {from_number} ({name})")
    
    try:
        response = requests.post(WEBHOOK_URL, data=data)
        
        if response.status_code == 200:
            # Parsear la respuesta XML de Twilio
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            # Buscar el mensaje de respuesta
            message_elem = root.find('.//Message')
            if message_elem is not None:
                response_text = message_elem.text
                print(f"\n[BOT] Respuesta del bot:")
                print("-" * 40)
                print(response_text)
                print("-" * 40)
            else:
                print("[OK] Mensaje procesado (sin respuesta)")
        else:
            print(f"[ERROR] Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("[ERROR] Error: No se puede conectar al servidor")
        print("   Asegurate de que Flask esta corriendo (python run.py)")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def main():
    print("=" * 50)
    print("[BOT] SIMULADOR DE WHATSAPP BOT")
    print("=" * 50)
    print("\nComandos especiales:")
    print("  /salir - Terminar simulación")
    print("  /cambiar - Cambiar número/nombre")
    print("\n")
    
    phone = input("[PHONE] Numero de telefono (ej: +50688881234): ") or "+50688881234"
    name = input("[USER] Nombre (ej: Juan Perez): ") or "Test User"

    print(f"\n[OK] Simulando mensajes desde {phone} ({name})")
    print("=" * 50)

    while True:
        message = input("\n[CHAT] Escribe un mensaje (o /salir): ")
        
        if message.lower() == '/salir':
            print("\n[EXIT] Terminando simulacion...")
            break
        elif message.lower() == '/cambiar':
            phone = input("[PHONE] Nuevo numero: ") or phone
            name = input("[USER] Nuevo nombre: ") or name
            print(f"[OK] Cambiado a {phone} ({name})")
            continue
        elif message.strip() == '':
            continue
            
        simulate_whatsapp_message(message, phone, name)

    print("\n[DONE] Simulacion terminada")

if __name__ == "__main__":
    main()
