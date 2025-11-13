"""
Script para verificar y configurar Twilio Sandbox
"""
import sys
import os

# Fix encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from dotenv import load_dotenv
load_dotenv()

print("\n" + "="*60)
print("CONFIGURACION TWILIO SANDBOX - BJJ MINGO")
print("="*60 + "\n")

try:
    from twilio.rest import Client

    # Cargar credenciales
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')

    print("1. Conectando a Twilio...")
    client = Client(account_sid, auth_token)

    print("   [OK] Conectado a Twilio\n")

    # Obtener información de la cuenta
    print("2. Informacion de tu cuenta Twilio:")
    account = client.api.accounts(account_sid).fetch()
    print(f"   Account SID: {account.sid}")
    print(f"   Status: {account.status}")
    print(f"   Tipo: {account.type}")

    # Intentar obtener configuración del Sandbox
    print("\n3. Verificando WhatsApp Sandbox...")

    try:
        # Listar servicios de mensajería
        services = list(client.messaging.v1.services.list(limit=20))

        if services:
            print(f"   [OK] Encontrados {len(services)} servicios de mensajeria")
            for service in services:
                print(f"   - {service.friendly_name} (SID: {service.sid})")
        else:
            print("   [!] No se encontraron servicios de mensajeria configurados")
    except Exception as e:
        print(f"   [!] No se pudieron listar servicios: {e}")

    # Obtener números de teléfono disponibles
    print("\n4. Numeros de telefono en tu cuenta:")
    try:
        phone_numbers = client.incoming_phone_numbers.list(limit=20)

        if phone_numbers:
            print(f"   [OK] Encontrados {len(phone_numbers)} numeros")
            for number in phone_numbers:
                print(f"   - {number.phone_number} ({number.friendly_name})")
        else:
            print("   [!] No tienes numeros de telefono configurados")
            print("   [!] Para WhatsApp Sandbox, no necesitas comprar un numero")
    except Exception as e:
        print(f"   [!] Error listando numeros: {e}")

    print("\n" + "="*60)
    print("INSTRUCCIONES PARA CONFIGURAR SANDBOX")
    print("="*60 + "\n")

    print("IMPORTANTE: Como ya usaste +50670150369 para testing,")
    print("es posible que ya este registrado en el Sandbox.\n")

    print("PASOS A SEGUIR:\n")

    print("1. Accede a Twilio Console Sandbox:")
    print("   https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn\n")

    print("2. En esa pagina veras:")
    print("   - Un CODIGO DE SANDBOX (ej: 'join animal-cat')")
    print("   - Un NUMERO DE WHATSAPP (ej: '+1 415 523 8886')\n")

    print("3. COPIA ese codigo de sandbox (lo necesitaremos)\n")

    print("4. Desde +50670150369, envia un WhatsApp a ese numero con:")
    print("   Mensaje: 'join [codigo-que-viste]'\n")

    print("5. Espera confirmacion de Twilio (llegara en segundos)\n")

    print("6. Una vez confirmado, actualiza el .env con el numero correcto")
    print("   (lo verificaremos en el siguiente paso)\n")

    print("="*60)
    print("\nCuando hayas completado estos pasos, presiona ENTER...")
    input()

    print("\n[!] Ahora vamos a verificar el numero correcto del Sandbox\n")
    print("Ve a: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
    print("\nEn esa pagina, busca 'Your Sandbox Phone Number'")
    print("y copialo exactamente como aparece (ej: +1 415 523 8886)\n")

    sandbox_number = input("Pega aqui el numero del Sandbox: ").strip()

    if sandbox_number:
        # Limpiar el número
        sandbox_number = sandbox_number.replace(" ", "").replace("-", "")
        if not sandbox_number.startswith("+"):
            sandbox_number = "+" + sandbox_number

        print(f"\n[OK] Numero del Sandbox: {sandbox_number}")
        print(f"     Formato para .env: whatsapp:{sandbox_number}")

        # Actualizar .env
        print("\n5. Actualizando archivo .env...")

        env_path = os.path.join(os.path.dirname(__file__), '.env')

        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Actualizar la línea de TWILIO_WHATSAPP_NUMBER
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('TWILIO_WHATSAPP_NUMBER='):
                lines[i] = f'TWILIO_WHATSAPP_NUMBER=whatsapp:{sandbox_number}\n'
                updated = True
                break

        if updated:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"   [OK] .env actualizado con: whatsapp:{sandbox_number}")
        else:
            print("   [!] No se encontro TWILIO_WHATSAPP_NUMBER en .env")
            print(f"   Agrega manualmente: TWILIO_WHATSAPP_NUMBER=whatsapp:{sandbox_number}")

        print("\n6. Probando conexion con el nuevo numero...")
        print("   Ejecuta: python quick_test.py")
        print("\n[OK] Configuracion completada!")
    else:
        print("\n[!] No se proporciono numero. Actualiza .env manualmente:")
        print("    TWILIO_WHATSAPP_NUMBER=whatsapp:+[numero-del-sandbox]")

except ImportError:
    print("[X] Error: twilio library no instalada")
    print("    Instala con: pip install twilio")
except Exception as e:
    print(f"\n[X] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
