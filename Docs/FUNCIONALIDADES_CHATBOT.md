# Funcionalidades Completas del Chatbot - BJJ Mingo

## 📋 Índice
1. [Arquitectura General](#arquitectura-general)
2. [Flujo de Conversación](#flujo-de-conversación)
3. [Funcionalidades Principales](#funcionalidades-principales)
4. [Sistemas de Automatización](#sistemas-de-automatización)
5. [Integraciones](#integraciones)
6. [Base de Datos](#base-de-datos)

---

## 🏗️ Arquitectura General

```
┌─────────────────┐
│   WhatsApp      │
│   (Twilio)      │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────┐
│   Flask Webhook                 │
│   - Normalización de teléfono   │
│   - Extracción de datos         │
└────────┬────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│   MessageHandler                │
│   - Identificación de usuario   │
│   - Detección de nombre         │
│   - Gestión de conversación     │
└────────┬────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│   OpenAI GPT (IA)               │
│   - Respuestas naturales        │
│   - Voseo costarricense         │
│   - Contexto personalizado      │
└────────┬────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│   AppointmentScheduler          │
│   - Agendamiento de clases      │
│   - Semanas de prueba           │
└────────┬────────────────────────┘
         │
         ↓
┌──────────────────┬──────────────┐
│                  │              │
↓                  ↓              ↓
┌──────────┐  ┌─────────┐  ┌──────────┐
│Reminder  │  │Notifica-│  │Database  │
│Service   │  │tion     │  │PostgreSQL│
│          │  │Service  │  │          │
└──────────┘  └─────────┘  └──────────┘
```

---

## 💬 Flujo de Conversación

### 1. Recepción de Mensaje

**Archivo**: `backend/app/__init__.py`

```python
# Usuario envía mensaje por WhatsApp
↓
# Twilio webhook recibe el mensaje
↓
# Normalización del número de teléfono
from_number = re.sub(r'[^\d+]', '', from_number_raw)
↓
# Extracción de datos
- Body (mensaje)
- ProfileName (nombre del perfil)
- From (número normalizado)
```

**Logs generados**:
```
[WEBHOOK] Número RAW: whatsapp:+50612345678
[WEBHOOK] Número NORMALIZADO: +50612345678
[WEBHOOK] Nombre del perfil: Javi Vargas
[WEBHOOK] Mensaje: Hola, quiero información
```

### 2. Identificación de Usuario

**Archivo**: `backend/app/services/message_handler.py`

```python
# 1. Buscar o crear Lead por teléfono
lead_id = self._get_or_create_lead(phone_number, name)
↓
# 2. Detectar nombre en el mensaje
detected_name = self._detect_name_in_message(message)
# Detecta: "Mi nombre es Juan", "Me llamo María", etc.
↓
# 3. Actualizar nombre si se detectó
if detected_name:
    self._update_lead_name(lead_id, detected_name)
```

**Logs generados**:
```
[LEAD] Buscando lead con teléfono: +50612345678
[LEAD] Lead encontrado - ID: 15, Nombre actual: Javi Vargas
[NAME_DETECTION] Nombre detectado en mensaje: Juan Pérez
[UPDATE] Cambiando nombre de 'WhatsApp User' a 'Juan Pérez'
```

### 3. Gestión de Conversación

```python
# 1. Obtener o crear conversación activa
conv_id = self._get_or_create_conversation(lead_id)
↓
# 2. Guardar mensaje del usuario
self._save_message(conv_id, MessageDirection.INBOUND, message)
↓
# 3. Cargar historial (últimos 5 mensajes)
history = self._get_conversation_history(conv_id, limit=5)
```

**Logs generados**:
```
[CONVERSATION] Buscando conversación activa para lead_id: 15
[CONVERSATION] Conversación encontrada - ID: 10, Mensajes: 4
[HISTORY] Obteniendo últimos 5 mensajes de conversación ID: 10
[HISTORY] Encontrados 3 mensajes
[HISTORY] - user: Hola...
[HISTORY] - assistant: ¡Hola, Javi! ¿Cómo estás?...
[HISTORY] - user: Quiero agendar una clase...
```

### 4. Generación de Respuesta con IA

**Archivo**: `backend/app/services/message_handler.py`

```python
# 1. Cargar información del lead y academia
lead_info = self._get_lead_info(lead_id)
academy_info = self._get_academy_info()
↓
# 2. Construir prompt del sistema con voseo costarricense
system_prompt = self._build_system_prompt(academy_info, lead_info)
↓
# 3. Preparar mensajes para OpenAI
messages = [
    {"role": "system", "content": system_prompt},
    ... historial de conversación ...,
    {"role": "user", "content": mensaje_actual}
]
↓
# 4. Llamar a OpenAI GPT
response = openai_client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=messages
)
```

**Sistema Prompt** (personalizado con voseo):
- Ubicación: Santo Domingo de Heredia
- Horarios REALES de BJJ Mingo
- Precios actualizados
- Tono: Natural, humano, NO robótico
- Lenguaje: Voseo costarricense (vos, querés, tenés, podés)

### 5. Detección de Intención de Agendamiento

```python
# Analiza si el usuario quiere agendar
booking_detected = self._detect_booking_intent(message, ai_response, history)
↓
# Si detecta intención de agendamiento:
if booking_detected:
    # Parsear fecha/hora del mensaje
    parsed = scheduler.parse_appointment_request(message, lead_id)
    ↓
    # Crear semana de prueba
    result = scheduler.book_trial_week(
        lead_id,
        clase_tipo='adultos_jiujitsu',
        notes=f"Agendado via WhatsApp: {message}"
    )
```

**Palabras clave detectadas**:
- `agendar`, `reservar`, `apartar`, `quiero clase`
- `semana de prueba`, `clase el`, `clase para`
- Días: `lunes`, `martes`, `miércoles`, `jueves`, `viernes`
- Horas: `6:00`, `18:00`, `7:30 pm`, etc.

---

## 🎯 Funcionalidades Principales

### 1. IA Conversacional (OpenAI GPT)

**Características**:
- ✅ Conversación natural en español con voseo costarricense
- ✅ Contexto personalizado por usuario
- ✅ Memoria de conversación (últimos 5 mensajes)
- ✅ Respuestas NO robóticas
- ✅ Información precisa sobre horarios, precios, ubicación

**Ejemplos de conversación**:

```
Usuario: Hola
Bot: ¡Hola! ¿Cómo estás hoy? Soy Mingo Asistente de BJJ Mingo. ¿En qué puedo ayudarte?

Usuario: Quiero información sobre las clases
Bot: ¡Genial que te interese! Tenemos clases de Jiu-Jitsu brasileño para adultos, kids y juniors.
     ¿Vos querés entrenar o es para alguien más de la familia?

Usuario: Para mí, soy adulto
Bot: Perfecto. Tenemos Jiu-Jitsu adultos de lunes a viernes a las 6:00 pm, y también
     Striking martes y jueves a las 7:30 pm. ¿Cuál te llama más la atención?

Usuario: Jiu-Jitsu. Cuánto cuesta?
Bot: El Jiu-Jitsu adultos está ₡33,000 al mes. Pero lo mejor es que podés probar una
     SEMANA COMPLETA GRATIS primero para ver si te gusta. ¿Te gustaría venir a probar?
```

### 2. Agendamiento de Clases de Prueba

**Archivo**: `backend/app/services/appointment_scheduler.py`

**Horarios disponibles**:
```python
'adultos_jiujitsu': {
    'dias': [1, 2, 3, 4, 5],  # Lunes a Viernes
    'hora': '18:00',
    'nombre': 'Jiu-Jitsu Adultos'
},
'adultos_striking': {
    'dias': [2, 4],  # Martes y Jueves
    'hora': '19:30',
    'nombre': 'Striking Adultos'
},
'kids': {
    'dias': [2, 4],  # Martes y Jueves
    'hora': '17:00',
    'nombre': 'Jiu-Jitsu Kids (4-10 años)'
},
'juniors': {
    'dias': [1, 3],  # Lunes y Miércoles
    'hora': '17:00',
    'nombre': 'Jiu-Jitsu Juniors (11-16 años)'
}
```

**Proceso de agendamiento**:
1. Usuario expresa interés en probar una clase
2. Bot detecta intención de agendamiento
3. Se parsea el tipo de clase, día y hora del mensaje
4. Se registra en la BD con estado `SCHEDULED`
5. Se envía confirmación al usuario con:
   - ✅ Detalles de la clase
   - ✅ Link de Waze
   - ✅ Qué traer
   - ✅ Recordatorio que recibirá notificación 24hrs antes

**Mensaje de confirmación**:
```
✅ ¡SEMANA DE PRUEBA CONFIRMADA!

📋 Detalles:
- Clase: Jiu-Jitsu Adultos
- Días: Lunes a Viernes
- Hora: 18:00
- Primera clase: Lunes 18/11/2025
- Válido hasta: 25/11/2025

📍 Ubicación: Santo Domingo de Heredia
🗺️ Waze: https://waze.com/ul/hd1u0y3qpc

👕 Qué traer:
- Ropa deportiva cómoda (pantaloneta/lycra, camisa deportiva)
- Sin zapatos
- Agua
- Si tenés gi, podés traerlo

🎯 *La academia te contactará pronto para confirmar tu asistencia.*
🔔 *Te enviaremos un recordatorio 24 horas antes de cada clase.*

📞 Cualquier duda: +506-7015-0369

¡Te esperamos! 🥋
```

### 3. Sistema de Recordatorios Automáticos

**Archivo**: `backend/app/services/reminder_service.py`

**Funcionamiento**:
1. Cuando se agenda una semana de prueba, se crean recordatorios automáticos
2. Se programa un recordatorio **24 horas antes** de cada clase
3. Los recordatorios se envían por WhatsApp automáticamente
4. Se usa Celery (task queue) para programar el envío

**Flujo**:
```
Agendamiento de semana de prueba
↓
ReminderService.schedule_trial_week_reminders()
↓
Para cada día de clase en los próximos 7 días:
  - Calcular fecha/hora de la clase
  - Calcular cuándo enviar recordatorio (24hrs antes)
  - Crear registro en tabla 'class_reminders'
  - Estado: PENDING
↓
Celery ejecuta tarea periódica cada hora:
  - Busca recordatorios con estado PENDING
  - Verifica si send_at <= ahora
  - Envía WhatsApp con recordatorio
  - Marca como SENT
```

**Mensaje de recordatorio**:
```
🔔 Recordatorio de Clase!

¡Hola Javi Vargas!

Te recordamos que mañana tenés tu clase de Jiu-Jitsu Adultos:

📅 Lunes 18/11/2025
🕕 18:00
📍 Santo Domingo de Heredia
🗺️ Waze: https://waze.com/ul/hd1u0y3qpc

👕 Qué traer:
- Ropa deportiva cómoda
- Agua
- Si tenés gi, podés traerlo

¡Te esperamos! 🥋

Si no podés asistir, avisanos por favor.
```

**Estados de recordatorios**:
- `PENDING`: Por enviar
- `SENT`: Enviado exitosamente
- `FAILED`: Falló el envío
- `CANCELLED`: Cancelado

### 4. Notificaciones al Staff

**Archivo**: `backend/app/services/notification_service.py`

**Cuando un prospecto agenda una clase**, se notifica automáticamente al staff por:
1. **WhatsApp primario**: +50670150369
2. **WhatsApp secundario** (si falla el primario): +50688888888
3. **Email** (si fallan ambos WhatsApp): testingtoimp2025@gmail.com

**Mensaje al staff**:
```
🔔 *NUEVO PROSPECTO - SEMANA DE PRUEBA*

👤 *Prospecto:*
• Nombre: Javi Vargas
• Teléfono: +50612345678
• Estado: scheduled

🥋 *Clase Agendada:*
• Tipo: Jiu-Jitsu Adultos
• Días: Lunes a Viernes
• Horario: 18:00
• Inicio: 18/11/2025

📝 *Notas:*
Agendado via WhatsApp: Quiero probar jiu-jitsu el lunes

⏰ Registrado: 16/11/2025 14:30

---
*BJJ Mingo - Sistema de Notificaciones*
```

---

## 🤖 Sistemas de Automatización

### 1. Celery (Task Queue)

**Archivo**: `backend/app/celery_app.py`

**Tareas programadas**:

#### A. Envío de Recordatorios (cada hora)
```python
@celery.task
def send_pending_reminders():
    """
    Ejecuta cada hora:
    - Busca recordatorios pendientes con send_at <= ahora
    - Envía WhatsApp
    - Marca como SENT o FAILED
    """
```

**Configuración**:
```python
CELERYBEAT_SCHEDULE = {
    'send-reminders-every-hour': {
        'task': 'app.tasks.reminder_tasks.send_pending_reminders',
        'schedule': crontab(minute=0),  # Cada hora en punto
    }
}
```

### 2. Redis (Broker)

**Uso**: Cola de mensajes para Celery

**Configuración**:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. PostgreSQL (Base de Datos)

**Migración**: SQLite → PostgreSQL

**Ventajas**:
- ✅ Mejor rendimiento
- ✅ Soporte para producción
- ✅ Concurrencia
- ✅ Búsquedas más eficientes

---

## 🗄️ Base de Datos

### Modelos Principales

#### 1. Academy (Academias)
```python
- id
- name
- description
- instructor_name
- phone
- address_street
- address_city
- created_at
```

#### 2. Lead (Prospectos)
```python
- id
- academy_id
- phone (ÚNICO, normalizado)
- name
- email
- source (whatsapp, facebook, etc.)
- status (new, engaged, interested, scheduled, converted, lost)
- trial_class_date
- lead_score
- created_at
- updated_at
```

**Estados del lead**:
- `NEW`: Primer contacto
- `ENGAGED`: Ha respondido al bot
- `INTERESTED`: Mostró interés en clases
- `SCHEDULED`: Agendó semana de prueba
- `SHOWED_UP`: Asistió a la clase
- `CONVERTED`: Se convirtió en cliente
- `NO_SHOW`: No asistió
- `LOST`: No mostró más interés

#### 3. Conversation (Conversaciones)
```python
- id
- academy_id
- lead_id
- platform (whatsapp)
- is_active (Boolean)
- message_count
- inbound_count
- outbound_count
- started_at
- last_message_at
```

#### 4. Message (Mensajes)
```python
- id
- conversation_id
- direction (inbound/outbound)
- content
- created_at
```

#### 5. ClassReminder (Recordatorios)
```python
- id
- lead_id
- academy_id
- class_type (adultos_jiujitsu, kids, etc.)
- class_datetime (fecha/hora de la clase)
- send_at (cuándo enviar el recordatorio)
- status (pending, sent, failed, cancelled)
- message_sid (Twilio)
- sent_at
- failed_reason
- created_at
```

### Relaciones

```
Academy (1) ←→ (N) Lead
Lead (1) ←→ (N) Conversation
Conversation (1) ←→ (N) Message
Lead (1) ←→ (N) ClassReminder
```

---

## 🔧 Integraciones

### 1. Twilio (WhatsApp)

**Funcionalidades**:
- ✅ Recibir mensajes de WhatsApp
- ✅ Enviar respuestas
- ✅ Enviar recordatorios automáticos
- ✅ Notificar al staff

**Configuración**:
```env
TWILIO_ACCOUNT_SID=ACxxxxx...
TWILIO_AUTH_TOKEN=xxxxx...
TWILIO_WHATSAPP_NUMBER=+14155238886
```

**Webhook configurado en Twilio**:
```
https://tu-dominio.com/
```

### 2. OpenAI GPT

**Modelo**: `gpt-3.5-turbo`

**Parámetros**:
```python
max_tokens = 600
temperature = 0.7
```

**Configuración**:
```env
OPENAI_API_KEY=sk-xxxxx...
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=600
OPENAI_TEMPERATURE=0.7
```

### 3. PostgreSQL

**Configuración**:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/bjj_academy
```

### 4. Redis

**Configuración**:
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 📊 Métricas y Tracking

### Lead Score (Puntuación)

**Sistema de puntuación automática**:
```python
+ 10 puntos: Tiene nombre
+ 10 puntos: Tiene email
+ 20 puntos: Status = interested
+ 30 puntos: Status = scheduled
+ 5 puntos: Base (nuevo lead)
```

**Máximo**: 100 puntos

### Tracking de Conversaciones

**Métricas automáticas**:
- Total de mensajes
- Mensajes entrantes (inbound)
- Mensajes salientes (outbound)
- Última interacción
- Duración de conversación

---

## 🔐 Seguridad

### 1. Normalización de Teléfonos

**Previene duplicados y errores de identificación**:
```python
# ANTES
from_number = "whatsapp:+506 1234-5678"

# DESPUÉS
from_number = "+50612345678"
```

### 2. Validación de Datos

- ✅ Teléfonos normalizados
- ✅ Nombres sanitizados
- ✅ Validación de tipos de clase
- ✅ Validación de fechas

### 3. Variables de Entorno

**Archivo**: `.env`
```env
# NUNCA commitear este archivo
SECRET_KEY=...
DATABASE_URL=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
OPENAI_API_KEY=...
```

---

## 📈 Mejoras Futuras Sugeridas

1. **Dashboard Web**
   - Ver prospectos en tiempo real
   - Estadísticas de conversión
   - Gestión de recordatorios

2. **Análisis de Sentimiento**
   - Detectar usuarios frustrados
   - Escalar automáticamente al staff

3. **Multi-idioma**
   - Soporte para inglés
   - Detección automática de idioma

4. **Pagos Online**
   - Integración con SINPE Móvil
   - Stripe/PayPal para tarjetas

5. **Onboarding Automatizado**
   - Envío de formularios de inscripción
   - Recolección de firmas digitales
   - Envío de reglamento

---

**Última actualización**: 16 de noviembre de 2025
**Versión del sistema**: 2.0 (PostgreSQL + Recordatorios)
**Desarrollado por**: Claude Code
