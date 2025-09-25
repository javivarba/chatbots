#!/usr/bin/env python3
"""
Crear README.md profesional para el proyecto
"""

from pathlib import Path
from datetime import datetime

def create_readme():
    """Crear README.md completo"""
    
    # Determinar ruta
    current_path = Path.cwd()
    if current_path.name == 'backend':
        readme_path = current_path.parent / 'README.md'
    else:
        readme_path = current_path / 'README.md'
    
    print(f"📝 Creando README.md en: {readme_path}")
    
    readme_content = '''# BJJ Academy WhatsApp Bot 🥋

> Sistema automatizado de gestión de leads y agendamiento de clases para academias de Brazilian Jiu-Jitsu

## 📋 Descripción

Bot inteligente de WhatsApp que automatiza la atención al cliente, captura de leads y agendamiento de clases de prueba para academias de BJJ. Utiliza IA (OpenAI GPT-3.5) para respuestas naturales y cuenta con un dashboard administrativo completo.

## ✨ Características Principales

### 🤖 Bot de WhatsApp
- **Respuestas Inteligentes**: Integración con OpenAI GPT-3.5 para conversaciones naturales
- **Detección de Intenciones**: Identifica automáticamente interés en clases, precios, horarios
- **Multiidioma**: Responde en español de forma natural y contextual
- **Fallback Automático**: Respuestas predefinidas cuando OpenAI no está disponible

### 📊 Sistema de Leads
- **Captura Automática**: Cada conversación genera un lead en la base de datos
- **Scoring de Interés**: Califica leads del 1-10 según su interacción
- **Estados Dinámicos**: new → interested → scheduled → customer
- **Historial Completo**: Guarda todas las conversaciones

### 📅 Agendamiento Inteligente
- **Interpretación Natural**: Entiende "mañana a las 6pm", "lunes por la tarde", etc.
- **Horarios Configurables**: Lun-Vie: 7am, 12pm, 6pm, 8pm | Sáb: 9am, 11am
- **Validaciones**: Capacidad máxima, no duplicados, horarios válidos
- **Google Calendar**: Genera links para agregar citas al calendario personal

### 💼 Dashboard Administrativo
- **Estadísticas en Tiempo Real**: Total leads, interesados, agendados, tasa de conversión
- **Gestión de Leads**: Vista completa con historial de conversaciones
- **Control de Citas**: Confirmar, cancelar, ver citas del día
- **Auto-actualización**: Refresh automático cada 10 segundos

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Cuenta de Twilio (para WhatsApp)
- API Key de OpenAI (opcional pero recomendado)
- ngrok (para desarrollo local)

### Paso 1: Clonar el Repositorio
```bash
git clone [URL-de-tu-repositorio]
cd bjj-academy-bot
```

### Paso 2: Crear Entorno Virtual (Recomendado)
```bash
python -m venv venv

# En Windows:
venv\\Scripts\\activate

# En Mac/Linux:
source venv/bin/activate
```

### Paso 3: Instalar Dependencias
```bash
cd backend
pip install -r requirements.txt
```

### Paso 4: Configurar Variables de Entorno
```bash
# Crear archivo .env basado en el ejemplo
cp .env.example .env
```

Editar `.env` con tus credenciales:
```env
# OpenAI
OPENAI_API_KEY=sk-tu-api-key-aqui

# Twilio (para producción)
TWILIO_ACCOUNT_SID=tu-account-sid
TWILIO_AUTH_TOKEN=tu-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Flask
FLASK_ENV=development
SECRET_KEY=genera-una-clave-secreta-segura
```

### Paso 5: Iniciar el Servidor
```bash
python run.py
```
El servidor estará disponible en: `http://localhost:5000`

### Paso 6: Configurar ngrok (para WhatsApp)
En una terminal separada:
```bash
ngrok http 5000
```
Copia la URL HTTPS generada (ej: `https://abc123.ngrok.io`)

## 📱 Configuración de WhatsApp/Twilio

1. **Acceder a Twilio Console**
   - Ir a: https://console.twilio.com
   - Navegar a: Messaging → Try it out → WhatsApp

2. **Configurar Sandbox**
   - En "Sandbox Configuration"
   - **WHEN A MESSAGE COMES IN**: `https://tu-url-ngrok.ngrok.io`
   - **METHOD**: HTTP POST
   - Guardar configuración

3. **Conectar WhatsApp**
   - Enviar código de activación al número de Twilio
   - Generalmente: "join [palabra-código]"

## 💻 Uso del Sistema

### Para Usuarios (WhatsApp)
1. Enviar mensaje al número de WhatsApp configurado
2. Ejemplos de conversación:
   - "Hola, quiero información"
   - "¿Cuánto cuesta la mensualidad?"
   - "Quiero agendar una clase de prueba"
   - "Mañana a las 6pm"

### Para Administradores (Dashboard)
1. Acceder a: `http://localhost:5000/dashboard`
2. **Sección Estadísticas**: Ver métricas generales y leads
3. **Sección Citas**: Gestionar agendamientos
4. Click en "Ver Chat" para revisar conversaciones completas

## 🗂️ Estructura del Proyecto

```
bjj-academy-bot/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Configuración Flask
│   │   ├── api/
│   │   │   └── dashboard_routes.py  # Endpoints del dashboard
│   │   ├── services/
│   │   │   ├── message_handler.py   # Procesamiento de mensajes
│   │   │   └── appointment_scheduler.py  # Lógica de agendamiento
│   │   └── templates/
│   │       └── dashboard.html    # Interface del dashboard
│   ├── bjj_academy.db           # Base de datos SQLite
│   ├── requirements.txt         # Dependencias Python
│   ├── .env                     # Variables de entorno
│   └── run.py                   # Script principal
└── README.md                    # Este archivo
```

## 📊 Base de Datos

### Esquema Principal
- **academy**: Información de la academia
- **lead**: Datos de prospectos/clientes
- **conversation**: Sesiones de chat
- **message**: Mensajes individuales
- **appointment**: Citas agendadas
- **schedule_slots**: Horarios disponibles

## 🧪 Testing

### Prueba Básica
```bash
# 1. Verificar servidor
curl http://localhost:5000/health

# 2. Verificar API
curl http://localhost:5000/api/stats

# 3. Simular mensaje WhatsApp
curl -X POST http://localhost:5000/webhook/whatsapp \\
  -d "Body=Hola&From=whatsapp:+521234567890"
```

### Flujo de Prueba Completo
1. Enviar "Hola" por WhatsApp
2. Preguntar por precios
3. Agendar una clase
4. Verificar en dashboard
5. Confirmar/cancelar cita

## 🚀 Deployment

### Opción 1: Heroku
```bash
# Crear Procfile
echo "web: cd backend && python run.py" > Procfile

# Subir a Heroku
heroku create tu-app-name
git push heroku main
```

### Opción 2: Railway
1. Conectar repositorio GitHub
2. Configurar variables de entorno
3. Deploy automático

### Consideraciones de Producción
- Cambiar SQLite por PostgreSQL
- Configurar HTTPS/SSL
- Usar servicio de mensajería dedicado
- Implementar autenticación en dashboard
- Configurar backups automáticos

## 📈 Métricas del Proyecto

- **Leads Capturados**: 8
- **Conversaciones**: 8
- **Mensajes Procesados**: 30+
- **Citas Agendadas**: 3
- **Tasa de Conversión**: ~37%

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask (Python 3.8+)
- **Base de Datos**: SQLite (desarrollo), PostgreSQL (producción recomendado)
- **IA**: OpenAI GPT-3.5 Turbo
- **Mensajería**: Twilio WhatsApp Business API
- **Frontend**: HTML5, Tailwind CSS, JavaScript Vanilla
- **Herramientas**: ngrok, Git

## 📝 Variables de Entorno

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | API Key de OpenAI | Opcional* |
| `TWILIO_ACCOUNT_SID` | ID de cuenta Twilio | Sí |
| `TWILIO_AUTH_TOKEN` | Token de autenticación | Sí |
| `TWILIO_WHATSAPP_NUMBER` | Número WhatsApp | Sí |
| `FLASK_ENV` | Entorno (development/production) | No |
| `SECRET_KEY` | Clave secreta Flask | Sí |

*Si no se configura OpenAI, el bot usa respuestas predefinidas

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📞 Soporte

Para soporte, problemas o sugerencias:
- Crear un issue en GitHub
- Contactar al desarrollador

## 🏆 Características Futuras

- [ ] Integración con Google Calendar API
- [ ] Sistema de pagos en línea
- [ ] App móvil para instructores
- [ ] Análisis predictivo de deserción
- [ ] Multi-academia (SaaS)
- [ ] Recordatorios automáticos
- [ ] Integración con CRM

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

**Tu Nombre**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)
- LinkedIn: [tu-perfil](https://linkedin.com/in/tu-perfil)

## 🙏 Agradecimientos

- OpenAI por GPT-3.5
- Twilio por la API de WhatsApp
- Comunidad de Flask
- Academia BJJ por la oportunidad

---

**Desarrollado con ❤️ para BJJ Academy | Septiembre 2024**
'''
    
    # Guardar README
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ README.md creado exitosamente!")
    
    # Crear también .env.example
    create_env_example(readme_path.parent)
    
    # Crear requirements.txt actualizado
    create_requirements(readme_path.parent / 'backend')
    
    # Crear .gitignore
    create_gitignore(readme_path.parent)
    
    return True

def create_env_example(project_root):
    """Crear archivo .env.example"""
    
    env_example_path = project_root / 'backend' / '.env.example'
    
    env_content = '''# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production

# OpenAI Configuration (Optional but recommended)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///bjj_academy.db

# Application Settings
APP_NAME=BJJ Academy Bot
APP_VERSION=1.0.0
MAX_CONVERSATION_HISTORY=10
'''
    
    with open(env_example_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ .env.example creado")

def create_requirements(backend_path):
    """Crear requirements.txt actualizado"""
    
    req_path = backend_path / 'requirements.txt'
    
    requirements = '''Flask==2.3.3
flask-cors==4.0.0
python-dotenv==1.0.0
requests==2.31.0
twilio==8.5.0
openai==0.28.0
SQLAlchemy==2.0.20
colorama==0.4.6
Werkzeug==2.3.7
'''
    
    with open(req_path, 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    print(f"✅ requirements.txt actualizado")

def create_gitignore(project_root):
    """Crear .gitignore"""
    
    gitignore_path = project_root / '.gitignore'
    
    gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Flask
instance/
.webassets-cache

# Environment
.env
*.env

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Testing
.coverage
htmlcov/
.pytest_cache/

# Backups
*.backup
*.bak

# Old scripts
_old_scripts/

# Ngrok
ngrok.exe
ngrok
'''
    
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print(f"✅ .gitignore creado")

if __name__ == "__main__":
    print("="*60)
    print("CREANDO ARCHIVOS DE DOCUMENTACIÓN")
    print("="*60)
    
    if create_readme():
        print("\n" + "="*60)
        print("✅ DOCUMENTACIÓN CREADA")
        print("="*60)
        
        print("\n📁 Archivos creados:")
        print("  • README.md")
        print("  • .env.example")
        print("  • requirements.txt")
        print("  • .gitignore")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("\n1. Actualiza el README con tu información:")
        print("   - Tu nombre y contacto")
        print("   - URL del repositorio")
        print("   - Información de la academia")
        
        print("\n2. Sube a GitHub:")
        print("   git add .")
        print("   git commit -m 'feat: BJJ Academy WhatsApp Bot - Sistema completo'")
        print("   git checkout -b production")
        print("   git push origin production")
        
        print("\n3. Graba video de demostración mostrando:")
        print("   - Conversación por WhatsApp")
        print("   - Agendamiento de clase")
        print("   - Dashboard administrativo")
        
        print("\n✨ PROYECTO LISTO PARA ENTREGAR!")