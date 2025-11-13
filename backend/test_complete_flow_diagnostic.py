"""
Script de Test con Diagnóstico para BJJ Mingo WhatsApp Bot
Primero verifica qué archivos y clases están disponibles
"""

import os
import sys
import sqlite3
import importlib
import inspect
from datetime import datetime
from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar variables de entorno
load_dotenv(override=True)

# Colores para el output
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

class DiagnosticTest:
    def __init__(self):
        self.services_path = os.path.join('app', 'services')
        self.config_path = os.path.join('app', 'config')
        self.available_services = {}
        self.db_path = 'bjj_academy.db'
        
    def check_file_structure(self):
        """Verifica la estructura de archivos"""
        print_header("1. VERIFICANDO ESTRUCTURA DE ARCHIVOS")
        
        # Verificar directorio de servicios
        if os.path.exists(self.services_path):
            print_success(f"Directorio de servicios encontrado: {self.services_path}")
            
            # Listar archivos de servicios
            service_files = [f for f in os.listdir(self.services_path) if f.endswith('.py')]
            print_info(f"Archivos de servicio encontrados:")
            for file in service_files:
                print(f"  - {file}")
                
                # Verificar clases en cada archivo
                self.check_classes_in_file(os.path.join(self.services_path, file))
        else:
            print_error(f"Directorio de servicios NO encontrado: {self.services_path}")
        
        # Verificar directorio de configuración
        if os.path.exists(self.config_path):
            print_success(f"Directorio de config encontrado: {self.config_path}")
            
            config_files = [f for f in os.listdir(self.config_path) if f.endswith('.py')]
            print_info(f"Archivos de configuración encontrados:")
            for file in config_files:
                print(f"  - {file}")
        else:
            print_warning(f"Directorio de config NO encontrado: {self.config_path}")
    
    def check_classes_in_file(self, filepath):
        """Verifica qué clases contiene un archivo"""
        filename = os.path.basename(filepath)
        module_name = filename.replace('.py', '')
        
        try:
            # Leer el archivo para buscar definiciones de clase
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar definiciones de clase
            import re
            class_pattern = r'class\s+(\w+)\s*\('
            classes = re.findall(class_pattern, content)
            
            if classes:
                print(f"    📦 {filename} contiene: {', '.join(classes)}")
                
                # Guardar info para uso posterior
                for class_name in classes:
                    self.available_services[class_name] = f"app.services.{module_name}"
            
        except Exception as e:
            print_warning(f"    No se pudo leer {filename}: {e}")
    
    def try_import_services(self):
        """Intenta importar los servicios disponibles"""
        print_header("2. INTENTANDO IMPORTAR SERVICIOS")
        
        imported = {}
        
        # Lista de servicios esperados
        expected_services = [
            'MessageProcessor',
            'NotificationService',
            'AppointmentScheduler',
            'AIService'
        ]
        
        for service_name in expected_services:
            if service_name in self.available_services:
                module_path = self.available_services[service_name]
                try:
                    module = importlib.import_module(module_path)
                    service_class = getattr(module, service_name)
                    imported[service_name] = service_class
                    print_success(f"✓ {service_name} importado desde {module_path}")
                except Exception as e:
                    print_error(f"✗ No se pudo importar {service_name}: {e}")
            else:
                print_warning(f"⚠ {service_name} no encontrado en los archivos")
        
        return imported
    
    def check_database(self):
        """Verifica el estado de la base de datos"""
        print_header("3. VERIFICANDO BASE DE DATOS")
        
        if not os.path.exists(self.db_path):
            print_error(f"Base de datos NO encontrada: {self.db_path}")
            return False
        
        print_success(f"Base de datos encontrada: {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print_info("Tablas en la base de datos:")
            for table in tables:
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} registros")
            
            conn.close()
            return True
            
        except Exception as e:
            print_error(f"Error verificando BD: {e}")
            return False
    
    def check_environment(self):
        """Verifica las variables de entorno"""
        print_header("4. VERIFICANDO VARIABLES DE ENTORNO")
        
        env_vars = {
            'OPENAI_API_KEY': False,
            'TWILIO_ACCOUNT_SID': False,
            'TWILIO_AUTH_TOKEN': False,
            'TWILIO_WHATSAPP_NUMBER': False
        }
        
        for var in env_vars:
            value = os.getenv(var)
            if value and value != f'your-{var.lower()}-here':
                env_vars[var] = True
                # Mostrar solo los primeros caracteres por seguridad
                display_value = value[:10] + "..." if len(value) > 10 else value
                print_success(f"✓ {var}: {display_value}")
            else:
                print_warning(f"✗ {var}: No configurado")
        
        return env_vars
    
    def test_basic_flow(self, services):
        """Prueba básica del flujo con los servicios disponibles"""
        print_header("5. PRUEBA BÁSICA DEL FLUJO")
        
        if not services:
            print_error("No hay servicios disponibles para probar")
            return False
        
        # Mock objects
        class MockLead:
            def __init__(self):
                self.id = 1
                self.phone = "+506-TEST-1234"
                self.name = "Test User"
                self.status = "new"
                self.source = "whatsapp"
            
            def calculate_lead_score(self):
                return 8
        
        class MockConversation:
            def __init__(self):
                self.id = 1
                self.lead_id = 1
                self.status = "active"
        
        class MockAcademy:
            def __init__(self):
                self.name = "BJJ Mingo"
                self.phone = "+506-8888-8888"
        
        results = {}
        
        # Test MessageProcessor si está disponible
        if 'MessageProcessor' in services:
            try:
                print_info("\nProbando MessageProcessor...")
                processor = services['MessageProcessor']()
                lead = MockLead()
                conversation = MockConversation()
                academy = MockAcademy()
                
                response = processor.process_message(
                    "Hola, quiero información",
                    lead, conversation, academy
                )
                
                if response:
                    print_success("MessageProcessor funcionando")
                    print(f"  Respuesta: {response[:100]}...")
                    results['message_processor'] = True
                else:
                    print_warning("MessageProcessor no generó respuesta")
                    results['message_processor'] = False
                    
            except Exception as e:
                print_error(f"Error en MessageProcessor: {e}")
                results['message_processor'] = False
        
        # Test AIService si está disponible
        if 'AIService' in services:
            try:
                print_info("\nProbando AIService...")
                ai_service = services['AIService']()
                
                if hasattr(ai_service, 'test_connection'):
                    success, message = ai_service.test_connection()
                    if success:
                        print_success(f"AIService funcionando: {message}")
                        results['ai_service'] = True
                    else:
                        print_warning(f"AIService no conectado: {message}")
                        results['ai_service'] = False
                else:
                    print_info("AIService no tiene método test_connection")
                    results['ai_service'] = None
                    
            except Exception as e:
                print_error(f"Error en AIService: {e}")
                results['ai_service'] = False
        
        # Test AppointmentScheduler si está disponible
        if 'AppointmentScheduler' in services:
            try:
                print_info("\nProbando AppointmentScheduler...")
                scheduler = services['AppointmentScheduler']()
                
                # Probar parseo
                parsed = scheduler.parse_appointment_request(
                    "Quiero agendar jiu-jitsu adultos el martes"
                )
                
                if parsed.get('parsed'):
                    print_success("AppointmentScheduler funcionando")
                    print(f"  Clase detectada: {parsed.get('clase_nombre')}")
                    results['appointment_scheduler'] = True
                else:
                    print_warning("AppointmentScheduler no pudo parsear")
                    results['appointment_scheduler'] = False
                    
            except Exception as e:
                print_error(f"Error en AppointmentScheduler: {e}")
                results['appointment_scheduler'] = False
        
        # Test NotificationService si está disponible
        if 'NotificationService' in services:
            try:
                print_info("\nProbando NotificationService...")
                notifier = services['NotificationService']()
                
                # Solo verificar que se puede instanciar
                print_success("NotificationService instanciado")
                results['notification_service'] = True
                
                # Verificar si Twilio está configurado
                if hasattr(notifier, 'twilio_available'):
                    if notifier.twilio_available:
                        print_info("  Twilio disponible")
                    else:
                        print_warning("  Twilio no configurado")
                        
            except Exception as e:
                print_error(f"Error en NotificationService: {e}")
                results['notification_service'] = False
        
        return results
    
    def run_diagnostic(self):
        """Ejecuta el diagnóstico completo"""
        print_header("🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA BJJ MINGO")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Directorio actual: {os.getcwd()}")
        
        # 1. Verificar estructura de archivos
        self.check_file_structure()
        
        # 2. Intentar importar servicios
        imported_services = self.try_import_services()
        
        # 3. Verificar base de datos
        db_ok = self.check_database()
        
        # 4. Verificar variables de entorno
        env_vars = self.check_environment()
        
        # 5. Probar flujo básico
        if imported_services:
            flow_results = self.test_basic_flow(imported_services)
        else:
            flow_results = {}
        
        # Resumen final
        print_header("📊 RESUMEN DEL DIAGNÓSTICO")
        
        print("\n🗂️ ARCHIVOS:")
        if self.available_services:
            for service, location in self.available_services.items():
                print(f"  ✓ {service} en {location}")
        else:
            print("  ✗ No se encontraron servicios")
        
        print("\n💾 BASE DE DATOS:")
        if db_ok:
            print("  ✓ Base de datos operativa")
        else:
            print("  ✗ Problemas con la base de datos")
        
        print("\n🔐 CONFIGURACIÓN:")
        for var, configured in env_vars.items():
            if configured:
                print(f"  ✓ {var}")
            else:
                print(f"  ✗ {var}")
        
        print("\n⚙️ SERVICIOS:")
        for service, status in flow_results.items():
            if status:
                print(f"  ✓ {service}")
            elif status is False:
                print(f"  ✗ {service}")
            else:
                print(f"  ⚠ {service} (parcial)")
        
        # Recomendaciones
        print_header("💡 RECOMENDACIONES")
        
        if 'NotificationService' not in self.available_services and 'MessageProcessor' in self.available_services:
            print_warning("Parece que los archivos están mezclados:")
            print("  1. Verifica que notification_service.py contenga la clase NotificationService")
            print("  2. Verifica que message_processor.py contenga la clase MessageProcessor")
            print("  3. Puede que necesites renombrar los archivos o mover las clases")
        
        if not any(env_vars.values()):
            print_warning("No hay variables de entorno configuradas:")
            print("  1. Crea un archivo .env en el directorio backend")
            print("  2. Agrega las claves de OpenAI y Twilio")
        
        return imported_services, flow_results

def main():
    """Función principal"""
    test = DiagnosticTest()
    services, results = test.run_diagnostic()
    
    # Retornar código de salida apropiado
    if services and any(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()