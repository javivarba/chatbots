# 📱 CONFIGURACIÓN DE NOTIFICACIONES - BJJ MINGO

## ✅ ESTADO ACTUAL

### 📞 **Número de Teléfono Principal**
```
+506-7015-0369
```

**Formatos configurados:**
- Con guiones: `+506-7015-0369` (para mostrar)
- Sin guiones: `+50670150369` (para WhatsApp API)

---

## 🔔 SISTEMA DE NOTIFICACIONES

### 1️⃣ **Notificación a la Academia (Cuando se agenda una clase)**

**¿Cuándo se envía?**
- Inmediatamente después de que un lead agenda una semana de prueba

**¿A quién se envía?**
- WhatsApp Principal: `+506-7015-0369`
- WhatsApp Secundario (respaldo): `+506-8888-8888` (actualizar si existe)
- Email (respaldo): `testingtoimp2025@gmail.com`

**¿Qué contiene el mensaje?**
```
🔔 *NUEVO PROSPECTO - SEMANA DE PRUEBA*

👤 *Prospecto:*
• Nombre: Juan Pérez
• Teléfono: +506-8888-7777
• Estado: scheduled

🥋 *Clase Agendada:*
• Tipo: Jiu-Jitsu Adultos
• Días: Lunes a Viernes
• Horario: 18:00
• Inicio: 25/11/2025

📝 *Notas:*
Agendado vía WhatsApp

⏰ Registrado: 24/11/2025 15:30

---
*BJJ Mingo - Sistema de Notificaciones*
```

**Código responsable:**
- [`backend/app/services/appointment_scheduler.py:212-234`](backend/app/services/appointment_scheduler.py#L212-L234)
- [`backend/app/services/notification_service.py:54-140`](backend/app/services/notification_service.py#L54-L140)

---

### 2️⃣ **Recordatorio al Lead (24 horas antes de cada clase)**

**¿Cuándo se envía?**
- Automáticamente 24 horas antes de cada clase de la semana de prueba

**¿A quién se envía?**
- Al número de WhatsApp del prospecto

**¿Qué contiene el mensaje?**
```
Recordatorio de Clase!

Hola Juan!

Te recordamos que mañana tenés tu clase de Jiu-Jitsu Adultos:

Lunes 25/11/2025
18:00
Santo Domingo de Heredia
Waze: https://waze.com/ul/hd1u0y3qpc

Que traer:
- Ropa deportiva cómoda
- Agua
- Si tenés gi, podés traerlo

Te esperamos!

Si no podés asistir, avisanos por favor.
```

**Código responsable:**
- [`backend/app/services/appointment_scheduler.py:301-343`](backend/app/services/appointment_scheduler.py#L301-L343)
- [`backend/app/services/reminder_service.py:167-264`](backend/app/services/reminder_service.py#L167-L264)
- [`backend/app/tasks/reminder_tasks.py:24-90`](backend/app/tasks/reminder_tasks.py#L24-L90) (tarea Celery)

---

## 📂 ARCHIVOS CONFIGURADOS

### ✅ Archivos con número actualizado:

1. **[`backend/app/config/academy_info.py`](backend/app/config/academy_info.py)**
   - Línea 10: `'phone': '+506-7015-0369'`
   - Línea 12: `'primary_whatsapp': '+50670150369'`
   - Este es el archivo PRINCIPAL de configuración

2. **Base de Datos PostgreSQL**
   - Tabla: `academies`
   - Campo: `phone = '+506-7015-0369'`
   - Email: `testingtoimp2025@gmail.com`

### ℹ️ Archivos de testing (usan números mock):
- Todos los archivos en `backend/tests/` y `backend/test_*.py`
- Estos archivos usan números ficticios para testing aislado
- No afectan la configuración de producción

---

## 🔄 FLUJO COMPLETO DE NOTIFICACIONES

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LEAD AGENDA CLASE DE PRUEBA VÍA WHATSAPP                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. AppointmentScheduler.book_trial_week()                   │
│    - Actualiza lead.status = SCHEDULED                      │
│    - Actualiza lead.trial_class_date                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    ┌──────┴──────┐
                    ↓             ↓
    ┌───────────────────────┐  ┌──────────────────────────┐
    │ NOTIFICACIÓN INMEDIATA│  │ RECORDATORIOS PROGRAMADOS│
    └───────────────────────┘  └──────────────────────────┘
                ↓                           ↓
    ┌───────────────────────┐  ┌──────────────────────────┐
    │ NotificationService   │  │ ReminderService          │
    │ .notify_new_trial_    │  │ .schedule_trial_week_    │
    │  booking()            │  │  reminders()             │
    │                       │  │                          │
    │ → WhatsApp a          │  │ → Crea recordatorios en  │
    │   +506-7015-0369      │  │   tabla ClassReminder    │
    └───────────────────────┘  │ → Status: PENDING        │
                               │ → send_at: 24hrs antes   │
                               └──────────────────────────┘
                                           ↓
                               ┌──────────────────────────┐
                               │ Celery Task (cada hora)  │
                               │ check_and_send_reminders│
                               │                          │
                               │ → Busca PENDING con      │
                               │   send_at <= now         │
                               │ → Envía WhatsApp al lead │
                               │ → Status: SENT           │
                               └──────────────────────────┘
```

---

## 🧪 TESTING DEL SISTEMA

### Tests implementados (89 tests total):

✅ **MessageHandler Refactorizado** (4 tests)
- Inicialización, procesamiento de mensajes, detección de nombre, historial

✅ **IntentDetector** (31 tests)
- Detección de intenciones, nombres, agendamiento, etc.

✅ **LeadManager** (26 tests)
- CRUD de leads, actualización de status, scores

✅ **ConversationManager** (23 tests)
- CRUD de conversaciones, mensajes, historial, caché

✅ **Sistema de Notificaciones** (5 tests)
- ✅ Notificación a academia al agendar
- ✅ Programación de recordatorios con Celery
- ✅ Creación de recordatorios en BD
- ✅ Envío de recordatorios por WhatsApp
- ✅ Filtrado de recordatorios pendientes

**Ejecutar tests:**
```bash
# Tests de notificaciones y recordatorios
python backend/test_booking_notifications.py

# Tests de integración
python backend/test_message_handler_integration.py
```

---

## 🛠️ SCRIPTS ÚTILES

### Verificar estado de la base de datos:
```bash
python backend/verify_database_status.py
```

### Resetear base de datos (desarrollo):
```bash
python backend/reset_database.py
```

### Actualizar número de teléfono:
```bash
python backend/update_academy_phone.py
```

---

## 📋 CHECKLIST DE CONFIGURACIÓN

- [x] Número de teléfono actualizado en `academy_info.py`
- [x] Número de teléfono actualizado en base de datos
- [x] NotificationService configurado con Twilio
- [x] ReminderService configurado
- [x] Celery configurado para tareas programadas
- [x] Tests de notificaciones implementados (5/5)
- [x] Tests de recordatorios implementados (5/5)
- [x] Base de datos reseteada para testing manual
- [x] Sistema de notificaciones funcionando

---

## 🔐 VARIABLES DE ENTORNO REQUERIDAS

```env
# Twilio (para WhatsApp)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=+14155238886

# OpenAI (para chatbot)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# Celery/Redis (para recordatorios)
REDIS_URL=redis://...

# Base de datos
DATABASE_URL=postgresql://...
```

---

## ✅ ESTADO FINAL

**Base de datos:**
- ✅ Academia: BJJ Mingo
- ✅ Teléfono: +506-7015-0369
- ✅ Email: testingtoimp2025@gmail.com
- ✅ Trial enabled: Sí
- ✅ 0 leads (limpio para testing)
- ✅ 0 conversaciones
- ✅ 0 mensajes
- ✅ 0 recordatorios

**Sistema:**
- ✅ OpenAI: Configurado (gpt-4o-mini)
- ✅ Twilio: Configurado
- ✅ Celery: Configurado
- ✅ NotificationService: Funcionando
- ✅ ReminderService: Funcionando

**Todo listo para testing manual! 🚀**

---

## 🔧 FIXES RECIENTES

### Fix: Respuesta de Doble Booking (24/11/2025)

**Problema:** Cuando un lead intentaba agendar una segunda vez, el sistema correctamente rechazaba el booking pero el bot respondía con un mensaje optimista confirmando la reserva.

**Causa:** En `message_handler.py`, cuando `book_trial_week()` retornaba `success: False`, el código solo registraba un warning pero retornaba la respuesta optimista de OpenAI.

**Solución:** Agregado manejo de errores apropiado en [`backend/app/services/message_handler.py:212-217`](backend/app/services/message_handler.py#L212-L217):
```python
if 'Ya tenés una semana de prueba activa' in result['message']:
    return "Ya tenés una clase de prueba agendada. Si necesitás modificar tu reserva, por favor avisame."
else:
    return f"Disculpá, hubo un problema al agendar: {result['message']}"
```

**Verificación:** Test automatizado en [`backend/test_double_booking_fix.py`](backend/test_double_booking_fix.py)
