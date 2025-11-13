"""
Script de Test Completo para BJJ Mingo WhatsApp Bot
Versión corregida sin dependencias de SQLAlchemy
"""

import os
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar variables de entorno
load_dotenv(override=True)

# Importar solo los servicios necesarios (sin models)
from app.services.message_processor import MessageProcessor
from app.services.appointment_scheduler import AppointmentScheduler
from app.services.notification_service import NotificationService
from app.services.ai_service import AIService

# Intentar importar academy_info
try:
    from app.config.academy_info import ACADEMY_INFO
except ImportError:
    print("⚠️ No se pudo importar academy_info, usando valores por defecto")
    ACADEMY_INFO = {
        'name': 'BJJ Mingo',
        'phone': '+506-8888-8888',
        'notification_contacts': {
            'primary_whatsapp': '+50670150369',
            'secondary_whatsapp': '',
            'email': 'bjjmingo@gmail.com'
        }
    }

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
    print(f"{Colors.GREEN}[OK] {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}[ERROR] {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.ENDC}")

# Clases Mock para simular los modelos
class MockLead:
    def __init__(self, id, phone, name, status, source):
        self.id = id
        self.phone = phone
        self.phone_number = phone  # Algunos servicios usan phone_number
        self.name = name
        self.status = status
        self.source = source
        self.interest_level = 5
    
    def calculate_lead_score(self):
        """Método mock para calcular score"""
        self.interest_level = 8
        return self.interest_level

class MockConversation:
    def __init__(self, id, lead_id, status):
        self.id = id
        self.lead_id = lead_id
        self.status = status

class MockAcademy:
    def __init__(self):
        self.name = ACADEMY_INFO['name']
        self.phone = ACADEMY_INFO.get('phone', '+506-8888-8888')
        self.email = ACADEMY_INFO.get('email', 'info@bjjmingo.com')
        self.id = 1

class CompleteFlowTest:
    def __init__(self):
        """Inicializa el test con todos los servicios"""
        self.test_phone = "+506-TEST-1234"
        self.db_path = 'bjj_academy.db'
        
    def check_database(self):
        """Verifica que la base de datos existe y tiene las tablas necesarias"""
        print_header("0. VERIFICANDO BASE DE DATOS")
        
        if not os.path.exists(self.db_path):
            print_error(f"Base de datos no encontrada: {self.db_path}")
            print_info("Creando base de datos...")
            self.create_database()
        else:
            print_success(f"Base de datos encontrada: {self.db_path}")
        
        # Verificar tablas
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['academies', 'leads', 'conversations', 'messages', 'appointments', 'trial_weeks']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print_warning(f"Tablas faltantes: {', '.join(missing_tables)}")
            print_info("Creando tablas faltantes...")
            self.create_missing_tables(conn, missing_tables)
        else:
            print_success(f"Todas las tablas necesarias existen: {', '.join(required_tables)}")
        
        conn.close()
        return True
    
    def create_database(self):
        """Crea la base de datos con todas las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear todas las tablas
        self.create_missing_tables(conn, ['academies', 'leads', 'conversations', 'messages', 'appointments', 'trial_weeks'])
        
        conn.commit()
        conn.close()
        print_success("Base de datos creada exitosamente")
    
    def create_missing_tables(self, conn, tables):
        """Crea las tablas que faltan"""
        cursor = conn.cursor()
        
        if 'academies' in tables:
            cursor.execute("""
                CREATE TABLE academies (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    active INTEGER DEFAULT 1
                )
            """)
            print_info("Tabla 'academies' creada")
        
        if 'leads' in tables:
            cursor.execute("""
                CREATE TABLE leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    academy_id INTEGER NOT NULL,
                    phone TEXT NOT NULL,
                    name TEXT,
                    email TEXT,
                    source TEXT DEFAULT 'whatsapp',
                    status TEXT DEFAULT 'new',
                    goals TEXT,
                    experience_level TEXT,
                    trial_class_date TEXT,
                    converted_date TEXT,
                    last_contact_date TEXT,
                    follow_up_count INTEGER DEFAULT 0,
                    lead_score INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (academy_id) REFERENCES academies(id)
                )
            """)
            print_info("Tabla 'leads' creada")
        
        if 'conversations' in tables:
            cursor.execute("""
                CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    academy_id INTEGER NOT NULL,
                    lead_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    session_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    message_count INTEGER DEFAULT 0,
                    inbound_count INTEGER DEFAULT 0,
                    outbound_count INTEGER DEFAULT 0,
                    started_at TEXT,
                    last_message_at TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (academy_id) REFERENCES academies(id),
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            """)
            print_info("Tabla 'conversations' creada")
        
        if 'messages' in tables:
            cursor.execute("""
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
            print_info("Tabla 'messages' creada")
        
        if 'appointments' in tables:
            cursor.execute("""
                CREATE TABLE appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL,
                    appointment_datetime TEXT,
                    status TEXT DEFAULT 'scheduled',
                    confirmed INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TEXT,
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            """)
            print_info("Tabla 'appointments' creada")

        if 'trial_weeks' in tables:
            cursor.execute("""
                CREATE TABLE trial_weeks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL,
                    clase_tipo TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT DEFAULT 'active',
                    notes TEXT,
                    created_at TEXT,
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            """)
            print_info("Tabla 'trial_weeks' creada")
        
        conn.commit()
        
    def setup_test_data(self):
        """Configura datos de prueba en la BD"""
        print_header("1. CONFIGURANDO DATOS DE PRUEBA")
    
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
        # Limpiar datos de test anteriores
            cursor.execute("DELETE FROM leads WHERE phone = ?", (self.test_phone,))
            conn.commit()

        # Crear academia si no existe
            cursor.execute("SELECT COUNT(*) FROM academies WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO academies (id, name, phone, email, address, active)
                    VALUES (1, 'BJJ Mingo', '+506-8888-8888', 'info@bjjmingo.com',
                        'Santo Domingo de Heredia', 1)
                """)
                conn.commit()
                print_success("Academia creada en BD")
            else:
                print_info("Academia ya existe en BD")

            # Crear lead con academy_id
            cursor.execute("""
                INSERT INTO leads (phone, name, status, source, academy_id, created_at)
                VALUES (?, 'Test User', 'new', 'whatsapp', 1, ?)
            """, (self.test_phone, datetime.now().isoformat()))

            lead_id = cursor.lastrowid

            # Crear conversación
            cursor.execute("""
                INSERT INTO conversations (lead_id, academy_id, platform, is_active, created_at)
                VALUES (?, 1, 'whatsapp', 1, ?)
            """, (lead_id, datetime.now().isoformat()))
        
            conv_id = cursor.lastrowid
        
            conn.commit()
            conn.close()
        
            print_success(f"Lead de prueba creado - ID: {lead_id}")
            print_success(f"Conversación creada - ID: {conv_id}")
        
            return lead_id, conv_id
        
        except Exception as e:
            print_error(f"Error configurando datos: {e}")
            if conn:
                conn.close()
            return None, None
    
    def test_configuration(self):
        """Verifica la configuración de todos los servicios"""
        print_header("2. VERIFICANDO CONFIGURACIÓN")
        
        results = {
            'academy_info': False,
            'openai': False,
            'twilio': False,
            'notification_contacts': False
        }
        
        # 1. Verificar academy_info
        try:
            print_info("Verificando academy_info...")
            print(f"  - Nombre: {ACADEMY_INFO['name']}")
            print(f"  - Teléfono: {ACADEMY_INFO.get('phone', 'NO CONFIGURADO')}")
            
            if 'notification_contacts' in ACADEMY_INFO:
                contacts = ACADEMY_INFO['notification_contacts']
                print(f"  - WhatsApp Primario: {contacts.get('primary_whatsapp', 'NO CONFIGURADO')}")
                print(f"  - WhatsApp Secundario: {contacts.get('secondary_whatsapp', 'NO CONFIGURADO')}")
                print(f"  - Email: {contacts.get('email', 'NO CONFIGURADO')}")
                results['notification_contacts'] = True
                print_success("Contactos de notificación configurados")
            else:
                print_warning("notification_contacts no encontrado en academy_info")
        except Exception as e:
            print_error(f"Error con academy_info: {e}")
        
        # 2. Verificar OpenAI
        try:
            print_info("\nVerificando OpenAI...")
            ai_service = AIService()
            if ai_service.enabled:
                success, message = ai_service.test_connection()
                if success:
                    print_success(f"OpenAI conectado: {message}")
                    results['openai'] = True
                else:
                    print_warning(f"OpenAI no funciona: {message}")
            else:
                print_warning("OpenAI no habilitado")
        except Exception as e:
            print_error(f"Error con OpenAI: {e}")
        
        # 3. Verificar Twilio
        try:
            print_info("\nVerificando Twilio...")
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
            
            if account_sid and auth_token and whatsapp_number:
                print(f"  - Account SID: {account_sid[:10]}...")
                print(f"  - WhatsApp Number: {whatsapp_number}")
                results['twilio'] = True
                print_success("Credenciales de Twilio configuradas")
            else:
                print_warning("Credenciales de Twilio incompletas")
        except Exception as e:
            print_error(f"Error con Twilio: {e}")
        
        return results
    
    def test_message_processing(self, lead_id, conv_id):
        """Prueba el procesamiento de mensajes"""
        print_header("3. PROBANDO PROCESAMIENTO DE MENSAJES")
        
        try:
            # Crear objetos mock
            lead = MockLead(lead_id, self.test_phone, "Test User", "new", "whatsapp")
            conversation = MockConversation(conv_id, lead_id, "active")
            academy = MockAcademy()
            
            # Inicializar procesador
            processor = MessageProcessor()
            
            # Probar diferentes mensajes
            test_messages = [
                ("Hola, quisiera información", "Saludo inicial"),
                ("¿Cuáles son los horarios?", "Consulta de horarios"),
                ("Me gustaría agendar una clase de prueba", "Solicitud de clase"),
                ("Quiero probar Jiu-Jitsu adultos", "Confirmación de clase")
            ]
            
            for message, description in test_messages:
                print_info(f"\nProbando: {description}")
                print(f"  Mensaje: '{message}'")
                
                response = processor.process_message(
                    message, lead, conversation, academy
                )

                if response:
                    print_success("Respuesta generada:")
                    try:
                        # Intentar imprimir, pero manejar errores de encoding
                        safe_response = response.encode('ascii', 'ignore').decode('ascii')
                        print(f"  {safe_response[:200]}..." if len(safe_response) > 200 else f"  {safe_response}")
                    except Exception as e:
                        print(f"  [Respuesta contiene caracteres especiales - longitud: {len(response)}]")
                else:
                    print_error("No se generó respuesta")
            
            return True
            
        except Exception as e:
            print_error(f"Error procesando mensajes: {e}")
            return False
    
    def test_appointment_booking(self, lead_id):
        """Prueba el agendamiento de clase y notificación"""
        print_header("4. PROBANDO AGENDAMIENTO Y NOTIFICACIÓN")
        
        try:
            # Inicializar scheduler
            scheduler = AppointmentScheduler()
            
            # Probar parseo de solicitud
            print_info("\nProbando parseo de solicitud...")
            request = "Quiero agendar Jiu-Jitsu adultos para el martes"
            parsed = scheduler.parse_appointment_request(request, lead_id)
            
            if parsed['parsed']:
                print_success("Solicitud parseada correctamente:")
                print(f"  - Clase: {parsed['clase_nombre']}")
                print(f"  - Fecha: {parsed['date']}")
                print(f"  - Hora: {parsed['time']}")
            else:
                print_warning("No se pudo parsear la solicitud")
            
            # Probar agendamiento de semana de prueba
            print_info("\nAgendando semana de prueba...")
            result = scheduler.book_trial_week(
                lead_id=lead_id,
                clase_tipo='adultos_jiujitsu',
                notes='Test de flujo completo'
            )
            
            if result['success']:
                print_success("Semana de prueba agendada:")
                try:
                    safe_message = result['message'].encode('ascii', 'ignore').decode('ascii')
                    print(safe_message[:300] + "...")
                except Exception:
                    print("[Mensaje contiene caracteres especiales]")
                
                # Verificar en BD
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM trial_weeks
                    WHERE lead_id = ? AND status = 'active'
                """, (lead_id,))

                trial = cursor.fetchone()
                if trial:
                    print_success(f"Trial registrado en BD - ID: {trial[0]}")

                # Verificar status del lead
                cursor.execute("SELECT status FROM leads WHERE id = ?", (lead_id,))
                status = cursor.fetchone()[0]
                print_info(f"Status del lead actualizado a: {status}")
                
                conn.close()
                
                return True
            else:
                print_error(f"Error agendando: {result['message']}")
                return False
                
        except Exception as e:
            print_error(f"Error en agendamiento: {e}")
            return False
    
    def test_notification_service(self):
        """Prueba el servicio de notificaciones directamente"""
        print_header("5. PROBANDO SERVICIO DE NOTIFICACIONES")
        
        try:
            notifier = NotificationService()
            
            print_info("Enviando notificación de prueba...")
            result = notifier.test_notification()
            
            if result['success']:
                print_success(f"Notificación enviada: {result['message']}")
                if 'sid' in result:
                    print_info(f"Twilio SID: {result['sid']}")
            else:
                print_warning(f"Notificación no enviada: {result['message']}")
            
            return result['success']
            
        except Exception as e:
            print_error(f"Error en notificación: {e}")
            return False
    
    def cleanup(self):
        """Limpia los datos de prueba"""
        print_header("6. LIMPIANDO DATOS DE PRUEBA")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Obtener lead_id
            cursor.execute("SELECT id FROM leads WHERE phone = ?", (self.test_phone,))
            result = cursor.fetchone()

            if result:
                lead_id = result[0]

                # Limpiar en orden por foreign keys
                cursor.execute("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE lead_id = ?)", (lead_id,))
                cursor.execute("DELETE FROM appointments WHERE lead_id = ?", (lead_id,))
                cursor.execute("DELETE FROM trial_weeks WHERE lead_id = ?", (lead_id,))
                cursor.execute("DELETE FROM conversations WHERE lead_id = ?", (lead_id,))
                cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
                
                conn.commit()
                print_success("Datos de prueba limpiados")
            
            conn.close()
            
        except Exception as e:
            print_error(f"Error limpiando: {e}")
    
    def run_complete_test(self):
        """Ejecuta todas las pruebas"""
        print_header("INICIANDO TEST COMPLETO DEL FLUJO")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'database': False,
            'setup': False,
            'config': False,
            'messages': False,
            'booking': False,
            'notification': False
        }
        
        try:
            # 0. Verificar base de datos
            results['database'] = self.check_database()
            
            # 1. Setup
            lead_id, conv_id = self.setup_test_data()
            results['setup'] = lead_id is not None
            
            if not results['setup']:
                print_error("Setup falló, abortando test")
                return results
            
            # 2. Verificar configuración
            config_results = self.test_configuration()
            results['config'] = any(config_results.values())
            
            # 3. Probar procesamiento de mensajes
            results['messages'] = self.test_message_processing(lead_id, conv_id)
            
            # 4. Probar agendamiento
            results['booking'] = self.test_appointment_booking(lead_id)
            
            # 5. Probar notificaciones
            results['notification'] = self.test_notification_service()
            
        finally:
            # 6. Limpiar
            self.cleanup()
        
        # Resumen final
        print_header("RESUMEN DE RESULTADOS")
        
        for test, passed in results.items():
            if passed:
                print_success(f"{test.upper()}: PASÓ")
            else:
                print_error(f"{test.upper()}: FALLÓ")
        
        total_passed = sum(results.values())
        total_tests = len(results)
        
        print(f"\n{Colors.BOLD}Total: {total_passed}/{total_tests} pruebas pasaron{Colors.ENDC}")
        
        if total_passed == total_tests:
            print_success("\nTODAS LAS PRUEBAS PASARON! El sistema esta funcionando correctamente.")
        else:
            print_warning(f"\n{total_tests - total_passed} pruebas fallaron. Revisa los logs arriba.")
        
        return results

def main():
    """Función principal"""
    test = CompleteFlowTest()
    results = test.run_complete_test()
    
    # Retornar código de salida apropiado
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()