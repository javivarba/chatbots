from app import create_app, db
from app.models import Academy, Lead, Conversation, Message

app = create_app("default")

with app.app_context():
    print("\n=== ESTADO DEL SISTEMA ===")
    print(f"Academias: {Academy.query.count()}")
    print(f"Leads: {Lead.query.count()}")
    print(f"Conversaciones: {Conversation.query.count()}")
    print(f"Mensajes: {Message.query.count()}")
    
    # Verificar si OpenAI está configurado
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "sk-your-openai-api-key-here":
        print(f"OpenAI: ✅ Configurado")
    else:
        print(f"OpenAI: ❌ No configurado")
    
    print("========================\n")
