# Sistema de Recordatorios Automáticos - BJJ Mingo

## Descripción

Sistema que envía recordatorios automáticos por WhatsApp 24 horas antes de cada clase confirmada.

**Ejemplo:**
- Si un cliente tiene clase el **Martes a las 6:00 PM**
- Recibirá un recordatorio el **Lunes a las 6:00 PM** (24 horas antes)

## Componentes del Sistema

### 1. **Base de Datos**
- **Tabla `class_reminders`**: Almacena todos los recordatorios programados
  - Trackea qué recordatorios se han enviado
  - Previene duplicados
  - Almacena errores para debugging

### 2. **ReminderService** (`app/services/reminder_service.py`)
- Crea recordatorios para cada día de clase de la semana de prueba
- Envía mensajes por WhatsApp usando Twilio
- Actualiza estado de recordatorios (pending → sent/failed)

### 3. **Celery Workers** (`app/celery_app.py` + `app/tasks/reminder_tasks.py`)
- **Tarea periódica cada hora**: Revisa qué clases están en 24 horas y envía recordatorios
- **Tareas de limpieza**: Elimina recordatorios antiguos
- **Tareas bajo demanda**: Programa recordatorios cuando se confirma un agendamiento

### 4. **Integración con AppointmentScheduler**
- Cuando se confirma una semana de prueba, automáticamente:
  1. Registra la semana en la base de datos
  2. Notifica al staff de la academia
  3. **NUEVO**: Programa recordatorios para cada día de clase

## Instalación y Configuración

### 1. Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

Esto instalará:
- `celery==5.3.4` - Sistema de tareas asíncronas
- `redis==5.0.1` - Broker de mensajes para Celery

### 2. Instalar y Ejecutar Redis

**Windows:**
```bash
# Opción 1: Con Docker
docker run -d -p 6379:6379 redis

# Opción 2: Descargar Redis desde https://github.com/microsoftarchive/redis/releases
# Ejecutar redis-server.exe
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Mac (con Homebrew)
brew install redis
brew services start redis
```

**Verificar que Redis está corriendo:**
```bash
redis-cli ping
# Debe responder: PONG
```

### 3. Configurar Variables de Entorno

Asegurarse que el archivo `.env` tenga:

```env
# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Twilio (requerido para enviar mensajes)
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 4. Ejecutar el Sistema

**Terminal 1 - Flask App (Backend principal):**
```bash
cd backend
python run.py
```

**Terminal 2 - Celery Worker (Procesa tareas):**
```bash
cd backend
celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Terminal 3 - Celery Beat (Scheduler periódico):**
```bash
cd backend
celery -A app.celery_app beat --loglevel=info
```

## Cómo Funciona

### Flujo Completo

1. **Cliente agenda una clase por WhatsApp**
   ```
   Cliente: "Quiero una clase de Jiu-Jitsu adultos el martes"
   ```

2. **Bot confirma y programa recordatorios**
   ```python
   # En appointment_scheduler.py
   trial_id = book_trial_week(lead_id, 'adultos_jiujitsu', notes)

   # Automáticamente programa recordatorios:
   # - Lunes 6pm → Recordatorio
   # - Martes 6pm → Recordatorio
   # - Miércoles 6pm → Recordatorio
   # etc.
   ```

3. **Celery Beat ejecuta cada hora**
   ```python
   # Cada hora (xx:00), ejecuta:
   check_and_send_reminders()

   # Busca clases entre ahora + 23h y ahora + 25h
   # Envía recordatorios pendientes
   ```

4. **Cliente recibe recordatorio 24hrs antes**
   ```
   🔔 RECORDATORIO DE CLASE

   ¡Hola Juan! 👋

   Te recordamos que mañana Martes 13/11/2025 tenés clase de:

   🥋 Jiu-Jitsu Adultos
   ⏰ Hora: 18:00
   📍 Santo Domingo de Heredia

   ¡Te esperamos! 🥋
   ```

## Comandos Útiles

### Ver estado de Celery
```bash
# Ver workers activos
celery -A app.celery_app inspect active

# Ver tareas programadas
celery -A app.celery_app inspect scheduled

# Ver estadísticas
celery -A app.celery_app inspect stats
```

### Testing Manual

**Probar recordatorios desde Python:**
```python
from app.services.reminder_service import ReminderService

reminder_service = ReminderService()

# Ver recordatorios pendientes
count = reminder_service.get_pending_reminders_count()
print(f"Recordatorios pendientes: {count}")

# Enviar recordatorio de prueba a un lead
result = reminder_service.test_reminder(lead_id=1)
print(result)
```

**Ejecutar tarea de recordatorios manualmente:**
```python
from app.tasks.reminder_tasks import check_and_send_reminders

# Ejecutar ahora (sin esperar la programación)
result = check_and_send_reminders()
print(result)
```

### Consultas SQL Útiles

```sql
-- Ver todos los recordatorios pendientes
SELECT
    cr.id,
    cr.class_datetime,
    l.name,
    l.phone_number,
    cr.reminder_status
FROM class_reminders cr
JOIN lead l ON cr.lead_id = l.id
WHERE cr.reminder_status = 'pending'
ORDER BY cr.class_datetime;

-- Ver recordatorios enviados hoy
SELECT
    cr.id,
    cr.class_datetime,
    cr.reminder_sent_at,
    l.name
FROM class_reminders cr
JOIN lead l ON cr.lead_id = l.id
WHERE cr.reminder_status = 'sent'
AND DATE(cr.reminder_sent_at) = DATE('now')
ORDER BY cr.reminder_sent_at DESC;

-- Ver estadísticas
SELECT
    reminder_status,
    COUNT(*) as count
FROM class_reminders
GROUP BY reminder_status;
```

## Tareas Programadas (Celery Beat Schedule)

| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `check-and-send-reminders` | Cada hora (xx:00) | Envía recordatorios 24hrs antes |
| `cleanup-old-reminders` | Diario (2:00 AM) | Elimina recordatorios antiguos |
| `update-expired-trials` | Diario (3:00 AM) | Marca trial weeks expiradas |

## Troubleshooting

### Redis no conecta
```bash
# Verificar que Redis está corriendo
redis-cli ping

# Si no responde, iniciar Redis
# Windows (Docker):
docker run -d -p 6379:6379 redis

# Linux:
sudo systemctl start redis
```

### Celery no encuentra tareas
```bash
# Verificar que el módulo app.tasks está en PYTHONPATH
cd backend
python -c "from app.tasks import check_and_send_reminders; print('OK')"
```

### Recordatorios no se envían
1. **Verificar que Celery Beat está corriendo**
   ```bash
   celery -A app.celery_app inspect scheduled
   ```

2. **Verificar logs de Celery Worker**
   - Buscar errores en la terminal donde corre el worker

3. **Verificar que Twilio está configurado**
   ```python
   from app.services.notification_service import NotificationService
   ns = NotificationService()
   print(ns.twilio_available)  # Debe ser True
   ```

4. **Verificar recordatorios en DB**
   ```sql
   SELECT * FROM class_reminders
   WHERE reminder_status = 'pending'
   AND class_datetime BETWEEN datetime('now', '+23 hours')
   AND datetime('now', '+25 hours');
   ```

### Formato de mensajes incorrectos
- Revisar zona horaria en `celery_app.py`
- Verificar configuración de `timezone='America/Costa_Rica'`

## Arquitectura

```
┌─────────────────┐
│   WhatsApp      │
│   (Cliente)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Flask App (Backend)               │
│   - MessageHandler                  │
│   - AppointmentScheduler            │
│     └─> book_trial_week()           │
│         └─> _schedule_reminders()   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   ReminderService                   │
│   - schedule_trial_week_reminders() │
│   - Crea recordatorios en DB        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Database (SQLite)                 │
│   - class_reminders (tabla)         │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Celery Beat (Scheduler)           │
│   - Ejecuta cada hora               │
│   - check_and_send_reminders()      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Celery Worker                     │
│   - Procesa tarea                   │
│   - ReminderService.send_reminder() │
│   - NotificationService (Twilio)    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   WhatsApp      │
│   (Cliente)     │
│   🔔 Recordatorio│
└─────────────────┘
```

## Próximas Mejoras

- [ ] Dashboard para ver recordatorios pendientes
- [ ] Opción para que clientes cancelen clases desde WhatsApp
- [ ] Recordatorios personalizados por tipo de clase
- [ ] Integración con Google Calendar
- [ ] Métricas de asistencia post-recordatorio

## Contacto

Para soporte o preguntas sobre el sistema de recordatorios, contactar al equipo de desarrollo.
