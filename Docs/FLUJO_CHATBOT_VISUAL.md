# Flujo Visual del Chatbot BJJ Mingo

## 🔄 Flujo Principal de Conversación

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUARIO ENVÍA MENSAJE                     │
│                         "Hola, quiero info"                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    TWILIO RECIBE MENSAJE                         │
│  - Número: whatsapp:+50612345678                                 │
│  - Nombre: Javi Vargas                                           │
│  - Body: "Hola, quiero info"                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│               WEBHOOK NORMALIZA Y EXTRAE DATOS                   │
│  ✓ Número normalizado: +50612345678                              │
│  ✓ Nombre del perfil: Javi Vargas                               │
│  ✓ Mensaje: "Hola, quiero info"                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                 BUSCAR O CREAR LEAD EN BD                        │
│  ┌──────────────────────────────────────────┐                   │
│  │ SELECT * FROM leads                      │                   │
│  │ WHERE phone = '+50612345678'             │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
│  ¿Existe? ─── SÍ ──→ Cargar lead existente                      │
│     │                                                             │
│     └─── NO ──→ Crear nuevo lead                                │
│                  - phone: +50612345678                           │
│                  - name: Javi Vargas                             │
│                  - status: NEW                                   │
│                  - source: whatsapp                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              DETECTAR NOMBRE EN MENSAJE                          │
│  Patrones:                                                       │
│  - "Mi nombre es Juan"                                           │
│  - "Me llamo María"                                              │
│  - "Soy Carlos Gomez"                                            │
│  - "Juan Pérez" (solo nombre)                                    │
│                                                                  │
│  ¿Detectado? ─── SÍ ──→ Actualizar nombre del lead              │
│     │                                                             │
│     └─── NO ──→ Continuar                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│             BUSCAR O CREAR CONVERSACIÓN ACTIVA                   │
│  ┌──────────────────────────────────────────┐                   │
│  │ SELECT * FROM conversations              │                   │
│  │ WHERE lead_id = 15                       │                   │
│  │ AND is_active = TRUE                     │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
│  ¿Existe? ─── SÍ ──→ Usar conversación existente                │
│     │                                                             │
│     └─── NO ──→ Crear nueva conversación                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              GUARDAR MENSAJE DEL USUARIO                         │
│  INSERT INTO messages                                            │
│  - conversation_id: 10                                           │
│  - direction: INBOUND                                            │
│  - content: "Hola, quiero info"                                 │
│  - created_at: 2025-11-16 14:30:00                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              CARGAR HISTORIAL DE CONVERSACIÓN                    │
│  SELECT * FROM messages                                          │
│  WHERE conversation_id = 10                                      │
│  ORDER BY created_at DESC                                        │
│  LIMIT 5                                                         │
│                                                                  │
│  Resultado (últimos 5 mensajes en orden):                       │
│  1. user: "Hola, quiero info"                                   │
│  2. assistant: "¡Perfecto! ¿Para vos o alguien más?"            │
│  3. user: "Para mí"                                             │
│  4. assistant: "¿Qué clase te interesa?"                        │
│  5. user: "Jiu-Jitsu"                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PREPARAR CONTEXTO PARA IA                       │
│                                                                  │
│  Lead Info:                                                      │
│  - Nombre: Javi Vargas                                           │
│  - Teléfono: +50612345678                                        │
│  - Status: interested                                            │
│  - Score: 8/10                                                   │
│                                                                  │
│  Academy Info:                                                   │
│  - Nombre: BJJ Mingo                                             │
│  - Ubicación: Santo Domingo de Heredia                           │
│  - Teléfono: +506-7015-0369                                      │
│  - Horarios: {...}                                               │
│  - Precios: {...}                                                │
│                                                                  │
│  System Prompt:                                                  │
│  - Voseo costarricense                                           │
│  - Tono natural, NO robótico                                     │
│  - Información precisa                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                 LLAMAR A OPENAI GPT-3.5-TURBO                    │
│                                                                  │
│  POST https://api.openai.com/v1/chat/completions                │
│                                                                  │
│  Body:                                                           │
│  {                                                               │
│    "model": "gpt-3.5-turbo",                                     │
│    "messages": [                                                 │
│      {                                                           │
│        "role": "system",                                         │
│        "content": "Sos Mingo Asistente..."                       │
│      },                                                          │
│      {                                                           │
│        "role": "user",                                           │
│        "content": "Hola, quiero info"                           │
│      },                                                          │
│      ... historial ...                                           │
│    ],                                                            │
│    "max_tokens": 600,                                            │
│    "temperature": 0.7                                            │
│  }                                                               │
│                                                                  │
│  Response:                                                       │
│  "¡Hola Javi! ¿Qué clase te interesa probar?"                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│            DETECTAR INTENCIÓN DE AGENDAMIENTO                    │
│                                                                  │
│  ¿El mensaje contiene?                                           │
│  - Palabras: "agendar", "reservar", "semana de prueba"          │
│  - Día: "lunes", "martes", "mañana"                             │
│  - Hora: "6pm", "18:00"                                          │
│  - Nombre: "Juan Pérez"                                          │
│                                                                  │
│  ¿Intención detectada? ─── SÍ ──→ Parsear y agendar             │
│     │                                                             │
│     └─── NO ──→ Solo responder con IA                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    ┌────────┴────────┐
                    │                 │
                   SÍ                NO
                    │                 │
                    ↓                 ↓
    ┌───────────────────────┐   ┌─────────────────┐
    │  AGENDAR CLASE        │   │ ENVIAR RESPUESTA│
    │                       │   │ DEL BOT         │
    └───────┬───────────────┘   └────────┬────────┘
            │                             │
            ↓                             │
┌───────────────────────────┐            │
│  PARSEAR INFORMACIÓN      │            │
│  - Tipo: adultos_jiujitsu │            │
│  - Día: lunes             │            │
│  - Hora: 18:00            │            │
└───────┬───────────────────┘            │
        │                                 │
        ↓                                 │
┌───────────────────────────┐            │
│  ACTUALIZAR LEAD          │            │
│  - status: SCHEDULED      │            │
│  - trial_class_date: ...  │            │
│  - lead_score: 9          │            │
└───────┬───────────────────┘            │
        │                                 │
        ↓                                 │
┌───────────────────────────┐            │
│  PROGRAMAR RECORDATORIOS  │            │
│  Para los próximos 7 días:│            │
│  - Lunes 18/11: 18:00     │            │
│  - Martes 19/11: 18:00    │            │
│  - Miércoles 20/11: 18:00 │            │
│  - ...                    │            │
│  Enviar 24hrs antes       │            │
└───────┬───────────────────┘            │
        │                                 │
        ↓                                 │
┌───────────────────────────┐            │
│  NOTIFICAR AL STAFF       │            │
│  WhatsApp: +50670150369   │            │
│  "Nuevo prospecto:        │            │
│   Javi Vargas agendó..."  │            │
└───────┬───────────────────┘            │
        │                                 │
        ↓                                 │
┌───────────────────────────┐            │
│  MENSAJE DE CONFIRMACIÓN  │            │
│  "✅ ¡SEMANA DE PRUEBA    │            │
│   CONFIRMADA!             │            │
│   - Clase: Jiu-Jitsu...   │            │
│   - Días: Lun-Vie         │            │
│   - ..."                  │            │
└───────┬───────────────────┘            │
        │                                 │
        └────────────┬────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                  GUARDAR RESPUESTA DEL BOT                       │
│  INSERT INTO messages                                            │
│  - conversation_id: 10                                           │
│  - direction: OUTBOUND                                           │
│  - content: "¡Hola Javi! ¿Qué clase..."                         │
│  - created_at: 2025-11-16 14:30:15                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  ACTUALIZAR LEAD STATUS                          │
│  Si mensaje contiene: "agendar", "clase", "prueba"              │
│  → status = INTERESTED                                           │
│  → lead_score = 8                                                │
│                                                                  │
│  Si es primera interacción:                                      │
│  → status = ENGAGED                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ENVIAR RESPUESTA A TWILIO                     │
│  MessagingResponse()                                             │
│  → WhatsApp → Usuario                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    ┌────────────────┐
                    │  FIN DEL FLUJO │
                    └────────────────┘
```

---

## 🔔 Flujo de Recordatorios Automáticos

```
┌─────────────────────────────────────────────────────────────────┐
│          USUARIO AGENDÓ SEMANA DE PRUEBA                         │
│          (Ver flujo principal arriba)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              CREAR RECORDATORIOS EN BD                           │
│                                                                  │
│  Para cada clase en los próximos 7 días:                        │
│                                                                  │
│  Clase 1:                                                        │
│  - class_datetime: 2025-11-18 18:00:00                          │
│  - send_at: 2025-11-17 18:00:00 (24hrs antes)                   │
│  - status: PENDING                                               │
│                                                                  │
│  Clase 2:                                                        │
│  - class_datetime: 2025-11-19 18:00:00                          │
│  - send_at: 2025-11-18 18:00:00                                 │
│  - status: PENDING                                               │
│                                                                  │
│  ... (hasta 5 clases en la semana)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              CELERY EJECUTA TAREA CADA HORA                      │
│                                                                  │
│  Crontab: cada hora en punto                                     │
│  Task: send_pending_reminders()                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│           BUSCAR RECORDATORIOS PENDIENTES                        │
│                                                                  │
│  SELECT * FROM class_reminders                                   │
│  WHERE status = 'PENDING'                                        │
│  AND send_at <= NOW()                                            │
│  LIMIT 100                                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    ¿Hay recordatorios?
                             │
                    ┌────────┴────────┐
                   SÍ                NO
                    │                 │
                    ↓                 ↓
    ┌───────────────────────┐   ┌─────────────┐
    │ PARA CADA RECORDATORIO│   │ FIN - ESPERAR│
    │                       │   │ PRÓXIMA HORA │
    └───────┬───────────────┘   └─────────────┘
            │
            ↓
┌───────────────────────────┐
│  OBTENER INFO DEL LEAD    │
│  - lead_id: 15            │
│  - name: Javi Vargas      │
│  - phone: +50612345678    │
└───────┬───────────────────┘
        │
        ↓
┌───────────────────────────┐
│  CONSTRUIR MENSAJE        │
│  "🔔 Recordatorio!        │
│   Hola Javi Vargas!       │
│   Mañana tenés clase...   │
│   Lunes 18/11 a las 18:00"│
└───────┬───────────────────┘
        │
        ↓
┌───────────────────────────┐
│  ENVIAR VÍA TWILIO        │
│  POST /Messages           │
│  - from: whatsapp:+14155..│
│  - to: whatsapp:+50612... │
│  - body: mensaje          │
└───────┬───────────────────┘
        │
        ↓
    ¿Éxito?
        │
  ┌─────┴─────┐
 SÍ           NO
  │            │
  ↓            ↓
┌────────┐  ┌────────┐
│MARCAR  │  │MARCAR  │
│COMO    │  │COMO    │
│SENT    │  │FAILED  │
│        │  │        │
│- status│  │- status│
│  SENT  │  │  FAILED│
│- sent_ │  │- failed│
│  at    │  │  _reason│
│- msg_  │  │        │
│  sid   │  │        │
└────────┘  └────────┘
```

---

## 📬 Flujo de Notificación al Staff

```
┌─────────────────────────────────────────────────────────────────┐
│          USUARIO AGENDÓ SEMANA DE PRUEBA                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              PREPARAR INFORMACIÓN                                │
│                                                                  │
│  Lead Info:                                                      │
│  - name: Javi Vargas                                             │
│  - phone: +50612345678                                           │
│  - status: scheduled                                             │
│                                                                  │
│  Trial Info:                                                     │
│  - clase_nombre: Jiu-Jitsu Adultos                               │
│  - dias_texto: Lunes a Viernes                                   │
│  - hora: 18:00                                                   │
│  - start_date: 2025-11-18                                        │
│  - notes: "Agendado via WhatsApp"                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              CONSTRUIR MENSAJE DE NOTIFICACIÓN                   │
│                                                                  │
│  "🔔 *NUEVO PROSPECTO - SEMANA DE PRUEBA*                       │
│                                                                  │
│  👤 *Prospecto:*                                                 │
│  • Nombre: Javi Vargas                                           │
│  • Teléfono: +50612345678                                        │
│  • Estado: scheduled                                             │
│                                                                  │
│  🥋 *Clase Agendada:*                                            │
│  • Tipo: Jiu-Jitsu Adultos                                       │
│  • Días: Lunes a Viernes                                         │
│  • Horario: 18:00                                                │
│  • Inicio: 18/11/2025                                            │
│                                                                  │
│  📝 *Notas:*                                                     │
│  Agendado via WhatsApp                                           │
│                                                                  │
│  ⏰ Registrado: 16/11/2025 14:30"                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│          INTENTAR ENVÍO POR WHATSAPP PRIMARIO                    │
│          Número: +50670150369                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                   ÉXITO            ERROR
                    │                 │
                    ↓                 ↓
        ┌───────────────┐   ┌─────────────────────┐
        │ ✅ ENVIADO    │   │ INTENTAR WHATSAPP   │
        │ FIN           │   │ SECUNDARIO          │
        └───────────────┘   │ +50688888888        │
                            └─────────┬───────────┘
                                      │
                            ┌─────────┴─────────┐
                          ÉXITO             ERROR
                            │                  │
                            ↓                  ↓
                ┌───────────────┐   ┌──────────────────┐
                │ ✅ ENVIADO    │   │ INTENTAR EMAIL   │
                │ FIN           │   │ testingtoimp...  │
                └───────────────┘   └─────────┬────────┘
                                              │
                                    ┌─────────┴─────────┐
                                  ÉXITO             ERROR
                                    │                  │
                                    ↓                  ↓
                        ┌───────────────┐   ┌──────────────┐
                        │ ✅ ENVIADO    │   │ ❌ SOLO LOG  │
                        │ FIN           │   │ EN CONSOLA   │
                        └───────────────┘   └──────────────┘
```

---

**Resumen de Flujos**:
- ✅ **Flujo Principal**: Recepción → Identificación → IA → Respuesta
- ✅ **Flujo de Agendamiento**: Detección → Parseo → BD → Confirmación
- ✅ **Flujo de Recordatorios**: Creación → Celery → Envío 24hrs antes
- ✅ **Flujo de Notificación**: Staff notificado en tiempo real

**Fecha**: 16 de noviembre de 2025
