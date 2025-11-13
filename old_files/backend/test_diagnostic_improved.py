"""
Script de Diagnóstico Mejorado - Lee y muestra el contenido real de los archivos
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

class ImprovedDiagnostic:
    def __init__(self):
        self.services_path = os.path.join('app', 'services')
        self.config_path = os.path.join('app', 'config')
        self.found_classes = {}
        
    def analyze_service_files(self):
        """Analiza detalladamente cada archivo de servicio"""
        print_header("ANÁLISIS DETALLADO DE ARCHIVOS DE SERVICIO")
        
        service_files = {
            'message_processor.py': 'MessageProcessor',
            'notification_service.py': 'NotificationService',
            'appointment_scheduler.py': 'AppointmentScheduler',
            'ai_service.py': 'AIService',
            'message_handler.py': 'MessageHandler'
        }
        
        for filename, expected_class in service_files.items():
            filepath = os.path.join(self.services_path, filename)
            
            if os.path.exists(filepath):
                print(f"\n📄 Analizando {filename}:")
                self.analyze_file_content(filepath, expected_class)
            else:
                print_error(f"Archivo no encontrado: {filename}")
    
    def analyze_file_content(self, filepath, expected_class):
        """Analiza el contenido de un archivo específico"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Buscar líneas que contengan 'class'
            lines = content.split('\n')
            class_definitions = []
            
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('class '):
                    # Extraer el nombre de la clase
                    class_line = line.strip()
                    if '(' in class_line:
                        class_name = class_line.split('class ')[1].split('(')[0].strip()
                    else:
                        class_name = class_line.split('class ')[1].split(':')[0].strip()
                    
                    class_definitions.append((i, class_name))
            
            if class_definitions:
                print_success(f"  Clases encontradas:")
                for line_num, class_name in class_definitions:
                    print(f"    - Línea {line_num}: {class_name}")
                    
                    # Verificar si es la clase esperada
                    if class_name == expected_class:
                        print_success(f"      ✓ Clase esperada '{expected_class}' encontrada")
                        self.found_classes[expected_class] = filepath
                    else:
                        print_warning(f"      ⚠ Se esperaba '{expected_class}' pero se encontró '{class_name}'")
            else:
                print_warning(f"  No se encontraron definiciones de clase")
                
            # Buscar las primeras líneas con contenido significativo
            print_info("  Primeras líneas con código:")
            code_lines_shown = 0
            for i, line in enumerate(lines[:50], 1):
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                    if 'import' in line or 'from' in line or 'class' in line or 'def' in line:
                        print(f"    Línea {i}: {line[:80]}")
                        code_lines_shown += 1
                        if code_lines_shown >= 5:
                            break
                            
        except Exception as e:
            print_error(f"  Error leyendo archivo: {e}")
    
    def test_imports(self):
        """Intenta importar las clases encontradas"""
        print_header("PRUEBA DE IMPORTACIÓN")
        
        imported = {}
        
        # Mapeo de nombres de archivo a rutas de importación
        file_to_module = {
            'message_processor.py': 'app.services.message_processor',
            'notification_service.py': 'app.services.notification_service',
            'appointment_scheduler.py': 'app.services.appointment_scheduler',
            'ai_service.py': 'app.services.ai_service',
            'message_handler.py': 'app.services.message_handler'
        }
        
        for filename, module_path in file_to_module.items():
            filepath = os.path.join(self.services_path, filename)
            if os.path.exists(filepath):
                print(f"\nIntentando importar desde {module_path}:")
                
                try:
                    # Intentar importación dinámica
                    exec_globals = {}
                    exec_locals = {}
                    exec(f"from {module_path} import *", exec_globals, exec_locals)
                    
                    # Ver qué se importó
                    imported_items = [key for key in exec_locals.keys() if not key.startswith('_')]
                    if imported_items:
                        print_success(f"  Importado exitosamente: {', '.join(imported_items)}")
                        for item in imported_items:
                            imported[item] = exec_locals[item]
                    else:
                        print_warning(f"  Módulo importado pero no se encontraron clases públicas")
                        
                except Exception as e:
                    print_error(f"  Error de importación: {e}")
        
        return imported
    
    def check_file_mix(self):
        """Verifica si los archivos están mezclados"""
        print_header("VERIFICACIÓN DE ARCHIVOS MEZCLADOS")
        
        # Revisar específicamente notification_service.py
        notif_path = os.path.join(self.services_path, 'notification_service.py')
        if os.path.exists(notif_path):
            print(f"\nRevisando notification_service.py en detalle:")
            try:
                with open(notif_path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_lines = [f.readline() for _ in range(20)]
                
                content_preview = ''.join(first_lines)
                
                if 'MessageProcessor' in content_preview:
                    print_error("  ⚠️ ARCHIVO MEZCLADO: notification_service.py contiene MessageProcessor")
                    print_warning("  Esto explica por qué no se puede importar NotificationService")
                    print_info("  SOLUCIÓN: El contenido de message_processor.py está en notification_service.py")
                elif 'NotificationService' in content_preview:
                    print_success("  ✓ notification_service.py parece contener NotificationService")
                else:
                    print_warning("  No se puede determinar el contenido")
                    
            except Exception as e:
                print_error(f"  Error leyendo archivo: {e}")
    
    def suggest_fixes(self):
        """Sugiere correcciones basadas en el análisis"""
        print_header("🔧 ACCIONES CORRECTIVAS SUGERIDAS")
        
        if 'NotificationService' not in self.found_classes:
            print("\n1. ARREGLAR notification_service.py:")
            print("   El archivo notification_service.py NO contiene la clase NotificationService")
            print("   Parece contener MessageProcessor en su lugar")
            print("   ACCIÓN: Necesitas el archivo correcto notification_service.py con la clase NotificationService")
            print("   que compartí anteriormente en la conversación")
        
        if 'MessageProcessor' not in self.found_classes:
            print("\n2. VERIFICAR message_processor.py:")
            print("   Asegúrate de que message_processor.py contiene la clase MessageProcessor")
            print("   Si el contenido está en notification_service.py, muévelo al archivo correcto")
        
        print("\n3. VERIFICACIÓN RÁPIDA:")
        print("   Abre notification_service.py y verifica que la primera clase sea:")
        print("   class NotificationService:")
        print("   NO debe ser: class MessageProcessor:")
    
    def run_complete_diagnostic(self):
        """Ejecuta el diagnóstico completo"""
        print_header("🔍 DIAGNÓSTICO DETALLADO DE ARCHIVOS")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Analizar archivos
        self.analyze_service_files()
        
        # 2. Probar importaciones
        imported = self.test_imports()
        
        # 3. Verificar archivos mezclados
        self.check_file_mix()
        
        # 4. Sugerir correcciones
        self.suggest_fixes()
        
        # Resumen
        print_header("📊 RESUMEN")
        print("\nCLASES ENCONTRADAS CORRECTAMENTE:")
        for class_name, filepath in self.found_classes.items():
            print(f"  ✓ {class_name} en {os.path.basename(filepath)}")
        
        if not self.found_classes:
            print("  ❌ No se encontraron las clases esperadas en los archivos correctos")
        
        print("\nCLASES IMPORTADAS EXITOSAMENTE:")
        for class_name in imported.keys():
            print(f"  ✓ {class_name}")
        
        if not imported:
            print("  ❌ No se pudieron importar clases")
        
        return len(self.found_classes) > 0, len(imported) > 0

def main():
    diagnostic = ImprovedDiagnostic()
    found, imported = diagnostic.run_complete_diagnostic()
    
    if not found:
        print_error("\n⚠️ PROBLEMA CRÍTICO: Los archivos no contienen las clases esperadas")
        print_warning("Necesitas restaurar los archivos correctos que compartí anteriormente")

if __name__ == "__main__":
    main()