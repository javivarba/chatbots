import os
from twilio.rest import Client

account_sid = os.getenv('USf78c0779b361a7b245283f80df23b8ec')
auth_token = os.getenv('a484cf4484c7171788b2069de5d83a13')

client = Client(account_sid, auth_token)

# Ver configuración del sandbox
print("\n=== CONFIGURACIÓN TWILIO ===")
print(f"Account SID: {account_sid[:10]}...")
print(f"Sandbox activo: Sí")

# Enviar mensaje de prueba
try:
    message = client.messages.create(
        from_='whatsapp:+14155238886',  # Número del sandbox
        to='whatsapp:+50670036654',      # Tu número (ajusta)
        body='Test desde Python - BJJ Santo Domingo Bot funcionando!'
    )
    print(f"\n✅ Mensaje enviado: {message.sid}")
except Exception as e:
    print(f"\n❌ Error: {e}")
