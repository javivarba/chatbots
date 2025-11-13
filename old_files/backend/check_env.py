"""
Verificador de Configuración .env para Notificaciones
Revisa y sugiere correcciones en el formato
"""

import os
from dotenv import load_dotenv

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def check_env_config():
    """Verifica la configuración del .env"""
    
    print_header("🔍 VERIFICADOR DE CONFIGURACIÓN .ENV")
    
    # Cargar .env
    load_dotenv(override=True)
    
    issues = []
    corrections = []
    
    # Verificar TWILIO_WHATSAPP_NUMBER
    print_header("1. VERIFICANDO TWILIO_WHATSAPP_NUMBER")
    
    whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    
    if not whatsapp_number:
        print_error("TWILIO_WHATSAPP_NUMBER no está configurado")
        issues.append("missing_whatsapp_number")
        corrections.append("Agregar: TWILIO_WHATSAPP_NUMBER=+14155238886")
    else:
        print_info(f"Valor actual: {whatsapp_number}")
        
        # Verificar formato
        if whatsapp_number.startswith('whatsapp:'):
            print_error("❌ El número tiene el prefijo 'whatsapp:'")
            print_warning("El prefijo se agrega automáticamente en el código")
            clean_number = whatsapp_number.replace('whatsapp:', '').strip()
            corrections.append(f"Cambiar a: TWILIO_WHATSAPP_NUMBER={clean_number}")
            issues.append("wrong_format_whatsapp")
        elif not whatsapp_number.startswith('+'):
            print_warning("⚠️  El número no tiene formato internacional (+)")
            corrections.append(f"Cambiar a: TWILIO_WHATSAPP_NUMBER=+{whatsapp_number}")
            issues.append("missing_plus")
        elif whatsapp_number == '+14155238886':
            print_success("✅ Formato correcto - Twilio Sandbox")
            print_info("Recuerda: los números destino deben unirse al sandbox")
        else:
            print_success("✅ Formato correcto - Número de producción")
    
    # Verificar TWILIO_ACCOUNT_SID
    print_header("2. VERIFICANDO TWILIO_ACCOUNT_SID")
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    
    if not account_sid:
        print_error("TWILIO_ACCOUNT_SID no está configurado")
        issues.append("missing_account_sid")
        corrections.append("Agregar: TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx")
    else:
        if account_sid.startswith('AC'):
            print_success(f"✅ Formato correcto: {account_sid[:10]}...")
        else:
            print_warning("⚠️  No tiene el formato esperado (debe empezar con 'AC')")
            issues.append("wrong_sid_format")
    
    # Verificar TWILIO_AUTH_TOKEN
    print_header("3. VERIFICANDO TWILIO_AUTH_TOKEN")
    
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not auth_token:
        print_error("TWILIO_AUTH_TOKEN no está configurado")
        issues.append("missing_auth_token")
        corrections.append("Agregar: TWILIO_AUTH_TOKEN=tu_token_de_twilio")
    else:
        print_success(f"✅ Configurado: {'*' * 20}")
    
    # Verificar academy_info
    print_header("4. VERIFICANDO NOTIFICATION_CONTACTS")
    
    try:
        from app.config.academy_info import ACADEMY_INFO
        contacts = ACADEMY_INFO.get('notification_contacts', {})
        
        primary = contacts.get('primary_whatsapp')
        
        if not primary:
            print_error("primary_whatsapp no configurado en academy_info.py")
            issues.append("missing_primary_contact")
            corrections.append("Configurar primary_whatsapp en app/config/academy_info.py")
        else:
            print_info(f"Valor actual: {primary}")
            
            # Verificar formato
            if primary.startswith('whatsapp:'):
                print_error("❌ El número tiene el prefijo 'whatsapp:'")
                clean = primary.replace('whatsapp:', '').strip()
                corrections.append(f"En academy_info.py, cambiar a: 'primary_whatsapp': '{clean}'")
                issues.append("wrong_format_primary")
            elif not primary.startswith('+'):
                print_warning("⚠️  El número no tiene formato internacional")
                corrections.append(f"En academy_info.py, cambiar a: 'primary_whatsapp': '+{primary}'")
                issues.append("missing_plus_primary")
            else:
                print_success("✅ Formato correcto")
                
    except ImportError:
        print_error("No se pudo importar academy_info.py")
        issues.append("academy_info_import")
    
    # Resumen
    print_header("📊 RESUMEN")
    
    if not issues:
        print_success("✅ ¡TODA LA CONFIGURACIÓN ESTÁ CORRECTA!")
        print_info("\nSi las notificaciones aún no funcionan:")
        print_info("1. Ejecuta: python test_notifications.py")
        print_info("2. Verifica que el número destino esté unido al sandbox")
    else:
        print_warning(f"⚠️  Se encontraron {len(issues)} problema(s)")
        
        if corrections:
            print_header("🔧 CORRECCIONES NECESARIAS")
            for i, correction in enumerate(corrections, 1):
                print(f"  {i}. {correction}")
        
        print_info("\nDespués de corregir:")
        print_info("1. Guarda los archivos")
        print_info("2. Ejecuta: python test_notifications.py")
    
    return len(issues) == 0

def show_example_env():
    """Muestra ejemplo de .env correcto"""
    
    print_header("📝 EJEMPLO DE .env CORRECTO")
    
    example = """
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACef289d5e1f787e4cc365962d535457e7
TWILIO_AUTH_TOKEN=tu_token_aqui_sin_comillas
TWILIO_WHATSAPP_NUMBER=+14155238886

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-tu-key-aqui
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=600
OPENAI_TEMPERATURE=0.2

# Google Calendar (opcional)
GOOGLE_CALENDAR_ID=tu_calendar_id@group.calendar.google.com
"""
    
    print(example)
    
    print_header("📝 EJEMPLO DE academy_info.py CORRECTO")
    
    example_py = """
ACADEMY_INFO = {
    'name': 'BJJ Mingo',
    'phone': '+506-7015-0369',
    'notification_contacts': {
        'primary_whatsapp': '+50670150369',      # ← Sin 'whatsapp:'
        'secondary_whatsapp': '+50688888888',
        'email': 'testingtoimp2025@gmail.com'
    }
}
"""
    
    print(example_py)

if __name__ == "__main__":
    import sys
    
    success = check_env_config()
    
    print("\n")
    show_example_env()
    
    sys.exit(0 if success else 1)