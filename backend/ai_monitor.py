from app import create_app
from app.services.openai_service import AIService
import os

app = create_app('default')

with app.app_context():
    print("\n=== ESTADO DE IA ===")
    
    ai = AIService()
    if ai.enabled:
        print(f"✅ OpenAI activo")
        print(f"   Modelo: {ai.model}")
        print(f"   Max tokens: {ai.max_tokens}")
        print(f"   Temperatura: {ai.temperature}")
    else:
        print("❌ OpenAI no configurado")
    
    # Test rápido
    if ai.enabled:
        from app.models import Academy, Lead, Conversation
        academy = Academy.query.first()
        lead = Lead.query.first()
        conv = Conversation.query.first()
        
        if all([academy, lead, conv]):
            response = ai.generate_response(
                "Hola", lead, conv, academy, use_history=False
            )
            print(f"\nTest: '{response[:100]}...'")
