from app import create_app, db
from app.models import Conversation
from sqlalchemy import func

app = create_app("default")

with app.app_context():
    print("📊 Métricas de uso de IA:")
    print("=" * 40)
    
    # Conversaciones con IA
    total_convs = Conversation.query.count()
    
    # Mensajes totales
    total_msgs = db.session.query(
        func.sum(Conversation.message_count)
    ).scalar() or 0
    
    print(f"Conversaciones totales: {total_convs}")
    print(f"Mensajes totales: {total_msgs}")
    
    # Si tienes campos de tokens/costo (opcional)
    # total_tokens = db.session.query(
    #     func.sum(Conversation.total_tokens_used)
    # ).scalar() or 0
    # print(f"Tokens usados: {total_tokens}")
