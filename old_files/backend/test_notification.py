"""
Script de Prueba de Notificaciones Twilio WhatsApp
Prueba directa del envío de notificaciones con diagnóstico detallado
"""

import os
from dotenv import load_dotenv
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def test_twilio_notification():
    """Prueba el envío de notificación con diagnóstico completo"""
    
    print_header("🔔 PRUEBA DE NOTIFICACIONES TWILIO WHATSAPP")
    
    # Cargar variables de entorno
    load_dotenv(override=True)
    
    # Paso 1: Verificar configuración
    print_header("1. VERIFICANDO CONFIGURACIÓN")
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    
    print_info(f"Account SID: {account_sid[:10]}..." if account_sid else "❌ No configurado")
    print_info(f"Auth Token: {'*' * 20} (configurado)" if auth_token else "❌ No configurado")
    print_info(f"WhatsApp Number: {whatsapp_number}" if whatsapp_number else "❌ No configurado")
    
    if not all([account_sid, auth_token, whatsapp_number]):
        print_error("Faltan credenciales de Twilio en .env")
        return False
    
    # Verificar formato del número
    print_header("2. VERIFICANDO FORMATO DEL NÚMERO")
    
    # Limpiar el número si viene con prefijo
    clean_number = whatsapp_number.replace('whatsapp:', '').strip()
    print_info(f"Número limpio: {clean_number}")
    
    # Verificar si es sandbox
    is_sandbox = clean_number == '+14155238886'
    if is_sandbox:
        print_warning("Usando SANDBOX de Twilio")
        print_info("Los números destino deben estar unidos al sandbox")
    else:
        print_success("Usando número de producción")
    
    # Paso 2: Obtener número destino
    print_header("3. CONFIGURANDO NÚMERO DESTINO")
    
    try:
        from app.config.academy_info import ACADEMY_INFO
        contacts = ACADEMY_INFO.get('notification_contacts', {})
        to_number = contacts.get('primary_whatsapp')
        
        if not to_number:
            print_error("primary_whatsapp no configurado en academy_info")
            return False
        
        print_success(f"Número destino: {to_number}")
        
        # Limpiar el número destino
        clean_to_number = to_number.replace('whatsapp:', '').strip()
        
        # Verificar formato (debe empezar con +)
        if not clean_to_number.startswith('+'):
            print_warning(f"Número no tiene formato internacional, agregando +")
            if clean_to_number.startswith('506'):
                clean_to_number = '+' + clean_to_number
            print_info(f"Número corregido: {clean_to_number}")
        
    except ImportError:
        print_error("No se pudo importar academy_info")
        print_info("Usando número de prueba...")
        clean_to_number = '+50670150369'  # Tu número de prueba
    
    # Paso 3: Inicializar cliente de Twilio
    print_header("4. INICIALIZANDO CLIENTE TWILIO")
    
    try:
        from twilio.rest import Client
        
        client = Client(account_sid, auth_token)
        print_success("Cliente de Twilio inicializado")
        
    except ImportError:
        print_error("Librería 'twilio' no instalada")
        print_info("Instalar con: pip install twilio")
        return False
    except Exception as e:
        print_error(f"Error inicializando cliente: {e}")
        return False
    
    # Paso 4: Construir mensaje de prueba
    print_header("5. CONSTRUYENDO MENSAJE DE PRUEBA")
    
    test_message = f"""🔔 *PRUEBA DE NOTIFICACIÓN*

✅ Este es un mensaje de prueba del sistema de notificaciones de BJJ Mingo.

📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Si recibiste este mensaje, las notificaciones están funcionando correctamente.

---
*Sistema de Notificaciones BJJ Mingo*"""
    
    print_success("Mensaje construido")
    print_info(f"Longitud: {len(test_message)} caracteres")
    
    # Paso 5: Formatear números para WhatsApp
    print_header("6. FORMATEANDO NÚMEROS PARA WHATSAPP")
    
    from_whatsapp = f"whatsapp:{clean_number}"
    to_whatsapp = f"whatsapp:{clean_to_number}"
    
    print_info(f"From: {from_whatsapp}")
    print_info(f"To: {to_whatsapp}")
    
    # Paso 6: Intentar envío
    print_header("7. ENVIANDO NOTIFICACIÓN")
    
    try:
        print_info("Llamando a Twilio API...")
        
        message = client.messages.create(
            from_=from_whatsapp,
            to=to_whatsapp,
            body=test_message
        )
        
        print_success(f"✅ ¡NOTIFICACIÓN ENVIADA EXITOSAMENTE!")
        print_info(f"Message SID: {message.sid}")
        print_info(f"Status: {message.status}")
        print_info(f"Direction: {message.direction}")
        
        print_header("✅ RESULTADO: ÉXITO")
        print_success("La notificación fue enviada correctamente")
        print_info(f"Revisa tu WhatsApp en: {clean_to_number}")
        
        return True
        
    except Exception as e:
        print_error(f"Error enviando notificación: {e}")
        
        # Diagnóstico del error
        print_header("🔍 DIAGNÓSTICO DEL ERROR")
        
        error_str = str(e)
        
        if "not a valid phone number" in error_str:
            print_warning("El número FROM no es válido")
            print_info("Posibles causas:")
            print_info("1. El número en .env ya incluye 'whatsapp:' (debe ser solo el número)")
            print_info("2. El formato del número no es correcto")
            print_info(f"3. El número del sandbox debe ser exactamente: +14155238886")
            print_info("\nVerifica tu .env:")
            print_info(f"TWILIO_WHATSAPP_NUMBER={clean_number}")
            print_info("(sin el prefijo 'whatsapp:')")
            
        elif "not authorized" in error_str:
            print_warning("El número destino no está autorizado")
            print_info("Para el sandbox:")
            print_info("1. El número destino debe unirse al sandbox primero")
            print_info("2. Envía el código de unión desde WhatsApp al: +1 415 523 8886")
            print_info("3. Verifica en: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
            
        elif "authenticate" in error_str or "credentials" in error_str:
            print_warning("Problema con las credenciales")
            print_info("Verifica:")
            print_info("1. TWILIO_ACCOUNT_SID es correcto")
            print_info("2. TWILIO_AUTH_TOKEN es correcto")
            print_info("3. Las credenciales están en el .env correcto")
            
        else:
            print_warning("Error desconocido")
            print_info(f"Error completo: {error_str}")
        
        return False

def test_with_notification_service():
    """Prueba usando el NotificationService real"""
    
    print_header("🔄 PROBANDO CON NOTIFICATION SERVICE")
    
    try:
        from app.services.notification_service import NotificationService
        
        notifier = NotificationService()
        
        if not notifier.twilio_available:
            print_error("NotificationService reporta que Twilio no está disponible")
            return False
        
        print_success("NotificationService inicializado")
        
        # Crear datos de prueba
        test_lead = {
            'name': 'Juan Pérez (PRUEBA)',
            'phone': '+506-1234-5678',
            'status': 'trial_scheduled'
        }
        
        test_trial = {
            'clase_nombre': 'Jiu-Jitsu Adultos',
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'dias_texto': 'Lunes a Viernes',
            'hora': '18:00',
            'notes': 'Mensaje de prueba del sistema'
        }
        
        print_info("Enviando notificación con NotificationService...")
        result = notifier.notify_new_trial_booking(test_lead, test_trial)
        
        if result['success']:
            print_success("✅ Notificación enviada por NotificationService")
            if 'sid' in result:
                print_info(f"SID: {result['sid']}")
            return True
        else:
            print_error(f"Error: {result['message']}")
            return False
            
    except Exception as e:
        print_error(f"Error usando NotificationService: {e}")
        import traceback
        print_info(traceback.format_exc())
        return False

def main():
    """Función principal"""
    
    print_header("🚀 INICIANDO PRUEBA DE NOTIFICACIONES")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Prueba 1: Envío directo
    print_info("\n" + "="*60)
    print_info("PRUEBA 1: Envío directo con Twilio")
    print_info("="*60)
    
    direct_success = test_twilio_notification()
    
    # Prueba 2: Con NotificationService
    print_info("\n" + "="*60)
    print_info("PRUEBA 2: Usando NotificationService")
    print_info("="*60)
    
    service_success = test_with_notification_service()
    
    # Resumen
    print_header("📊 RESUMEN DE RESULTADOS")
    
    if direct_success:
        print_success("Envío directo: EXITOSO ✅")
    else:
        print_error("Envío directo: FALLÓ ❌")
    
    if service_success:
        print_success("NotificationService: EXITOSO ✅")
    else:
        print_error("NotificationService: FALLÓ ❌")
    
    if direct_success and service_success:
        print_header("🎉 ¡TODO FUNCIONANDO!")
        print_success("Las notificaciones están configuradas correctamente")
    elif direct_success and not service_success:
        print_header("⚠️ PROBLEMA EN NOTIFICATION SERVICE")
        print_warning("El envío directo funciona pero el servicio tiene problemas")
        print_info("Verifica la configuración en app/config/academy_info.py")
    else:
        print_header("❌ NECESITA CONFIGURACIÓN")
        print_warning("Revisa el diagnóstico arriba para solucionar los problemas")
    
    return direct_success or service_success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)