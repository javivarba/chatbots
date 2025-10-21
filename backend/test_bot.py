from app.services.message_handler import MessageHandler

# Inicializar el handler
handler = MessageHandler()

# Simular un mensaje
phone = "+50612345678"
message = "Hola, quiero información sobre las clases"

print("Enviando mensaje de prueba...")
response = handler.process_message(phone, message, name="Test User")

print("\n=== RESPUESTA DEL BOT ===")
print(response)