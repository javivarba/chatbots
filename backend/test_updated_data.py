from app import create_app
from app.services.ai_service import AIService
from app.models import Academy, Lead, Conversation

app = create_app('default')

with app.app_context():
    ai = AIService()
    academy = Academy.query.first()
    lead = Lead.query.first()
    conv = Conversation.query.first()
    
    if ai.enabled and all([academy, lead, conv]):
        response = ai.generate_response(
            "¿Cuál es el teléfono de la academia?",
            lead, conv, academy, use_history=False
        )
        print(f"\nRespuesta del bot:")
        print(response)
        
        # Verificar que menciona los datos correctos
        if "BJJ Santo Domingo" in response:
            print("\n✅ Nombre correcto")
        if "70036654" in response or "+506 7003 6654" in response:
            print("✅ Teléfono correcto")
