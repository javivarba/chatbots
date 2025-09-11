from app import create_app, db
from app.models import Academy, Lead, Conversation

app = create_app('default')

with app.app_context():
    print('📊 Verificando base de datos...')
    print(f'Academias: {Academy.query.count()}')
    print(f'Leads: {Lead.query.count()}')
    print(f'Conversaciones: {Conversation.query.count()}')
    
    # Mostrar primer lead
    lead = Lead.query.first()
    if lead:
        print(f'\nPrimer lead: {lead.name} - {lead.phone}')
