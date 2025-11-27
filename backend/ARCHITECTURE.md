# 🏗️ ARQUITECTURA DEL SISTEMA - BJJ ACADEMY BOT

**Fecha de migración:** 24/11/2025
**Arquitectura:** Modular con Single Responsibility Principle (SRP)
**Orquestador principal:** MessageProcessor

---

## 📋 TABLA DE CONTENIDOS

1. [Visión General](#vision-general)
2. [Arquitectura de Servicios](#arquitectura-de-servicios)
3. [Flujo de Procesamiento de Mensajes](#flujo-de-procesamiento-de-mensajes)
4. [Servicios Especializados](#servicios-especializados)
5. [Migración de MessageHandler](#migracion-de-messagehandler)
6. [Stack Tecnológico](#stack-tecnologico)

---

## 🎯 VISIÓN GENERAL

El sistema está diseñado con arquitectura modular donde cada servicio tiene **una sola responsabilidad** (Single Responsibility Principle).

### Principios de Diseño

1. **Separación de Responsabilidades**: Cada servicio maneja un aspecto específico
2. **Dependency Injection**: Los servicios se inyectan en el constructor
3. **Orquestación Centralizada**: MessageProcessor coordina todos los servicios
4. **Testabilidad**: Servicios fácilmente mockables e independientes
5. **Escalabilidad**: Nuevos servicios se agregan sin modificar existentes

---

## 🏛️ ARQUITECTURA DE SERVICIOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    TWILIO WEBHOOK (Flask)                       │
│                    app/__init__.py:root()                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE PROCESSOR                            │
│              (Orquestador Principal)                            │
│                                                                 │
│  Responsabilidad:                                               │
│  - Coordinar flujo de procesamiento                            │
│  - Delegar a servicios especializados                          │
│  - NO contiene lógica de negocio                               │
│                                                                 │
│  Archivo: app/services/message_processor.py                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ LeadManager  │  │ Conversation │  │   Intent     │
│              │  │   Manager    │  │  Detector    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  AIService   │  │  Appointment │  │ Notification │
│              │  │   Scheduler  │  │   Service    │
└──────────────┘  └──────┬───────┘  └──────────────┘
                         │
                         ↓
                  ┌──────────────┐
                  │   Reminder   │
                  │   Service    │
                  └──────────────┘
```

---

## 🔄 FLUJO DE PROCESAMIENTO DE MENSAJES

### Flujo Completo (Paso a Paso)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. WEBHOOK RECIBE MENSAJE DE WHATSAPP                          │
│    - Twilio envía POST a http://localhost:5000/                │
│    - Extrae: phone_number, message, profile_name               │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. MESSAGE PROCESSOR - process_message()                       │
│    Orquesta todo el flujo                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. LEAD MANAGER - get_or_create()                              │
│    - Busca lead por teléfono                                   │
│    - Si no existe → crea nuevo con status=NEW                  │
│    - Si existe → retorna lead_id                               │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. INTENT DETECTOR - detect_name()                             │
│    - Analiza si el mensaje contiene un nombre                  │
│    - Patrones: "mi nombre es X", "me llamo X", etc.           │
│    - Si detecta → actualiza lead.name                          │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. CONVERSATION MANAGER - get_or_create()                      │
│    - Busca conversación activa para el lead                    │
│    - Si no existe → crea nueva conversación                    │
│    - Retorna conversation_id                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. CONVERSATION MANAGER - save_message(INBOUND)                │
│    - Guarda mensaje del usuario en BD                          │
│    - Direction: INBOUND                                        │
│    - Content: mensaje original                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. AI SERVICE - generate_response()                            │
│    - Obtiene historial de conversación (últimos 5 mensajes)   │
│    - Construye system prompt con info de academy              │
│    - Llama a OpenAI GPT-4o-mini                                │
│    - Retorna respuesta generada                                │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. INTENT DETECTOR - detect_booking_intent()                   │
│    - Analiza mensaje + respuesta + historial                  │
│    - Detecta palabras clave: "agendar", "reservar", días, etc.│
│    - Retorna: True/False                                       │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
                     [¿Booking detectado?]
                          │
                ┌─────────┴─────────┐
                │                   │
               Sí                  No
                │                   │
                ↓                   ↓
┌────────────────────────┐  ┌──────────────────┐
│ 9a. APPOINTMENT        │  │ 9b. Retornar     │
│     SCHEDULER          │  │     respuesta AI │
│                        │  └──────────────────┘
│ - parse_appointment()  │
│ - book_trial_week()    │
│                        │
│ ¿Success?              │
│   │                    │
│   ├─ Sí → Notificar   │
│   │       + Recordar  │
│   │                    │
│   └─ No → Error msg   │
└────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. CONVERSATION MANAGER - save_message(OUTBOUND)              │
│     - Guarda respuesta del bot en BD                           │
│     - Direction: OUTBOUND                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 11. LEAD MANAGER - update_status()                             │
│     - Actualiza status según keywords en mensaje               │
│     - NEW → CONTACTED → INTERESTED → SCHEDULED → etc.          │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 12. RETORNAR RESPUESTA A TWILIO                                │
│     - Flask devuelve TwiML con mensaje                         │
│     - Twilio envía WhatsApp al usuario                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 SERVICIOS ESPECIALIZADOS

### 1. MessageProcessor
**Archivo:** [`app/services/message_processor.py`](app/services/message_processor.py)
**Responsabilidad:** Orquestar el flujo completo de procesamiento

**Métodos principales:**
- `process_message(phone, message, name)` - Flujo completo
- `_generate_ai_response()` - Generar respuesta + detectar booking
- `_get_emergency_response()` - Respuesta de fallback

**Dependencias:**
- LeadManager
- ConversationManager
- IntentDetector
- AIService
- AppointmentScheduler

---

### 2. LeadManager
**Archivo:** [`app/services/lead_manager.py`](app/services/lead_manager.py)
**Responsabilidad:** Gestión de leads (CRUD + lógica de negocio)

**Métodos principales:**
- `get_or_create(phone, name)` - Obtener o crear lead
- `update_name(lead_id, name)` - Actualizar nombre
- `update_status(lead_id, message)` - Actualizar status según keywords
- `update_score(lead_id, points)` - Actualizar puntaje

**Modelo:** Lead (PostgreSQL)

---

### 3. ConversationManager
**Archivo:** [`app/services/conversation_manager.py`](app/services/conversation_manager.py)
**Responsabilidad:** Gestión de conversaciones y mensajes

**Métodos principales:**
- `get_or_create(lead_id)` - Obtener o crear conversación
- `save_message(conv_id, direction, content)` - Guardar mensaje
- `get_history(conv_id, limit)` - Obtener historial con caché
- `close_conversation(conv_id)` - Cerrar conversación

**Modelos:** Conversation, Message (PostgreSQL)
**Caché:** Redis Cloud

---

### 4. IntentDetector
**Archivo:** [`app/services/intent_detector.py`](app/services/intent_detector.py)
**Responsabilidad:** Detectar intenciones del usuario (sin IA)

**Métodos principales:**
- `detect_booking_intent(msg, response, history)` - Detectar agendamiento
- `detect_name(message)` - Extraer nombre del mensaje
- `_extract_day_from_message(message)` - Extraer día mencionado
- `_extract_time_from_message(message)` - Extraer hora mencionada

**Técnica:** Regex + Keywords (sin consumir API de OpenAI)

---

### 5. AIService
**Archivo:** [`app/services/ai_service.py`](app/services/ai_service.py)
**Responsabilidad:** Integración con OpenAI para respuestas conversacionales

**Métodos principales:**
- `generate_response(message, lead, conv, academy)` - Generar respuesta
- `_build_system_prompt(academy, lead)` - Construir contexto
- `_get_conversation_history(conversation)` - Formatear historial

**API:** OpenAI GPT-4o-mini
**Configuración:** 1000 max tokens, temperature 0.7

---

### 6. AppointmentScheduler
**Archivo:** [`app/services/appointment_scheduler.py`](app/services/appointment_scheduler.py)
**Responsabilidad:** Gestión de agendamiento de clases de prueba

**Métodos principales:**
- `book_trial_week(lead_id, clase_tipo, notes)` - Agendar semana
- `parse_appointment_request(message, lead_id)` - Parsear fecha/hora
- `_validate_trial_week_availability()` - Validar disponibilidad

**Protecciones:**
- ✅ Prevención de doble booking
- ✅ Validación de horarios
- ✅ Notificación automática al staff

**Integraciones:**
- NotificationService (notificar a academia)
- ReminderService (programar recordatorios)
- Celery (tareas asíncronas)

---

### 7. NotificationService
**Archivo:** [`app/services/notification_service.py`](app/services/notification_service.py)
**Responsabilidad:** Envío de notificaciones al staff de la academia

**Métodos principales:**
- `notify_new_trial_booking(lead_info, trial_info)` - Notificar booking
- `_send_whatsapp_notification(to, message)` - Enviar WhatsApp
- `_send_email_notification()` - Enviar email (fallback)

**Destinatarios:**
- WhatsApp primario: +506-7015-0369
- WhatsApp secundario: +506-8888-8888 (backup)
- Email: testingtoimp2025@gmail.com (fallback)

**API:** Twilio WhatsApp

---

### 8. ReminderService
**Archivo:** [`app/services/reminder_service.py`](app/services/reminder_service.py)
**Responsabilidad:** Gestión de recordatorios programados

**Métodos principales:**
- `schedule_trial_week_reminders(lead_id, clase_tipo, start_date)` - Programar
- `send_reminder(reminder_id)` - Enviar recordatorio
- `get_pending_reminders()` - Obtener pendientes

**Modelo:** ClassReminder (PostgreSQL)
**Queue:** Celery + Redis Cloud

---

## 🔄 FLUJO DE PROCESAMIENTO DE MENSAJES

### Código en MessageProcessor.process_message()

```python
def process_message(self, phone_number: str, message: str, name: Optional[str] = None) -> str:
    """
    1. Gestionar lead
       - LeadManager.get_or_create(phone, name)
       - Crea nuevo o retorna existente

    2. Detectar nombre
       - IntentDetector.detect_name(message)
       - Si encuentra nombre → LeadManager.update_name()

    3. Gestionar conversación
       - ConversationManager.get_or_create(lead_id)
       - Crea nueva o retorna activa

    4. Guardar mensaje entrante
       - ConversationManager.save_message(INBOUND)
       - Persiste en PostgreSQL

    5. Generar respuesta con IA
       - AIService.generate_response()
       - OpenAI GPT-4o-mini + historial

    6. Detectar intención de agendamiento
       - IntentDetector.detect_booking_intent()
       - Si detecta → AppointmentScheduler.book_trial_week()
       - Si falla → Retornar mensaje de error apropiado

    7. Guardar respuesta del bot
       - ConversationManager.save_message(OUTBOUND)

    8. Actualizar status del lead
       - LeadManager.update_status()
       - NEW → CONTACTED → INTERESTED → SCHEDULED

    9. Retornar respuesta
       - Flask → Twilio → WhatsApp usuario
    """
```

---

## 🔧 MIGRACIÓN DE MESSAGEHANDLER

### ⚠️ MessageHandler → MessageProcessor

**Fecha:** 24/11/2025

**Razón de la migración:**
- MessageHandler tenía lógica duplicada con otros servicios
- Difícil de mantener y testear
- No seguía principio de responsabilidad única
- Código repetido entre message_handler y message_processor

**Cambios realizados:**

1. ✅ **MessageProcessor actualizado** con fix de doble booking
2. ✅ **app/__init__.py migrado** a usar MessageProcessor
3. ✅ **MessageHandler marcado como DEPRECATED**
4. ✅ **Tests migrados** a usar MessageProcessor
5. ⚠️ **Tests antiguos** mantienen MessageHandler temporalmente

**Archivo deprecated:** [`app/services/message_handler.py`](app/services/message_handler.py)

**Estado:**
- ⛔ NO usar en nuevos desarrollos
- ✅ Se mantiene solo para tests legacy
- 📅 Se eliminará cuando todos los tests migren

---

## 🛠️ STACK TECNOLÓGICO

### Backend
- **Framework:** Flask 3.0+
- **ORM:** SQLAlchemy 2.0+
- **Base de datos:** PostgreSQL 14+
- **Caché:** Redis Cloud
- **Queue:** Celery + Redis

### Integraciones
- **IA:** OpenAI GPT-4o-mini
- **WhatsApp:** Twilio API
- **Mensajería:** Twilio WhatsApp Sandbox

### Infraestructura
- **OS:** Windows (desarrollo)
- **Python:** 3.13
- **Encoding:** UTF-8 (configurado para Windows)

---

## 📊 MODELOS DE DATOS

### Academy
- Configuración de la academia
- Horarios, precios, clases
- 1 academy por instalación

### Lead
- Prospectos interesados
- Status: NEW → CONTACTED → INTERESTED → SCHEDULED → CONVERTED
- Relación: academy_id (FK)

### Conversation
- Conversaciones activas con leads
- is_active flag
- Relación: lead_id (FK)

### Message
- Mensajes individuales (INBOUND/OUTBOUND)
- Relación: conversation_id (FK)
- Caché en Redis

### ClassReminder
- Recordatorios programados para leads
- Status: PENDING → SENT → FAILED
- send_at: timestamp para envío
- Procesado por Celery cada hora

---

## 🧪 TESTING

### Estrategia de Testing

**Unit Tests:**
- SQLite in-memory para velocidad
- Mocks para servicios externos (Twilio, OpenAI)
- Tests aislados por servicio

**Integration Tests:**
- PostgreSQL real (desarrollo)
- Tests de flujo completo
- Sin mocks de base de datos

**Archivos de test:**
- `test_double_booking_fix.py` - Verifica fix de doble booking
- `test_booking_notifications.py` - Sistema de notificaciones
- `tests/test_lead_manager.py` - CRUD de leads
- `tests/test_conversation_manager.py` - CRUD de conversaciones
- `tests/test_intent_detector.py` - Detección de intenciones

**Total:** 89+ tests pasando

---

## 🔐 VARIABLES DE ENTORNO

**Archivo:** `.env` (NO commitear)

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_WHATSAPP_NUMBER=+14155238886

# PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/bjj_academy

# Redis Cloud
REDIS_URL=redis://default:password@host:port/0
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
```

---

## 🚀 PRÓXIMOS PASOS

1. **Migrar tests legacy** de MessageHandler a MessageProcessor
2. **Eliminar MessageHandler** una vez que todos los tests migren
3. **Crear tests end-to-end** del flujo completo
4. **Agregar monitoreo** de performance de servicios
5. **Documentar APIs** de cada servicio

---

## 📞 CONTACTO Y CONFIGURACIÓN

**Academia:** BJJ Mingo
**Teléfono:** +506-7015-0369
**Email:** testingtoimp2025@gmail.com
**Ubicación:** Santo Domingo de Heredia, Costa Rica

---

**Última actualización:** 24/11/2025
**Versión:** 2.0 (MessageProcessor)
