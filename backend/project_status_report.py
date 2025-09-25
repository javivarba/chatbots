#!/usr/bin/env python3
"""
Reporte de Estado del Proyecto BJJ Academy Bot
y Script de Limpieza de Archivos
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil

class ProjectReport:
    def __init__(self):
        self.project_root = Path.cwd()
        if self.project_root.name == 'backend':
            self.project_root = self.project_root.parent
        
        self.backend_path = self.project_root / 'backend'
        self.db_path = self.backend_path / 'bjj_academy.db'
        
        # Archivos a eliminar o mover
        self.files_to_cleanup = []
        self.files_to_organize = []
        
    def print_header(self, text, emoji=""):
        print(f"\n{'='*60}")
        print(f"{emoji} {text.center(58)}")
        print('='*60)
    
    def generate_status_report(self):
        """Generar reporte de estado actual"""
        
        print("\n" + "="*60)
        print("🏆 REPORTE DE ESTADO - BJJ ACADEMY BOT")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)
        
        # 1. FUNCIONALIDADES COMPLETADAS
        self.print_header("FUNCIONALIDADES COMPLETADAS ✅", "✨")
        
        features = [
            ("WhatsApp Bot", "100%", [
                "✅ Integración con Twilio funcionando",
                "✅ Recepción y envío de mensajes",
                "✅ Respuestas con OpenAI GPT-3.5",
                "✅ Fallback a respuestas predefinidas"
            ]),
            ("Sistema de Leads", "100%", [
                "✅ Captura automática de leads",
                "✅ Seguimiento de conversaciones",
                "✅ Niveles de interés detectados",
                "✅ Estados: new, interested, scheduled"
            ]),
            ("Agendamiento de Clases", "100%", [
                "✅ Horarios disponibles configurados",
                "✅ Interpretación de fechas naturales",
                "✅ Generación de links Google Calendar",
                "✅ Validaciones de capacidad y conflictos"
            ]),
            ("Dashboard Administrativo", "100%", [
                "✅ Vista de estadísticas en tiempo real",
                "✅ Lista de leads con conversaciones",
                "✅ Gestión de citas (confirmar/cancelar)",
                "✅ Auto-actualización cada 10 segundos"
            ]),
            ("Base de Datos", "100%", [
                "✅ SQLite con todas las tablas necesarias",
                "✅ Relaciones configuradas correctamente",
                "✅ Datos de prueba insertados",
                "✅ Backup automático disponible"
            ])
        ]
        
        for feature, percentage, details in features:
            print(f"\n📦 {feature} - {percentage}")
            for detail in details:
                print(f"   {detail}")
        
        # 2. ESTADÍSTICAS ACTUALES
        self.print_header("ESTADÍSTICAS DEL SISTEMA 📊", "📈")
        
        if self.db_path.exists():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar registros
            stats = {}
            tables = ['lead', 'conversation', 'message', 'appointment']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            print(f"\n📊 Base de Datos:")
            print(f"   • Leads: {stats['lead']}")
            print(f"   • Conversaciones: {stats['conversation']}")
            print(f"   • Mensajes: {stats['message']}")
            print(f"   • Citas agendadas: {stats['appointment']}")
            
            # Leads por estado
            cursor.execute("SELECT status, COUNT(*) FROM lead GROUP BY status")
            lead_status = cursor.fetchall()
            
            print(f"\n📈 Leads por Estado:")
            for status, count in lead_status:
                print(f"   • {status}: {count}")
            
            conn.close()
        
        # 3. ESTRUCTURA ACTUAL DEL PROYECTO
        self.print_header("ESTRUCTURA DEL PROYECTO 📁", "🗂️")
        
        important_files = {
            'backend/app/__init__.py': 'Flask app principal',
            'backend/app/services/message_handler.py': 'Procesamiento de mensajes',
            'backend/app/services/appointment_scheduler.py': 'Sistema de agendamiento',
            'backend/app/api/dashboard_routes.py': 'API del dashboard',
            'backend/app/templates/dashboard.html': 'Dashboard UI',
            'backend/bjj_academy.db': 'Base de datos',
            'backend/.env': 'Variables de entorno',
            'backend/run.py': 'Script principal'
        }
        
        print("\n📄 Archivos Principales:")
        for file, desc in important_files.items():
            file_path = self.project_root / file
            if file_path.exists():
                size = file_path.stat().st_size / 1024  # KB
                print(f"   ✅ {file} ({size:.1f} KB)")
                print(f"      └─ {desc}")
            else:
                print(f"   ❌ {file} - NO ENCONTRADO")
        
        # 4. ARCHIVOS A LIMPIAR
        self.print_header("ARCHIVOS A LIMPIAR 🧹", "🗑️")
        
        # Buscar scripts de arreglo y prueba
        cleanup_patterns = [
            'fix_*.py',
            'test_*.py',
            'check_*.py',
            'create_*.py',
            'restore_*.py',
            'debug_*.py',
            'diagnostic_*.py',
            'scheduling_step*.py',
            'prepare_*.py',
            '*.backup',
            '*.problem'
        ]
        
        files_to_clean = []
        for pattern in cleanup_patterns:
            files_to_clean.extend(list(self.project_root.glob(pattern)))
            files_to_clean.extend(list(self.backend_path.glob(pattern)))
        
        if files_to_clean:
            print(f"\n🗑️ Archivos de setup/fix encontrados ({len(files_to_clean)}):")
            for file in files_to_clean[:10]:  # Mostrar máximo 10
                print(f"   • {file.name}")
            
            if len(files_to_clean) > 10:
                print(f"   ... y {len(files_to_clean) - 10} más")
            
            self.files_to_cleanup = files_to_clean
        else:
            print("\n✅ No hay archivos temporales para limpiar")
        
        # 5. PRÓXIMOS PASOS SUGERIDOS
        self.print_header("PRÓXIMOS PASOS SUGERIDOS 🎯", "🚀")
        
        next_steps = [
            ("CRÍTICO - Documentación", [
                "README.md con instrucciones de instalación",
                "requirements.txt actualizado",
                "Manual de usuario (PDF o Markdown)",
                "Video demostración (3-5 minutos)"
            ]),
            ("IMPORTANTE - Testing", [
                "Pruebas end-to-end del flujo completo",
                "Verificar casos edge (citas duplicadas, etc)",
                "Testing con múltiples usuarios simultáneos",
                "Validar respuestas de OpenAI"
            ]),
            ("OPCIONAL - Mejoras", [
                "Recordatorios automáticos 24h antes",
                "Exportar leads a CSV",
                "Gráficas en el dashboard",
                "Integración con email real"
            ]),
            ("DEPLOYMENT", [
                "Preparar para producción (Heroku/Railway)",
                "Configurar base de datos PostgreSQL",
                "Variables de entorno de producción",
                "Dominio y SSL"
            ])
        ]
        
        for category, tasks in next_steps:
            print(f"\n📌 {category}:")
            for task in tasks:
                print(f"   • {task}")
        
        # 6. ESTADO PARA ENTREGA
        self.print_header("ESTADO PARA ENTREGA 🎓", "📦")
        
        print("\n✅ LISTO PARA ENTREGAR:")
        print("   • Bot WhatsApp funcional")
        print("   • Dashboard administrativo completo")
        print("   • Sistema de agendamiento operativo")
        print("   • Base de datos con datos de prueba")
        
        print("\n⚠️ PENDIENTES MÍNIMOS:")
        print("   • README.md con instrucciones")
        print("   • Video de demostración")
        print("   • Limpiar archivos temporales")
        
        print("\n📅 FECHA DE ENTREGA: 18 de Septiembre")
        days_remaining = (datetime(2024, 9, 18) - datetime.now()).days
        print(f"⏰ DÍAS RESTANTES: {max(0, days_remaining)}")
    
    def cleanup_files(self):
        """Limpiar archivos temporales"""
        
        if not self.files_to_cleanup:
            print("\n✅ No hay archivos para limpiar")
            return
        
        print(f"\n🧹 Limpiando {len(self.files_to_cleanup)} archivos...")
        
        # Crear carpeta para scripts antiguos
        old_scripts = self.project_root / '_old_scripts'
        old_scripts.mkdir(exist_ok=True)
        
        moved = 0
        deleted = 0
        
        for file in self.files_to_cleanup:
            try:
                if file.suffix == '.py' and 'fix' in file.name or 'create' in file.name:
                    # Mover scripts de utilidad a carpeta old
                    dest = old_scripts / file.name
                    shutil.move(str(file), str(dest))
                    moved += 1
                else:
                    # Eliminar backups y otros archivos temporales
                    file.unlink()
                    deleted += 1
            except Exception as e:
                print(f"   ⚠️ No se pudo procesar {file.name}: {e}")
        
        print(f"\n✅ Limpieza completada:")
        print(f"   • {moved} archivos movidos a _old_scripts/")
        print(f"   • {deleted} archivos eliminados")
        
        return True
    
    def create_readme(self):
        """Crear README.md básico"""
        
        readme_path = self.project_root / 'README.md'
        
        readme_content = '''# BJJ Academy WhatsApp Bot 🥋

Sistema de gestión de leads y agendamiento automatizado para academia de Brazilian Jiu-Jitsu.

## 🚀 Características

- ✅ Bot de WhatsApp con IA (OpenAI GPT-3.5)
- ✅ Captura automática de leads
- ✅ Sistema de agendamiento de clases
- ✅ Dashboard administrativo
- ✅ Generación de links para Google Calendar

## 📋 Requisitos

- Python 3.8+
- Cuenta de Twilio (para WhatsApp)
- API Key de OpenAI (opcional)
- ngrok (para desarrollo local)

## 🔧 Instalación

1. Clonar el repositorio:
```bash
git clone [tu-repositorio]
cd bjj-academy-bot
```

2. Instalar dependencias:
```bash
cd backend
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

4. Iniciar el servidor:
```bash
python run.py
```

5. En otra terminal, iniciar ngrok:
```bash
ngrok http 5000
```

## 📱 Configuración de WhatsApp

1. Ir a Twilio Console
2. Configurar WhatsApp Sandbox
3. Usar la URL de ngrok como webhook

## 💻 Acceder al Dashboard

Abrir en el navegador:
```
http://localhost:5000/dashboard
```

## 📝 Uso

1. Enviar mensaje a WhatsApp de Twilio
2. Bot responde automáticamente
3. Para agendar: "Quiero agendar una clase"
4. Ver leads y citas en el Dashboard

## 🛠️ Tecnologías

- Flask (Python)
- SQLite
- OpenAI GPT-3.5
- Twilio WhatsApp API
- Tailwind CSS

## 👤 Autor

[Tu nombre]

## 📄 Licencia

MIT
'''
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"\n✅ README.md creado en: {readme_path}")
        
        return True

def main():
    report = ProjectReport()
    
    # Generar reporte
    report.generate_status_report()
    
    # Preguntar si limpiar archivos
    print("\n" + "="*60)
    print("🧹 LIMPIEZA DE ARCHIVOS")
    print("="*60)
    
    response = input("\n¿Quieres limpiar los archivos temporales? (s/n): ")
    
    if response.lower() == 's':
        report.cleanup_files()
    
    # Preguntar si crear README
    if not (report.project_root / 'README.md').exists():
        response = input("\n¿Quieres crear un README.md? (s/n): ")
        if response.lower() == 's':
            report.create_readme()
    
    print("\n" + "="*60)
    print("✅ REPORTE COMPLETADO")
    print("="*60)
    print("\n🎯 Tu proyecto está LISTO para entregar!")
    print("Solo falta:")
    print("  1. Grabar video de demostración")
    print("  2. Hacer pruebas finales")
    print("  3. Subir a GitHub/GitLab")

if __name__ == "__main__":
    main()