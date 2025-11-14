# Guía de Inicio Rápido - Sistema de Recordatorios

## 🚀 Inicio Rápido (3 Pasos)

### Paso 1: Iniciar Redis

**Opción A - Con Docker (Recomendado):**
```bash
docker run -d --name redis-bjj -p 6379:6379 redis
```

**Opción B - Sin Docker (Windows):**
1. Descargar Redis desde: https://github.com/microsoftarchive/redis/releases
2. Ejecutar `redis-server.exe`

**Verificar que Redis está corriendo:**
```bash
redis-cli ping
# Debe responder: PONG
```

---

### Paso 2: Abrir 3 Terminales

Necesitas **3 terminales separadas** ejecutándose simultáneamente.

#### **TERMINAL 1: Flask App (Backend Principal)**
```bash
cd backend
python run.py
```
Esta terminal mostrará los logs de mensajes de WhatsApp entrantes.

#### **TERMINAL 2: Celery Worker (Procesa Tareas)**
```bash
cd backend
start_celery_worker.bat
```
Esta terminal procesará las tareas de envío de recordatorios.

#### **TERMINAL 3: Celery Beat (Scheduler)**
```bash
cd backend
start_celery_beat.bat
```
Esta terminal ejecutará la tarea cada hora para revisar recordatorios pendientes.

---

### Paso 3: Verificar que Todo Funciona

```bash
# En una nueva terminal
cd backend
python test_reminders_system.py
```

Deberías ver:
```
[OK] PASS - Database
[OK] PASS - ReminderService
[OK] PASS - NotificationService
[OK] PASS - Redis
[OK] PASS - Celery Tasks
```

---

## 📊 Cómo Funciona

Una vez todo iniciado:

1. **Cliente agenda clase** → WhatsApp
2. **Bot confirma** → Registra en BD
3. **Scheduler programa recordatorios** → Tabla `class_reminders`
4. **Celery Beat revisa cada hora** → ¿Hay clases en 24h?
5. **Celery Worker envía recordatorio** → WhatsApp al cliente

---

## 🔍 Monitoreo

### Ver logs de Celery Worker
La Terminal 2 mostrará:
```
[INFO] Tarea ejecutándose: check_and_send_reminders
[INFO] Recordatorios enviados: 3
```

### Ver logs de Celery Beat
La Terminal 3 mostrará:
```
[INFO] Scheduler: Sending due task check-and-send-reminders
```

### Verificar recordatorios en BD
```sql
-- En DB Browser o similar
SELECT * FROM class_reminders WHERE reminder_status = 'pending';
```

---

## 🛠️ Comandos Útiles

### Ver tareas activas de Celery
```bash
celery -A app.celery_app inspect active
```

### Ver tareas programadas
```bash
celery -A app.celery_app inspect scheduled
```

### Reiniciar Celery Worker (si haces cambios en código)
```bash
# Presionar Ctrl+C en Terminal 2
# Luego volver a ejecutar:
start_celery_worker.bat
```

### Detener todo
- **Ctrl+C** en cada una de las 3 terminales
- **Detener Redis:**
  ```bash
  # Con Docker:
  docker stop redis-bjj

  # Sin Docker:
  # Cerrar la ventana de redis-server.exe
  ```

---

## ⚠️ Solución de Problemas

### Error: "Redis connection refused"
```bash
# Verificar si Redis está corriendo
redis-cli ping

# Si no responde, iniciar Redis:
docker run -d --name redis-bjj -p 6379:6379 redis
```

### Error: "No module named 'celery'"
```bash
# Instalar dependencias
pip install -r requirements.txt
```

### Recordatorios no se envían
1. **Verificar logs de Celery Worker** (Terminal 2)
2. **Verificar logs de Celery Beat** (Terminal 3)
3. **Verificar que hay recordatorios pendientes:**
   ```bash
   python -c "from app.services.reminder_service import ReminderService; rs = ReminderService(); print(f'Pendientes: {rs.get_pending_reminders_count()}')"
   ```

### Error: "port 6379 already in use"
Redis ya está corriendo. No necesitas iniciarlo de nuevo.

---

## 📱 Probar Recordatorios Manualmente

Sin esperar 24 horas:

```python
# En Python interactivo
from app.services.reminder_service import ReminderService
from datetime import datetime, timedelta

rs = ReminderService()

# Simular recordatorio para mañana
tomorrow = datetime.now() + timedelta(days=1)
tomorrow_6pm = tomorrow.replace(hour=18, minute=0, second=0)

# Crear y enviar recordatorio de prueba
reminder_id = rs._create_reminder(
    lead_id=1,  # Cambiar por un lead_id real
    clase_tipo='adultos_jiujitsu',
    class_datetime=tomorrow_6pm
)

# Verificar
print(f"Recordatorio creado: {reminder_id}")
print(f"Pendientes: {rs.get_pending_reminders_count()}")
```

---

## 🎯 Resumen Visual

```
┌─────────────────────────────────────────────────────┐
│  TERMINAL 1: Flask App (python run.py)             │
│  → Procesa mensajes WhatsApp                       │
│  → Agenda clases                                   │
│  → Crea recordatorios en BD                        │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  BASE DE DATOS (SQLite)                            │
│  → Tabla: class_reminders                         │
│  → Status: pending                                 │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  TERMINAL 3: Celery Beat (Scheduler)               │
│  → Ejecuta cada hora: check_and_send_reminders()  │
│  → Busca clases en ~24 horas                       │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  REDIS (Message Broker)                            │
│  → Encola tareas                                   │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  TERMINAL 2: Celery Worker                         │
│  → Procesa tarea                                   │
│  → Envía WhatsApp con Twilio                       │
│  → Marca como 'sent' en BD                         │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  CLIENTE                                           │
│  → Recibe recordatorio 24hrs antes                 │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Inicio

- [ ] Redis corriendo (`redis-cli ping` → PONG)
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Terminal 1: Flask corriendo (`python run.py`)
- [ ] Terminal 2: Celery Worker corriendo (`start_celery_worker.bat`)
- [ ] Terminal 3: Celery Beat corriendo (`start_celery_beat.bat`)
- [ ] Test pasado (`python test_reminders_system.py`)

---

## 🆘 Necesitas Ayuda?

- **Documentación completa:** [RECORDATORIOS_README.md](RECORDATORIOS_README.md)
- **Test del sistema:** `python test_reminders_system.py`
- **Test completo:** `python test_complete_flow.py`
