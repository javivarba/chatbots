# 🥋 BJJ Academy Bot

Sistema de chatbot inteligente para academias de Brazilian Jiu-Jitsu que automatiza la atención al cliente y gestión de leads a través de WhatsApp, Facebook e Instagram.

## 🎯 Features

- ✅ Respuestas automáticas inteligentes con IA (OpenAI/Claude)
- ✅ Gestión de leads y seguimiento automático
- ✅ Agendamiento de clases de prueba
- ✅ Multi-tenant (múltiples academias)
- ✅ Dashboard de analytics
- ✅ Integraciones con calendario (Cal.com/Google Calendar)

## 🛠️ Tech Stack

- **Backend**: Python 3.11+ / Flask
- **Database**: PostgreSQL
- **Cache**: Redis
- **Queue**: Celery
- **AI**: OpenAI GPT-3.5/4
- **Container**: Docker
- **Testing**: Pytest

## 🚀 Quick Start

### Prerequisitos

- Python 3.11+
- Docker Desktop
- Git

### Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/bjj-academy-bot.git
cd bjj-academy-bot
```

2. **Configurar ambiente virtual (Windows)**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

3. **Instalar dependencias**
```powershell
pip install -r backend\requirements.txt
```

4. **Configurar variables de entorno**
```powershell
copy backend\.env.example backend\.env
# Editar backend\.env con tus API keys
```

5. **Levantar servicios con Docker**
```powershell
docker-compose up -d postgres redis
```

6. **Inicializar base de datos**
```powershell
cd backend
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

7. **Ejecutar la aplicación**
```powershell
# Terminal 1 - Flask
flask run

# Terminal 2 - Celery Worker
celery -A app.celery_app worker --loglevel=info

# Terminal 3 - Celery Beat (opcional)
celery -A app.celery_app beat --loglevel=info
```

## 📊 Estructura del Proyecto

```
bjj-academy-bot/
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoints y webhooks
│   │   ├── models/        # Modelos de base de datos
│   │   ├── services/      # Lógica de negocio
│   │   └── utils/         # Utilidades
│   ├── tests/             # Tests unitarios e integración
│   ├── scripts/           # Scripts de utilidad
│   └── docs/              # Documentación adicional
├── docker-compose.yml     # Configuración Docker
├── README.md             # Este archivo
└── .gitignore           # Archivos ignorados por Git
```

## 🧪 Testing

```powershell
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration
```

## 📝 API Documentation

### Endpoints principales

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/whatsapp` | Recibe mensajes de WhatsApp |
| GET | `/api/v1/academies` | Lista academias |
| GET | `/api/v1/leads` | Lista leads |
| POST | `/api/v1/leads/{id}/schedule` | Agenda clase de prueba |
| GET | `/health` | Health check |

## 🔧 Configuración

### Variables de Entorno Principales

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | - |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | - |

## 📊 Modelo de Datos

### Academy (Multi-tenant)
- Información de la academia
- Configuración de integraciones
- Personalización de IA

### Lead
- Información de contacto
- Estado del lead
- Historial de conversaciones

### Conversation
- Mensajes
- Contexto
- Métricas

## 🚢 Deployment

### Docker

```powershell
docker-compose up --build
```

### Heroku

```bash
heroku create bjj-academy-bot
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
git push heroku main
```

## 📈 Monitoring

- **Logs**: Verificar en `logs/app.log`
- **Celery**: Monitor en `http://localhost:5555` (Flower)
- **Database**: pgAdmin en `http://localhost:5050`

## 🤝 Contributing

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 License

MIT License - ver LICENSE file para detalles

## 👥 Contacto

Tu Nombre - [@tu_twitter](https://twitter.com/tu_twitter)

Project Link: [https://github.com/tu-usuario/bjj-academy-bot](https://github.com/tu-usuario/bjj-academy-bot)

## 🙏 Acknowledgments

- OpenAI por la API de GPT
- Twilio por la integración de WhatsApp
- La comunidad de BJJ por la inspiración