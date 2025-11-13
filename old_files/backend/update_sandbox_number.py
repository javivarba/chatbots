"""
Script para actualizar el numero de Twilio Sandbox en .env
"""
import os

print("\n" + "="*60)
print("ACTUALIZAR NUMERO DE TWILIO SANDBOX")
print("="*60 + "\n")

print("Primero, necesitas hacer estos pasos:\n")
print("1. Ve a: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
print("2. Copia el CODIGO de sandbox (ej: 'join animal-cat')")
print("3. Desde WhatsApp +50670150369, envia ese codigo al numero de Twilio")
print("4. Espera la confirmacion de Twilio\n")

response = input("Ya completaste estos pasos? (si/no): ").strip().lower()

if response != 'si':
    print("\n[!] Completa esos pasos primero y vuelve a ejecutar este script.")
    print("="*60 + "\n")
    exit(0)

print("\n" + "="*60)
print("Ahora vamos a actualizar el archivo .env")
print("="*60 + "\n")

print("En la pagina de Twilio Console, busca 'Your Sandbox Phone Number'")
print("Ejemplos de numeros validos:")
print("  +1 415 523 8886")
print("  +12027599459")
print("  +1-202-759-9459\n")

sandbox_number = input("Pega aqui el numero del Sandbox: ").strip()

if not sandbox_number:
    print("\n[X] No proporcionaste un numero. Saliendo...")
    exit(1)

# Limpiar el número
sandbox_number = sandbox_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

if not sandbox_number.startswith("+"):
    sandbox_number = "+" + sandbox_number

print(f"\n[OK] Numero limpio: {sandbox_number}")
print(f"     Formato para .env: whatsapp:{sandbox_number}\n")

# Confirmar
confirm = input("Es correcto este numero? (si/no): ").strip().lower()

if confirm != 'si':
    print("\n[!] Cancelado. Ejecuta el script de nuevo con el numero correcto.")
    exit(0)

# Actualizar .env
env_path = os.path.join(os.path.dirname(__file__), '.env')

print(f"\n[!] Actualizando {env_path}...")

try:
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Actualizar la línea de TWILIO_WHATSAPP_NUMBER
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('TWILIO_WHATSAPP_NUMBER='):
            old_value = line.strip()
            lines[i] = f'TWILIO_WHATSAPP_NUMBER=whatsapp:{sandbox_number}\n'
            updated = True
            print(f"   Anterior: {old_value}")
            print(f"   Nuevo:    TWILIO_WHATSAPP_NUMBER=whatsapp:{sandbox_number}")
            break

    if updated:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("\n[OK] Archivo .env actualizado correctamente!\n")
    else:
        print("\n[!] No se encontro TWILIO_WHATSAPP_NUMBER en .env")
        print(f"    Agrega esta linea manualmente:")
        print(f"    TWILIO_WHATSAPP_NUMBER=whatsapp:{sandbox_number}\n")

except Exception as e:
    print(f"\n[X] Error actualizando .env: {e}\n")
    exit(1)

print("="*60)
print("SIGUIENTE PASO")
print("="*60 + "\n")
print("Ahora prueba la configuracion ejecutando:")
print("  python quick_test.py\n")
print("Deberas recibir un WhatsApp en +50670150369 con los detalles")
print("de un prospecto de prueba.\n")
print("="*60 + "\n")
