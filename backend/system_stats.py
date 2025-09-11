"""
Estadísticas del sistema BJJ Academy Bot
"""
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Academy, Lead, Conversation, Message
from sqlalchemy import func

app = create_app('default')

with app.app_context():
    print("\n" + "="*50)
    print("📊 ESTADÍSTICAS DEL SISTEMA")
    print("="*50)
    
    # Academia
    academy = Academy.query.first()
    if academy:
        print(f"\n🏢 Academia: {academy.name}")
        print(f"   Plan: {academy.subscription_plan}")
        print(f"   Creada: {academy.created_at.strftime('%Y-%m-%d')}")
    
    # Leads
    total_leads = Lead.query.count()
    new_leads = Lead.query.filter_by(status='new').count()
    engaged_leads = Lead.query.filter_by(status='engaged').count()
    interested_leads = Lead.query.filter_by(status='interested').count()
    
    print(f"\n👥 Leads Totales: {total_leads}")
    print(f"   • Nuevos: {new_leads}")
    print(f"   • Comprometidos: {engaged_leads}")
    print(f"   • Interesados: {interested_leads}")
    
    # Conversaciones
    total_convs = Conversation.query.count()
    active_convs = Conversation.query.filter_by(is_active=True).count()
    
    print(f"\n💬 Conversaciones: {total_convs}")
    print(f"   • Activas: {active_convs}")
    
    # Mensajes
    total_msgs = Message.query.count()
    inbound = Message.query.filter_by(direction='inbound').count()
    outbound = Message.query.filter_by(direction='outbound').count()
    
    print(f"\n📨 Mensajes Totales: {total_msgs}")
    print(f"   • Recibidos: {inbound}")
    print(f"   • Enviados: {outbound}")
    
    # Últimos mensajes
    recent_msgs = Message.query.order_by(
        Message.created_at.desc()
    ).limit(3).all()
    
    if recent_msgs:
        print(f"\n📝 Últimos mensajes:")
        for msg in recent_msgs:
            direction = "⬅️" if msg.direction == "inbound" else "➡️"
            content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"   {direction} {content}")
    
    # Tasa de respuesta
    if inbound > 0:
        response_rate = (outbound / inbound) * 100
        print(f"\n📈 Tasa de respuesta: {response_rate:.1f}%")
    
    print("\n" + "="*50)
