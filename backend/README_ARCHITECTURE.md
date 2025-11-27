# 📚 DOCUMENTACIÓN DE ARQUITECTURA - BJJ ACADEMY BOT

**Versión:** 2.0 (MessageProcessor)
**Fecha:** 24/11/2025
**Status:** ✅ Producción

---

## 🚀 INICIO RÁPIDO

### Para Nuevos Desarrolladores:

1. **Lee primero:** [`MIGRATION_SUMMARY.md`](MIGRATION_SUMMARY.md)
   - Resumen de la migración MessageHandler → MessageProcessor
   - Cambios clave del sistema
   - Razones técnicas

2. **Entiende la arquitectura:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
   - Arquitectura completa del sistema
   - Servicios especializados
   - Flujo de procesamiento
   - Stack tecnológico

3. **Visualiza el sistema:** [`ARCHITECTURE_DIAGRAM.md`](ARCHITECTURE_DIAGRAM.md)
   - Diagramas ASCII visuales
   - Flujo de booking paso a paso
   - Componentes y sus relaciones

4. **Configuración de notificaciones:** [`CONFIGURACION_NOTIFICACIONES.md`](../CONFIGURACION_NOTIFICACIONES.md)
   - Sistema de notificaciones
   - Recordatorios automáticos
   - Fixes recientes

---

## 📖 ÍNDICE DE DOCUMENTACIÓN

### Arquitectura

| Documento | Descripción | Para quién |
|-----------|-------------|------------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Arquitectura completa y detallada | Desarrolladores nuevos |
| [`ARCHITECTURE_DIAGRAM.md`](ARCHITECTURE_DIAGRAM.md) | Diagramas visuales del sistema | Visual learners |
| [`MIGRATION_SUMMARY.md`](MIGRATION_SUMMARY.md) | Resumen de migración v2.0 | Todos los dev |

### Configuración

| Documento | Descripción | Para quién |
|-----------|-------------|------------|
| [`CONFIGURACION_NOTIFICACIONES.md`](../CONFIGURACION_NOTIFICACIONES.md) | Sistema de notificaciones | Ops, Configuración |
| [`.env.example`](../.env.example) | Variables de entorno | DevOps |
| [`QUICK_START.md`](QUICK_START.md) | Guía de inicio rápido | Nuevos dev |

### Testing

| Documento | Descripción | Para quién |
|-----------|-------------|------------|
| [`tests/README.md`](tests/README.md) | Guía de testing | QA, Developers |
| [`test_double_booking_fix.py`](test_double_booking_fix.py) | Test de doble booking | Developers |
| [`test_booking_notifications.py`](test_booking_notifications.py) | Test de notificaciones | Developers |

### Funcionalidades

| Documento | Descripción | Para quién |
|-----------|-------------|------------|
| [`../Docs/FUNCIONALIDADES_CHATBOT.md`](../Docs/FUNCIONALIDADES_CHATBOT.md) | Features del chatbot | Product, Stakeholders |
| [`RECORDATORIOS_README.md`](RECORDATORIOS_README.md) | Sistema de recordatorios | Developers |

---

## 🏗️ ARQUITECTURA EN 5 MINUTOS

### Flujo Básico:

```
Usuario (WhatsApp)
    ↓
Twilio Webhook
    ↓
Flask App (app/__init__.py)
    ↓
MessageProcessor ← ORQUESTADOR PRINCIPAL
    ↓
├── LeadManager         (Gestión de leads)
├── ConversationManager (Gestión de conversaciones)
├── IntentDetector     (Detección de intenciones)
├── AIService          (OpenAI GPT-4o-mini)
├── AppointmentScheduler (Agendamiento)
├── NotificationService (Notificaciones)
└── ReminderService    (Recordatorios)
    ↓
PostgreSQL + Redis + Twilio + OpenAI
```

### Principios de Diseño:

1. **Single Responsibility Principle** - Cada servicio una responsabilidad
2. **Dependency Injection** - Servicios inyectados en constructor
3. **Testabilidad** - Servicios mockables e independientes
4. **Orquestación** - MessageProcessor coordina, no ejecuta

---

## 🔑 COMPONENTES PRINCIPALES

### 1. MessageProcessor (Orquestador)
**Archivo:** [`app/services/message_processor.py`](app/services/message_processor.py)
**Responsabilidad:** Coordinar flujo de procesamiento de mensajes
**Status:** ✅ Activo (versión 2.0)

### 2. MessageHandler (Deprecated)
**Archivo:** [`app/services/message_handler.py`](app/services/message_handler.py)
**Status:** ⛔ DEPRECATED (mantener solo para tests legacy)
**Migración:** Completada 24/11/2025

### 3. Servicios Especializados
- **LeadManager:** CRUD de leads + lógica de negocio
- **ConversationManager:** CRUD de conversaciones + caché
- **IntentDetector:** Detección de intenciones sin IA
- **AIService:** Integración con OpenAI
- **AppointmentScheduler:** Agendamiento de clases
- **NotificationService:** Notificaciones al staff
- **ReminderService:** Recordatorios programados

---

## 🛠️ STACK TECNOLÓGICO

### Backend Core
```
Flask 3.0+          → Framework web
SQLAlchemy 2.0+     → ORM
PostgreSQL 14+      → Base de datos principal
Redis Cloud         → Caché + Queue
```

### Integraciones
```
OpenAI API          → GPT-4o-mini para conversaciones
Twilio API          → WhatsApp messaging
Celery              → Background tasks
```

### Testing
```
pytest              → Test framework
SQLite in-memory    → Tests unitarios (velocidad)
unittest.mock       → Mocking de servicios externos
```

---

## 📊 DATOS IMPORTANTES

### Base de Datos

**PostgreSQL:** `bjj_academy` (localhost:5432)

Tablas principales:
- `academies` - Configuración de academias
- `leads` - Prospectos interesados
- `conversations` - Conversaciones activas
- `messages` - Mensajes individuales
- `class_reminders` - Recordatorios programados

### Caché

**Redis Cloud:** Para historial de conversaciones
- TTL: 1 hora
- Mejora performance 20x

### APIs Externas

**OpenAI:**
- Modelo: gpt-4o-mini
- Max tokens: 1000
- Temperature: 0.7

**Twilio:**
- Sandbox WhatsApp: +1 (415) 523-8886
- Notificaciones a: +506-7015-0369

---

## 🧪 TESTING

### Ejecutar Tests:

```bash
# Test de doble booking (MessageProcessor)
python test_double_booking_fix.py

# Tests de notificaciones
python test_booking_notifications.py

# Todos los tests con pytest
pytest tests/

# Tests con coverage
pytest --cov=app tests/
```

### Resultado Esperado:
```
✓ 89+ tests pasando
✓ MessageProcessor funcionando
✓ Fix de doble booking verificado
```

---

## 🚦 ESTADO DEL SISTEMA

### ✅ Completado

- [x] Migración a MessageProcessor
- [x] Fix de doble booking
- [x] Sistema de notificaciones
- [x] Sistema de recordatorios
- [x] Integración con OpenAI GPT-4o-mini
- [x] Integración con Twilio WhatsApp
- [x] Caché con Redis Cloud
- [x] Migración a PostgreSQL
- [x] 89+ tests pasando
- [x] Documentación completa

### 🔄 En Progreso

- [ ] Migrar tests legacy a MessageProcessor
- [ ] Eliminar MessageHandler completamente
- [ ] Agregar monitoreo de performance

### 📋 Pendiente

- [ ] Dashboard analytics
- [ ] Sistema de reportes
- [ ] Multi-tenancy
- [ ] App móvil para staff

---

## 📞 CONFIGURACIÓN DE PRODUCCIÓN

### Variables de Entorno Requeridas:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_WHATSAPP_NUMBER=+14155238886

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/bjj_academy

# Redis Cloud
REDIS_URL=redis://default:password@host:port/0
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
```

### Iniciar Servidor:

```bash
# Desarrollo
python run.py

# Con logs detallados
FLASK_DEBUG=True python run.py

# Producción (con Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

### Iniciar Worker de Celery:

```bash
celery -A app.tasks.celery worker --loglevel=info
```

---

## 🔍 TROUBLESHOOTING

### Problema: "MessageHandler está deprecated"

**Solución:** Actualizar imports a MessageProcessor
```python
# INCORRECTO
from app.services.message_handler import MessageHandler

# CORRECTO
from app.services.message_processor import MessageProcessor
```

### Problema: Redis no conecta

**Verificar:**
1. `REDIS_URL` en `.env` está configurado
2. Redis Cloud está accesible
3. Credenciales son correctas

### Problema: Tests fallan con PostgreSQL

**Solución:** Tests deben usar SQLite in-memory
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
```

---

## 📚 RECURSOS ADICIONALES

### Links Útiles

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Celery Documentation](https://docs.celeryq.dev/)

### Contacto

**Academia:** BJJ Mingo
**Teléfono:** +506-7015-0369
**Email:** testingtoimp2025@gmail.com
**Ubicación:** Santo Domingo de Heredia, Costa Rica

---

## 🎯 GUÍA RÁPIDA POR ROL

### Soy un Nuevo Desarrollador
1. Lee [`MIGRATION_SUMMARY.md`](MIGRATION_SUMMARY.md)
2. Estudia [`ARCHITECTURE.md`](ARCHITECTURE.md)
3. Mira los diagramas en [`ARCHITECTURE_DIAGRAM.md`](ARCHITECTURE_DIAGRAM.md)
4. Ejecuta tests: `python test_double_booking_fix.py`
5. Inicia el servidor: `python run.py`

### Soy DevOps/Ops
1. Lee [`CONFIGURACION_NOTIFICACIONES.md`](../CONFIGURACION_NOTIFICACIONES.md)
2. Configura variables de entorno (`.env`)
3. Verifica PostgreSQL está corriendo
4. Verifica Redis Cloud está accesible
5. Inicia Celery worker

### Soy QA
1. Lee [`tests/README.md`](tests/README.md)
2. Ejecuta todos los tests: `pytest tests/`
3. Verifica test de doble booking
4. Realiza testing manual del flujo completo

### Soy Product Manager
1. Lee [`../Docs/FUNCIONALIDADES_CHATBOT.md`](../Docs/FUNCIONALIDADES_CHATBOT.md)
2. Revisa [`MIGRATION_SUMMARY.md`](MIGRATION_SUMMARY.md) sección "PRÓXIMOS PASOS"
3. Verifica el roadmap

---

**Sistema listo para producción! 🚀**

_Documentación completa • Arquitectura modular • Tests pasando • Listo para escalar_

---

**Última actualización:** 24/11/2025
**Versión de Documentación:** 2.0
