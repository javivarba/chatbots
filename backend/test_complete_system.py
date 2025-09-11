"""
Script de validación completa del sistema BJJ Academy Bot
"""
import os
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Inicializar colorama para Windows
init()

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"{text}")
    print(f"{'='*50}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def check_environment():
    """Verifica variables de entorno"""
    print_header("1. VERIFICANDO CONFIGURACIÓN")
    
    required_vars = {
        'FLASK_APP': 'app',
        'DATABASE_URL': 'Base de datos',
        'OPENAI_API_KEY': 'OpenAI API'
    }
    
    issues = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value != 'sk-your-openai-api-key-here':
            print_success(f"{description} configurado")
        else:
            print_warning(f"{description} no configurado")
            if var == 'OPENAI_API_KEY':
                print("  -> Bot usará respuestas predefinidas")
    
    return len(issues) == 0

def check_database():
    """Verifica la base de datos"""
    print_header("2. VERIFICANDO BASE DE DATOS")
    
    try:
        from app import create_app, db
        from app.models import Academy, Lead, Conversation, Message
        
        app = create_app('default')
        with app.app_context():
            # Verificar tablas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['academies', 'leads', 'conversations', 'messages']
            for table in required_tables:
                if table in tables:
                    print_success(f"Tabla '{table}' existe")
                else:
                    print_error(f"Tabla '{table}' NO existe")
            
            # Verificar datos
            academy_count = Academy.query.count()
            lead_count = Lead.query.count()
            conv_count = Conversation.query.count()
            msg_count = Message.query.count()
            
            print(f"\n  Datos actuales:")
            print(f"  • Academias: {academy_count}")
            print(f"  • Leads: {lead_count}")
            print(f"  • Conversaciones: {conv_count}")
            print(f"  • Mensajes: {msg_count}")
            
            if academy_count == 0:
                print_warning("No hay academias - ejecuta init_db.py")
                return False
                
            return True
    except Exception as e:
        print_error(f"Error conectando a BD: {e}")
        return False

def check_services():
    """Verifica que los servicios funcionan"""
    print_header("3. VERIFICANDO SERVICIOS")
    
    try:
        # MessageProcessor
        from app.services.message_processor import MessageProcessor
        processor = MessageProcessor()
        print_success("MessageProcessor cargado")
        
        # AIService
        from app.services.ai_service import AIService
        ai_service = AIService()
        if ai_service.enabled:
            print_success(f"AIService habilitado (modelo: {ai_service.model})")
        else:
            print_warning("AIService deshabilitado (sin API key)")
        
        return True
    except Exception as e:
        print_error(f"Error cargando servicios: {e}")
        return False

def check_webhooks():
    """Verifica los webhooks"""
    print_header("4. VERIFICANDO WEBHOOKS")
    
    try:
        import requests
        
        # Verificar que Flask está corriendo
        try:
            response = requests.get('http://localhost:5000/health', timeout=2)
            if response.status_code == 200:
                print_success("Flask está corriendo")
                data = response.json()
                print(f"  • Estado: {data.get('status')}")
                print(f"  • BD: {data.get('database')}")
            else:
                print_warning("Flask responde pero con error")
        except requests.exceptions.ConnectionError:
            print_warning("Flask no está corriendo - ejecuta 'python run.py'")
            return False
        
        # Verificar webhook endpoint
        response = requests.get('http://localhost:5000/webhooks/whatsapp/test')
        if response.status_code == 200:
            print_success("Webhook WhatsApp accesible")
        else:
            print_error("Webhook no accesible")
            
        return True
    except Exception as e:
        print_error(f"Error verificando webhooks: {e}")
        return False

def test_message_flow():
    """Prueba el flujo completo de mensajes"""
    print_header("5. PROBANDO FLUJO DE MENSAJES")
    
    try:
        from app import create_app, db
        from app.models import Academy, Lead, Conversation
        from app.services.message_processor import MessageProcessor
        
        app = create_app('default')
        with app.app_context():
            # Obtener academia
            academy = Academy.query.first()
            if not academy:
                print_error("No hay academia para probar")
                return False
            
            # Crear lead de prueba
            test_lead = Lead(
                academy_id=academy.id,
                phone="test123456",
                name="Test User",
                source="test",
                status="new"
            )
            db.session.add(test_lead)
            db.session.commit()
            
            # Crear conversación
            test_conv = Conversation(
                academy_id=academy.id,
                lead_id=test_lead.id,
                platform="test",
                is_active=True
            )
            db.session.add(test_conv)
            db.session.commit()
            
            # Probar procesamiento
            processor = MessageProcessor()
            
            test_messages = [
                "Hola",
                "¿Cuánto cuesta?",
                "¿Dónde quedan?"
            ]
            
            for msg in test_messages:
                response = processor.process_message(
                    msg, test_lead, test_conv, academy
                )
                if response and len(response) > 10:
                    print_success(f"Mensaje '{msg}' -> Respuesta OK ({len(response)} chars)")
                else:
                    print_error(f"Mensaje '{msg}' -> Sin respuesta")
            
            # Limpiar datos de prueba
            db.session.delete(test_conv)
            db.session.delete(test_lead)
            db.session.commit()
            
            return True
            
    except Exception as e:
        print_error(f"Error en flujo de mensajes: {e}")
        return False

def main():
    print(f"\n{Fore.MAGENTA}╔══════════════════════════════════════════════╗")
    print(f"║     BJJ ACADEMY BOT - VALIDACIÓN COMPLETA     ║")
    print(f"╚══════════════════════════════════════════════╝{Style.RESET_ALL}")
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'Configuración': check_environment(),
        'Base de datos': check_database(),
        'Servicios': check_services(),
        'Webhooks': check_webhooks(),
        'Flujo mensajes': test_message_flow()
    }
    
    print_header("RESUMEN DE VALIDACIÓN")
    
    all_passed = True
    for component, status in results.items():
        if status:
            print_success(f"{component}")
        else:
            print_error(f"{component}")
            all_passed = False
    
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    if all_passed:
        print(f"{Fore.GREEN}🎉 SISTEMA FUNCIONANDO CORRECTAMENTE 🎉{Style.RESET_ALL}")
        print("\nPróximos pasos recomendados:")
        print("1. Configurar Twilio para WhatsApp real")
        print("2. Crear dashboard de administración")
        print("3. Implementar sistema de follow-up automático")
    else:
        print(f"{Fore.YELLOW}⚠️ HAY COMPONENTES QUE REQUIEREN ATENCIÓN{Style.RESET_ALL}")
        print("\nRevisa los errores arriba y:")
        print("1. Asegúrate que Flask está corriendo")
        print("2. Verifica la configuración en .env")
        print("3. Ejecuta init_db.py si faltan datos")
    
    return all_passed

if __name__ == "__main__":
    # Instalar colorama si no está
    try:
        import colorama
    except ImportError:
        print("Instalando colorama para mejor visualización...")
        os.system("pip install colorama")
        import colorama
    
    success = main()
    sys.exit(0 if success else 1)
