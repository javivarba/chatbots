print("\n=== CONFIGURACIÓN DE TWILIO ===\n")
print("Ve a https://console.twilio.com")
print("Necesitas:")
print("1. Account SID (en Dashboard)")
print("2. Auth Token (en Dashboard)")
print("3. Número del Sandbox (algo como +14155238886)")
print("\nIngresa los datos:\n")

import os

account_sid = input("ACef289d5e1f787e4cc365962d535457e7").strip()
auth_token = input("a484cf4484c7171788b2069de5d83a13").strip()
whatsapp_number = input("+14155238886").strip()

# Leer .env actual
with open('.env', 'r') as f:
    lines = f.readlines()

# Actualizar valores
updated = []
for line in lines:
    if line.startswith('TWILIO_ACCOUNT_SID='):
        updated.append(f'TWILIO_ACCOUNT_SID={account_sid}\n')
    elif line.startswith('TWILIO_AUTH_TOKEN='):
        updated.append(f'TWILIO_AUTH_TOKEN={auth_token}\n')
    elif line.startswith('TWILIO_WHATSAPP_NUMBER='):
        updated.append(f'TWILIO_WHATSAPP_NUMBER=whatsapp:{whatsapp_number}\n')
    else:
        updated.append(line)

# Guardar
with open('.env', 'w') as f:
    f.writelines(updated)

print("\n✅ Credenciales actualizadas en .env")
