from app import create_app, db
from app.models import Academy, Lead, Conversation, Message

app = create_app("default")

with app.app_context():
    print("?? Estado de la Base de Datos:")
    print("=" * 40)
    
    academies = Academy.query.all()
    print(f"Academias: {len(academies)}")
    for academy in academies:
        print(f"  - {academy.name}")
    
    leads = Lead.query.all()
    print(f"\nLeads: {len(leads)}")
    for lead in leads[:5]:
        print(f"  - {lead.name or 'Sin nombre'} - {lead.phone}")
    
    conversations = Conversation.query.all()
    print(f"\nConversaciones: {len(conversations)}")
    
    messages = Message.query.all()
    print(f"Mensajes: {len(messages)}")
    
    print("=" * 40)