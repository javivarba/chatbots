import time
from datetime import datetime
from app import create_app, db
from app.models import Message, Lead, Conversation

app = create_app('default')

print("📱 MONITOR DE WHATSAPP EN TIEMPO REAL")
print("=" * 50)
print("Esperando mensajes...")
print("(Ctrl+C para salir)\n")

last_count = 0

with app.app_context():
    while True:
        try:
            # Contar mensajes
            current_count = Message.query.count()
            
            if current_count > last_count:
                # Nuevos mensajes!
                new_messages = Message.query.order_by(
                    Message.created_at.desc()
                ).limit(current_count - last_count).all()
                
                for msg in reversed(new_messages):
                    direction = "📱→" if msg.direction == "inbound" else "🤖→"
                    
                    # Obtener info del lead
                    conv = Conversation.query.get(msg.conversation_id)
                    if conv:
                        lead = Lead.query.get(conv.lead_id)
                        sender = lead.name if lead else "Unknown"
                    else:
                        sender = "Unknown"
                    
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {direction} {sender}")
                    print(f"   {msg.content[:100]}...")
                
                last_count = current_count
            
            time.sleep(2)  # Check cada 2 segundos
            
        except KeyboardInterrupt:
            print("\n\n✅ Monitor detenido")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
