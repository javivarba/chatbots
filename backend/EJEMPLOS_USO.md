# Ejemplos de Uso - Sistema de Recordatorios

## 📱 Ejemplo Completo: Desde el Mensaje hasta el Recordatorio

### Escenario: Juan quiere probar una clase

#### **Paso 1: Cliente envía mensaje (Lunes 11:00 AM)**
```
Cliente (WhatsApp): Hola, quiero probar Jiu-Jitsu
```

#### **Paso 2: Bot responde y agenda (automático)**
```
Bot: ¡Hola Juan! 👋

Excelente que quieras probar Jiu-Jitsu. Tenemos clases de Lunes a Viernes
a las 6:00 PM.

¿Te gustaría empezar tu SEMANA DE PRUEBA GRATIS esta semana?
```

```
Cliente: Sí, quiero empezar el martes
```

```
Bot: ✅ ¡SEMANA DE PRUEBA CONFIRMADA!

📋 Detalles:
- Clase: Jiu-Jitsu Adultos
- Días: Lunes a Viernes
- Hora: 18:00
- Primera clase: Martes 12/11/2025
- Válido hasta: 18/11/2025

🔔 Te enviaremos un recordatorio 24 horas antes de cada clase.

¡Te esperamos! 🥋
```

#### **Paso 3: Sistema programa recordatorios (automático)**

En la base de datos se crean 5 recordatorios:
```sql
class_reminders:
  - Martes 12/11 18:00 (status: pending)
  - Miércoles 13/11 18:00 (status: pending)
  - Jueves 14/11 18:00 (status: pending)
  - Viernes 15/11 18:00 (status: pending)
  - Lunes 17/11 18:00 (status: pending)
```

#### **Paso 4: Celery Beat revisa cada hora**
```
Lunes 11/11 - 18:00 → Busca clases para Martes 12/11 ~18:00
              ↓
         Encuentra: Clase de Juan Martes 18:00
              ↓
    Encola tarea en Redis
```

#### **Paso 5: Celery Worker envía recordatorio (Lunes 6:00 PM)**
```
Bot → Juan (WhatsApp):

🔔 RECORDATORIO DE CLASE

¡Hola Juan! 👋

Te recordamos que mañana Martes 12/11/2025 tenés clase de:

🥋 Jiu-Jitsu Adultos
⏰ Hora: 18:00
📍 Santo Domingo de Heredia

🗺️ Waze: https://waze.com/ul/hd1u0y3qpc

👕 Recordá traer:
- Ropa deportiva cómoda
- Agua
- Toalla

¡Te esperamos! 🥋
```

#### **Paso 6: Actualiza base de datos**
```sql
UPDATE class_reminders
SET reminder_status = 'sent',
    reminder_sent_at = '2025-11-11 18:00:00'
WHERE id = 1;
```

---

## 🔄 Flujo Visual Completo

```
LUNES 11:00 AM
┌─────────────────────────────────┐
│ Cliente: "Quiero probar JJ"     │
└───────────────┬─────────────────┘
                ↓
         [Flask App]
                ↓
         [MessageHandler]
                ↓
    [AppointmentScheduler]
                ↓
┌─────────────────────────────────┐
│ BD: trial_weeks (nueva fila)    │
│ BD: class_reminders (5 filas)   │
│     - Martes 18:00 (pending)    │
│     - Miércoles 18:00 (pending) │
│     - Jueves 18:00 (pending)    │
│     - Viernes 18:00 (pending)   │
│     - Lunes 18:00 (pending)     │
└─────────────────────────────────┘

LUNES 18:00 (24 horas antes)
┌─────────────────────────────────┐
│ Celery Beat ejecuta cada hora   │
└───────────────┬─────────────────┘
                ↓
    [check_and_send_reminders()]
                ↓
    Busca: clases entre ahora+23h
           y ahora+25h
                ↓
    Encuentra: Martes 18:00
                ↓
┌─────────────────────────────────┐
│ Redis: Encola tarea             │
└───────────────┬─────────────────┘
                ↓
         [Celery Worker]
                ↓
    [ReminderService._send_reminder()]
                ↓
      [Twilio → WhatsApp]
                ↓
┌─────────────────────────────────┐
│ Cliente recibe recordatorio     │
└─────────────────────────────────┘
                ↓
┌─────────────────────────────────┐
│ BD: reminder_status = 'sent'    │
└─────────────────────────────────┘
```

---

## 💻 Ejemplos de Comandos

### Ver recordatorios pendientes desde Python
```python
from app.services.reminder_service import ReminderService
from app.utils.database import get_db_connection

rs = ReminderService()

# Contar pendientes
count = rs.get_pending_reminders_count()
print(f"Recordatorios pendientes: {count}")

# Ver detalles
with get_db_connection(db_path='bjj_academy.db') as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cr.id, l.name, cr.class_datetime, cr.reminder_status
        FROM class_reminders cr
        JOIN lead l ON cr.lead_id = l.id
        WHERE cr.reminder_status = 'pending'
        ORDER BY cr.class_datetime
    """)

    for reminder in cursor.fetchall():
        print(f"#{reminder[0]}: {reminder[1]} - {reminder[2]} ({reminder[3]})")
```

### Ejecutar manualmente la tarea de recordatorios
```python
from app.tasks.reminder_tasks import check_and_send_reminders

# Ejecutar ahora (sin esperar Celery Beat)
result = check_and_send_reminders()
print(result)

# Output:
# {
#   'success': True,
#   'sent': 3,
#   'failed': 0,
#   'total': 3
# }
```

### Crear recordatorio de prueba
```python
from app.services.reminder_service import ReminderService
from datetime import datetime, timedelta

rs = ReminderService()

# Crear recordatorio para mañana
tomorrow = datetime.now() + timedelta(days=1)
tomorrow_6pm = tomorrow.replace(hour=18, minute=0, second=0)

reminder_id = rs._create_reminder(
    lead_id=1,  # ID del lead
    trial_week_id=1,  # ID de la semana de prueba
    clase_tipo='adultos_jiujitsu',
    class_datetime=tomorrow_6pm
)

print(f"Recordatorio creado: ID {reminder_id}")
```

### Programar recordatorios para una semana completa
```python
from app.services.reminder_service import ReminderService

rs = ReminderService()

result = rs.schedule_trial_week_reminders(
    lead_id=1,
    trial_week_id=1,
    clase_tipo='adultos_jiujitsu',
    start_date='2025-11-12'
)

print(f"Resultado: {result['message']}")
for reminder in result.get('reminders', []):
    print(f"  - {reminder['day']} {reminder['date']} a las {reminder['time']}")
```

---

## 📊 Queries SQL Útiles

### Ver todos los recordatorios con información del lead
```sql
SELECT
    cr.id,
    l.name AS lead_name,
    l.phone AS lead_phone,
    cr.clase_tipo,
    cr.class_datetime,
    cr.reminder_status,
    cr.reminder_sent_at
FROM class_reminders cr
JOIN lead l ON cr.lead_id = l.id
ORDER BY cr.class_datetime;
```

### Ver recordatorios que se enviarán hoy
```sql
SELECT
    cr.id,
    l.name,
    cr.class_datetime,
    cr.reminder_status
FROM class_reminders cr
JOIN lead l ON cr.lead_id = l.id
WHERE cr.reminder_status = 'pending'
AND DATE(cr.class_datetime) = DATE('now', '+1 day')
ORDER BY cr.class_datetime;
```

### Estadísticas de recordatorios
```sql
SELECT
    reminder_status,
    COUNT(*) as cantidad,
    MIN(class_datetime) as primera_clase,
    MAX(class_datetime) as ultima_clase
FROM class_reminders
GROUP BY reminder_status;
```

### Ver tasa de éxito de recordatorios
```sql
SELECT
    reminder_status,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM class_reminders) as porcentaje
FROM class_reminders
GROUP BY reminder_status;
```

---

## 🧪 Testing Manual Paso a Paso

### Test 1: Verificar que Redis está corriendo
```bash
redis-cli ping
# Esperado: PONG
```

### Test 2: Verificar Celery Worker
```bash
celery -A app.celery_app inspect active
# Esperado: Lista de tareas activas (puede estar vacía)
```

### Test 3: Verificar Celery Beat
```bash
celery -A app.celery_app inspect scheduled
# Esperado: Lista de tareas programadas
```

### Test 4: Simular agendamiento completo
```python
# En Python interactivo
from app.services.appointment_scheduler import AppointmentScheduler

scheduler = AppointmentScheduler()

# Simular agendamiento
result = scheduler.book_trial_week(
    lead_id=1,  # Debe existir en BD
    clase_tipo='adultos_jiujitsu',
    notes='Test manual'
)

print(result)
# Esperado: {'success': True, 'message': '...', 'trial_id': X}
```

### Test 5: Verificar que se crearon recordatorios
```bash
python -c "from app.services.reminder_service import ReminderService; print(f'Pendientes: {ReminderService().get_pending_reminders_count()}')"
# Esperado: Pendientes: 5 (o el número esperado)
```

### Test 6: Enviar recordatorio de prueba
```python
from app.services.reminder_service import ReminderService

rs = ReminderService()
result = rs.test_reminder(lead_id=1)
print(result)
# Esperado: {'success': True, 'message': 'Recordatorio enviado'}
```

---

## 📈 Monitoreo en Tiempo Real

### Terminal 1: Ver logs de Flask
```bash
cd backend
python run.py

# Verás:
# [INFO] Mensaje de +506-XXXX-XXXX: Quiero agendar
# [INFO] Respuesta generada: 300 caracteres
# [INFO] Trial week programada: ID 5
```

### Terminal 2: Ver logs de Celery Worker
```bash
cd backend
start_celery_worker.bat

# Verás:
# [INFO] Task app.tasks.reminder_tasks.check_and_send_reminders succeeded
# [INFO] Recordatorio enviado a +506-XXXX-XXXX
```

### Terminal 3: Ver logs de Celery Beat
```bash
cd backend
start_celery_beat.bat

# Verás:
# [INFO] Scheduler: Sending due task check-and-send-reminders
# [INFO] check-and-send-reminders sent. id->5f3d2c1a
```

---

## 🎯 Casos de Uso Comunes

### Caso 1: Cliente agenda múltiples clases
El sistema crea recordatorios para CADA clase automáticamente.

### Caso 2: Cliente cancela
Puedes marcar los recordatorios como cancelados:
```python
cursor.execute("""
    UPDATE class_reminders
    SET reminder_status = 'cancelled'
    WHERE trial_week_id = ? AND reminder_status = 'pending'
""", (trial_week_id,))
```

### Caso 3: Re-enviar recordatorio
```python
# Cambiar status a pending
cursor.execute("""
    UPDATE class_reminders
    SET reminder_status = 'pending',
        reminder_sent_at = NULL,
        error_message = NULL
    WHERE id = ?
""", (reminder_id,))
```

### Caso 4: Personalizar mensaje de recordatorio
Editar `reminder_service.py` línea 126-145 (función `_send_reminder`)

---

## ✅ Checklist de Producción

- [ ] Redis corriendo 24/7
- [ ] Celery Worker con auto-restart (supervisor, systemd)
- [ ] Celery Beat con auto-restart
- [ ] Logs configurados (`celery_worker.log`, `celery_beat.log`)
- [ ] Monitoreo de errores (Sentry, Rollbar)
- [ ] Backup de base de datos
- [ ] Variables de entorno en `.env` (no en código)
- [ ] Tests automáticos ejecutándose

---

Para más información, consulta:
- [RECORDATORIOS_README.md](RECORDATORIOS_README.md) - Documentación completa
- [QUICK_START.md](QUICK_START.md) - Guía de inicio rápido
- [COMANDOS_RAPIDOS.txt](COMANDOS_RAPIDOS.txt) - Referencia rápida
