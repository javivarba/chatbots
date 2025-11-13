"""
Script rápido para probar el sistema de notificaciones
"""
import sys
import os
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Cargar variables de entorno
load_dotenv()

print("\n" + "="*60)
print("PRUEBA RAPIDA - SISTEMA DE NOTIFICACIONES BJJ MINGO")
print("="*60 + "\n")

# 1. Verificar variables de entorno
print("1. Verificando variables de entorno...")
twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

print(f"   TWILIO_ACCOUNT_SID: {'[OK] Configurado' if twilio_sid else '[X] No encontrado'}")
print(f"   TWILIO_AUTH_TOKEN: {'[OK] Configurado' if twilio_token else '[X] No encontrado'}")
print(f"   TWILIO_WHATSAPP_NUMBER: {twilio_number if twilio_number else '[X] No encontrado'}")

if not all([twilio_sid, twilio_token, twilio_number]):
    print("\n[X] ERROR: Faltan credenciales de Twilio en .env")
    sys.exit(1)

print("\n2. Importando modulos...")
try:
    from app.services.notification_service import NotificationService
    print("   [OK] notification_service importado")
except Exception as e:
    print(f"   [X] Error importando notification_service: {e}")
    sys.exit(1)

print("\n3. Inicializando NotificationService...")
try:
    notifier = NotificationService()
    if notifier.twilio_available:
        print("   [OK] Twilio inicializado correctamente")
    else:
        print("   [!] Twilio no disponible")
except Exception as e:
    print(f"   [X] Error inicializando: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Enviando notificacion de prueba...")
print("   Destino: +50670150369")
print("   Origen: " + twilio_number)

try:
    result = notifier.test_notification()

    print("\n" + "="*60)
    print("RESULTADO")
    print("="*60)

    if result['success']:
        print("[OK] Notificacion enviada exitosamente!")
        print(f"   Twilio SID: {result.get('sid', 'N/A')}")
        print("\n[!] Revisa el WhatsApp: +50670150369")
        print("   Deberias recibir un mensaje con los detalles del prospecto de prueba.")
    else:
        print("[X] No se pudo enviar la notificacion")
        print(f"   Razon: {result['message']}")

        if "not a valid" in result['message'].lower():
            print("\n[!] POSIBLE SOLUCION:")
            print("   El numero +50670150369 debe estar registrado en Twilio Sandbox.")
            print("   Pasos:")
            print("   1. Envia un WhatsApp a: +1 415 523 8886")
            print("   2. Mensaje: 'join [codigo de tu sandbox]'")
            print("   3. Espera confirmacion")
            print("   4. Vuelve a ejecutar este script")

    print("\n" + "="*60 + "\n")

except Exception as e:
    print(f"\n[X] Error durante la prueba: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
