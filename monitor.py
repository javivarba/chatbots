from app import create_app, db
from app.models import Lead, Conversation, Message
import time

app = create_app('default')

with app.app_context():
    while True:
        print('\033[2J\033[H')  # Clear screen
        print('📊 MONITOR EN TIEMPO REAL')
        print('=' * 40)
        
        # Estadísticas
        leads = Lead.query.count()
        conversations = Conversation.query.count()
        messages = Message.query.count()
        
        print(f'Leads: {leads}')
        print(f'Conversaciones: {conversations}')
        print(f'Mensajes: {messages}')
        
        # Últimos mensajes
        print('\n📨 Últimos 5 mensajes:')
        print('-' * 40)
        
        recent_messages = Message.query.order_by(
            Message.created_at.desc()
        ).limit(5).all()
        
        for msg in recent_messages:
            direction = '⬅️' if msg.direction == 'inbound' else '➡️'
            content = msg.content[:50] + '...' if len(msg.content) > 50 else msg.content
            print(f'{direction} {content}')
        
        time.sleep(5)  # Actualizar cada 5 segundos
