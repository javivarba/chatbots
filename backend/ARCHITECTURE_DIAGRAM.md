# 📐 DIAGRAMA DE ARQUITECTURA - BJJ ACADEMY BOT

## 🎯 ARQUITECTURA COMPLETA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USUARIO FINAL (WhatsApp)                           │
│                                    👤                                       │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TWILIO WHATSAPP API                               │
│                                   ☁️                                        │
│                                                                             │
│  - Recibe mensajes de WhatsApp                                             │
│  - Envía POST a webhook                                                    │
│  - Envía respuestas a usuarios                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLASK APPLICATION                                    │
│                      (app/__init__.py)                                      │
│                                                                             │
│  Endpoints:                                                                 │
│  ┌─────────────────────────────────────────────────┐                       │
│  │ POST /                 → Webhook principal      │                       │
│  │ POST /webhook/whatsapp → Webhook alternativo    │                       │
│  │ GET  /health          → Health check           │                       │
│  │ GET  /dashboard       → Dashboard admin        │                       │
│  │ GET  /api/*           → API REST               │                       │
│  └─────────────────────────────────────────────────┘                       │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MESSAGE PROCESSOR                                  │
│                    (Orquestador Principal)                                  │
│                 app/services/message_processor.py                           │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  process_message(phone_number, message, name)                      │    │
│  │                                                                     │    │
│  │  1. Gestionar Lead        → LeadManager                            │    │
│  │  2. Detectar Nombre       → IntentDetector                         │    │
│  │  3. Gestionar Conversación→ ConversationManager                    │    │
│  │  4. Guardar Mensaje       → ConversationManager                    │    │
│  │  5. Generar Respuesta IA  → AIService                              │    │
│  │  6. Detectar Booking      → IntentDetector + AppointmentScheduler  │    │
│  │  7. Guardar Respuesta     → ConversationManager                    │    │
│  │  8. Actualizar Status     → LeadManager                            │    │
│  │  9. Retornar Respuesta                                             │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┘
              │             │             │             │
      ┌───────┴──────┐ ┌───┴────┐ ┌──────┴──────┐ ┌───┴────────┐
      │              │ │        │ │             │ │            │
      ↓              ↓ ↓        ↓ ↓             ↓ ↓            ↓
┌─────────────┐ ┌──────────────────┐ ┌──────────────┐ ┌─────────────────┐
│             │ │                  │ │              │ │                 │
│ LeadManager │ │ Conversation     │ │   Intent     │ │   AIService     │
│             │ │    Manager       │ │  Detector    │ │                 │
│             │ │                  │ │              │ │                 │
└──────┬──────┘ └────────┬─────────┘ └──────┬───────┘ └────────┬────────┘
       │                 │                  │                  │
       │                 │                  │                  │
       ↓                 ↓                  ↓                  ↓
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│                    CAPA DE PERSISTENCIA                            │
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL     │  │   Redis Cloud    │  │   SQLAlchemy    │ │
│  │                  │  │                  │  │                 │ │
│  │  - academies     │  │  - conversation  │  │  - ORM          │ │
│  │  - leads         │  │    cache         │  │  - Migrations   │ │
│  │  - conversations │  │  - session data  │  │  - Models       │ │
│  │  - messages      │  │                  │  │                 │ │
│  │  - class_reminders│  │                  │  │                 │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
       ↑                 ↑                  ↑
       │                 │                  │
       └─────────────────┴──────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    SERVICIOS EXTERNOS                               │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │   OpenAI API     │  │   Twilio API     │  │   Celery +      │  │
│  │                  │  │                  │  │   Redis Queue   │  │
│  │  - GPT-4o-mini   │  │  - WhatsApp Send │  │                 │  │
│  │  - Chat          │  │  - SMS Fallback  │  │  - Reminders    │  │
│  │  - Embeddings    │  │                  │  │  - Background   │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLUJO DE BOOKING DE CLASE DE PRUEBA

```
┌──────────────────────────────────────────────────────────────────┐
│ USUARIO: "Quiero agendar una clase para mañana a las 6pm"      │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────────┐
│ MESSAGE PROCESSOR                                                  │
│                                                                    │
│  1. LeadManager.get_or_create(phone)                              │
│     → lead_id = 123                                               │
│                                                                    │
│  2. ConversationManager.get_or_create(lead_id)                    │
│     → conversation_id = 456                                       │
│                                                                    │
│  3. ConversationManager.save_message(INBOUND)                     │
│     → Guarda mensaje en PostgreSQL                                │
│                                                                    │
│  4. AIService.generate_response()                                 │
│     ┌──────────────────────────────────────────┐                 │
│     │ OpenAI GPT-4o-mini                       │                 │
│     │ + System Prompt (academy info)           │                 │
│     │ + Historial (últimos 5 mensajes)         │                 │
│     │ → "¡Perfecto! Te agendo para mañana..."  │                 │
│     └──────────────────────────────────────────┘                 │
│                                                                    │
│  5. IntentDetector.detect_booking_intent()                        │
│     Keywords: "agendar", "mañana", "6pm"                          │
│     → booking_detected = True                                     │
└────────────┬───────────────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────────┐
│ APPOINTMENT SCHEDULER                                              │
│                                                                    │
│  1. parse_appointment_request()                                   │
│     → clase_tipo: "adultos_jiujitsu"                              │
│     → fecha: "2025-11-25"                                         │
│     → hora: "18:00"                                               │
│                                                                    │
│  2. Validar disponibilidad                                        │
│     ✅ Horario válido                                             │
│     ✅ No hay doble booking                                       │
│     ✅ Semana de prueba disponible                                │
│                                                                    │
│  3. book_trial_week(lead_id, clase_tipo)                          │
│     → Actualiza lead.status = SCHEDULED                           │
│     → Actualiza lead.trial_class_date = "2025-11-25"             │
│     → Guarda en PostgreSQL                                        │
└────────────┬───────────────────────────────────────────────────────┘
             │
             ├──────────────────┬────────────────────┐
             │                  │                    │
             ↓                  ↓                    ↓
┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ NOTIFICATION     │  │ REMINDER        │  │ MESSAGE          │
│ SERVICE          │  │ SERVICE         │  │ PROCESSOR        │
│                  │  │                 │  │                  │
│ Enviar notifica- │  │ Programar       │  │ Retornar         │
│ ción al staff:   │  │ recordatorios:  │  │ respuesta al     │
│                  │  │                 │  │ usuario:         │
│ WhatsApp a       │  │ - 24h antes     │  │                  │
│ +506-7015-0369   │  │ - Celery task   │  │ "✅ Agendado!"   │
│                  │  │ - Redis Queue   │  │                  │
│ "🔔 NUEVO        │  │                 │  │                  │
│  PROSPECTO"      │  │ Status: PENDING │  │                  │
│                  │  │ send_at:        │  │                  │
│ Lead: Juan       │  │ 2025-11-24      │  │                  │
│ Clase: Jiu-Jitsu │  │ 18:00           │  │                  │
│ Fecha: 25/11     │  │                 │  │                  │
└──────────────────┘  └─────────────────┘  └──────────────────┘
        ↓                      ↓                     ↓
        │                      │                     │
        ↓                      ↓                     ↓
   ✅ ENVIADO          ⏰ PROGRAMADO           📱 ENVIADO
   (Twilio)           (Celery Task)          (WhatsApp)
```

---

## 🔧 MANEJO DE ERROR: DOBLE BOOKING

```
┌──────────────────────────────────────────────────────────────────┐
│ USUARIO: "Quiero agendar otra clase"                            │
│ (Ya tiene una clase agendada activamente)                       │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────────┐
│ MESSAGE PROCESSOR                                                  │
│  1-5. [Mismo flujo inicial...]                                     │
│  6. IntentDetector.detect_booking_intent() → True                  │
└────────────┬───────────────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────────┐
│ APPOINTMENT SCHEDULER                                              │
│                                                                    │
│  1. book_trial_week(lead_id, ...)                                 │
│                                                                    │
│  2. Validación: ¿Lead ya tiene booking activo?                    │
│     lead.status == SCHEDULED ✓                                    │
│     lead.trial_class_date != NULL ✓                               │
│                                                                    │
│  3. Retornar error:                                               │
│     {                                                              │
│       "success": False,                                            │
│       "message": "Ya tenés una semana de prueba activa."          │
│     }                                                              │
└────────────┬───────────────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────────┐
│ MESSAGE PROCESSOR - Manejo de Error                               │
│                                                                    │
│  if 'Ya tenés una semana de prueba activa' in result['message']:  │
│      return "Ya tenés una clase de prueba agendada.               │
│              Si necesitás modificar tu reserva,                    │
│              por favor avisame."                                   │
│                                                                    │
│  ✅ NO retorna respuesta optimista de OpenAI                       │
│  ✅ Retorna mensaje de error claro al usuario                      │
└────────────┬───────────────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────────────────┐
│ RESPUESTA AL USUARIO:                                            │
│                                                                  │
│ "Ya tenés una clase de prueba agendada.                         │
│  Si necesitás modificar tu reserva, por favor avisame."         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 DIAGRAMA DE COMPONENTES

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CAPA DE PRESENTACIÓN                           │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Twilio     │  │  Dashboard   │  │  REST API    │            │
│  │   Webhook    │  │   (Flask)    │  │  Endpoints   │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE ORQUESTACIÓN                             │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │           MESSAGE PROCESSOR (Orquestador)                 │    │
│  │                                                           │    │
│  │  - Coordina flujo de procesamiento                        │    │
│  │  - Maneja errores centralizadamente                       │    │
│  │  - Retorna respuestas unificadas                          │    │
│  └───────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE SERVICIOS                                │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐              │
│  │    Lead     │  │ Conversation │  │   Intent    │              │
│  │   Manager   │  │   Manager    │  │  Detector   │              │
│  └─────────────┘  └──────────────┘  └─────────────┘              │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐              │
│  │     AI      │  │ Appointment  │  │ Notification│              │
│  │   Service   │  │  Scheduler   │  │   Service   │              │
│  └─────────────┘  └──────────────┘  └─────────────┘              │
│                                                                     │
│  ┌─────────────┐                                                   │
│  │  Reminder   │                                                   │
│  │   Service   │                                                   │
│  └─────────────┘                                                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                                    │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   PostgreSQL    │  │   Redis Cloud   │  │   SQLAlchemy    │   │
│  │   (Principal)   │  │     (Caché)     │  │      (ORM)      │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE INTEGRACIÓN                              │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   OpenAI API    │  │   Twilio API    │  │  Celery Queue   │   │
│  │  (GPT-4o-mini)  │  │   (WhatsApp)    │  │  (Background)   │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 DIAGRAMA DE SEGURIDAD Y DATOS

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATOS SENSIBLES                                  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │                    .env (NO COMMITEAR)                   │     │
│  │                                                          │     │
│  │  OPENAI_API_KEY          → OpenAI API                   │     │
│  │  TWILIO_ACCOUNT_SID      → Twilio API                   │     │
│  │  TWILIO_AUTH_TOKEN       → Twilio API (Secreto)         │     │
│  │  DATABASE_URL            → PostgreSQL Connection         │     │
│  │  REDIS_URL               → Redis Cloud Connection       │     │
│  │  SECRET_KEY              → Flask Sessions (Secreto)     │     │
│  └──────────────────────────────────────────────────────────┘     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    DATOS PERSISTIDOS                                │
│                                                                     │
│  PostgreSQL:                                                        │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │   academies    │  │     leads      │  │  conversations │       │
│  │                │  │                │  │                │       │
│  │  - name        │  │  - phone       │  │  - lead_id     │       │
│  │  - phone       │  │  - name        │  │  - is_active   │       │
│  │  - email       │  │  - email       │  │  - created_at  │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐                           │
│  │    messages    │  │ class_reminders│                           │
│  │                │  │                │                           │
│  │  - conv_id     │  │  - lead_id     │                           │
│  │  - direction   │  │  - send_at     │                           │
│  │  - content     │  │  - status      │                           │
│  └────────────────┘  └────────────────┘                           │
│                                                                     │
│  Redis Cloud (Caché):                                              │
│  ┌────────────────────────────────────────────────┐               │
│  │  conversation_history:{conv_id}                │               │
│  │  - TTL: 1 hora                                 │               │
│  │  - Formato: Lista de mensajes JSON            │               │
│  └────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ DIAGRAMA DE PERFORMANCE

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OPTIMIZACIONES                                   │
│                                                                     │
│  1. CACHÉ DE CONVERSACIONES (Redis)                                │
│     ┌──────────────────────────────────────┐                       │
│     │ Sin caché:  ~200ms (PostgreSQL read) │                       │
│     │ Con caché:  ~10ms  (Redis read)      │                       │
│     │ Mejora:     20x más rápido           │                       │
│     └──────────────────────────────────────┘                       │
│                                                                     │
│  2. ÍNDICES EN POSTGRESQL                                          │
│     ┌────────────────────────────────────────────┐                 │
│     │ leads.phone         → Index (búsqueda)    │                 │
│     │ conversations.lead_id → Index (join)      │                 │
│     │ messages.conversation_id → Index (join)   │                 │
│     │ class_reminders.send_at → Index (query)   │                 │
│     └────────────────────────────────────────────┘                 │
│                                                                     │
│  3. BACKGROUND TASKS (Celery)                                      │
│     ┌──────────────────────────────────────────────────┐           │
│     │ Recordatorios → Procesados asincrónicamente     │           │
│     │ Notificaciones → No bloquean respuesta al user │           │
│     │ Queue: Redis Cloud                              │           │
│     └──────────────────────────────────────────────────┘           │
│                                                                     │
│  4. MOCKS EN TESTS                                                 │
│     ┌────────────────────────────────────────────┐                 │
│     │ OpenAI   → Mock (sin consumir API)       │                 │
│     │ Twilio   → Mock (sin enviar mensajes)    │                 │
│     │ Database → SQLite in-memory (velocidad)  │                 │
│     └────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘

MÉTRICAS OBJETIVO:
┌────────────────────────────────────┐
│ Tiempo de respuesta: < 2 segundos │
│ Cache hit rate:      > 80%        │
│ Uptime:              > 99.5%      │
│ Test coverage:       > 85%        │
└────────────────────────────────────┘
```

---

**Última actualización:** 24/11/2025
**Versión:** 2.0 (MessageProcessor Architecture)
