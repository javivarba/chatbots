# Guia Completa: Iniciar Sistema BJJ Mingo con Ngrok

## Sistema Completo Requiere 4 Terminales

```
┌─────────────────────────────────────────────────────────┐
│                   SISTEMA BJJ MINGO                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Terminal 1: Ngrok (Exponer webhook a internet)        │
│  Terminal 2: Flask App (Servidor principal)            │
│  Terminal 3: Celery Worker (Procesar tareas)           │
│  Terminal 4: Celery Beat (Programar recordatorios)     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Paso 1: Iniciar Ngrok (PRIMERO)

### Terminal 1 - Ngrok
```bash
ngrok http 5000
```

**Output esperado:**
```
ngrok

Session Status                online
Account                       tu-cuenta
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**IMPORTANTE: Copiar la URL de Ngrok**
```
https://xxxx-xxx-xxx-xxx.ngrok-free.app
```

Esta URL debe estar configurada en Twilio:
1. Ir a: https://console.twilio.com/
2. Messaging → Settings → WhatsApp sandbox settings
3. "When a message comes in": https://xxxx-xxx-xxx-xxx.ngrok-free.app/webhook
4. Guardar

---

## Paso 2: Iniciar Flask App

### Terminal 2 - Flask
```bash
cd c:\Users\javiv\OneDrive\Desktop\Proyectos\bjj-chatbot\bjj-academy-bot\backend
python run.py
```

**Output esperado:**
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
```

**Verificar que funciona:**
Abrir en navegador: http://127.0.0.1:5000/
Deberías ver: "BJJ Academy Bot API Running"

---

## Paso 3: Iniciar Celery Worker

### Terminal 3 - Celery Worker
```bash
cd c:\Users\javiv\OneDrive\Desktop\Proyectos\bjj-chatbot\bjj-academy-bot\backend
start_celery_worker.bat
```

**Output esperado:**
```
[INFO] Connected to redis://redis-19503.c262.us-east-1-3.ec2.cloud.redislabs.com:19503/0
[INFO] mingle: searching for neighbors
[INFO] mingle: all alone
[INFO] celery@DESKTOP ready.
[INFO] Received task: app.tasks.reminder_tasks.check_and_send_reminders
```

**Verificar conexión a Redis Cloud:**
```bash
# En otra terminal temporal
cd backend
python -c "from app.celery_app import celery_app; print(celery_app.control.inspect().active())"
```

---

## Paso 4: Iniciar Celery Beat

### Terminal 4 - Celery Beat
```bash
cd c:\Users\javiv\OneDrive\Desktop\Proyectos\bjj-chatbot\bjj-academy-bot\backend
start_celery_beat.bat
```

**Output esperado:**
```
[INFO] beat: Starting...
[INFO] Scheduler: Sending due task check-and-send-reminders (app.tasks.reminder_tasks.check_and_send_reminders)
[INFO] Writing entries...
```

**Verificar que programa tareas:**
En el log de Celery Worker (Terminal 3) deberías ver cada hora:
```
[INFO] Task app.tasks.reminder_tasks.check_and_send_reminders[xxx] received
[INFO] Task app.tasks.reminder_tasks.check_and_send_reminders[xxx] succeeded in 0.15s
```

---

## Resumen Visual de 4 Terminales

```
╔═══════════════════════════╗
║   Terminal 1: NGROK       ║
╠═══════════════════════════╣
║ ngrok http 5000           ║
║                           ║
║ Forwarding:               ║
║ https://xxxx.ngrok.app    ║
║ -> localhost:5000         ║
╚═══════════════════════════╝

╔═══════════════════════════╗
║   Terminal 2: FLASK       ║
╠═══════════════════════════╣
║ cd backend                ║
║ python run.py             ║
║                           ║
║ Running on:               ║
║ http://127.0.0.1:5000     ║
╚═══════════════════════════╝

╔═══════════════════════════╗
║ Terminal 3: CELERY WORKER ║
╠═══════════════════════════╣
║ cd backend                ║
║ start_celery_worker.bat   ║
║                           ║
║ Status: ready             ║
║ Connected to Redis Cloud  ║
╚═══════════════════════════╝

╔═══════════════════════════╗
║  Terminal 4: CELERY BEAT  ║
╠═══════════════════════════╣
║ cd backend                ║
║ start_celery_beat.bat     ║
║                           ║
║ Scheduler: Running        ║
║ Next run: 14:00:00        ║
╚═══════════════════════════╝
```

---

## Verificar que Todo Funciona

### Test 1: Enviar mensaje de prueba por WhatsApp

1. Enviar desde WhatsApp (tu número conectado a Twilio sandbox):
   ```
   Hola, quiero probar Jiu-Jitsu
   ```

2. **Terminal 2 (Flask)** debería mostrar:
   ```
   [INFO] Mensaje recibido de +506XXXXXXXX
   [INFO] Respuesta generada: 250 caracteres
   [INFO] Mensaje enviado exitosamente
   ```

3. Deberías recibir respuesta del bot en WhatsApp

### Test 2: Agendar clase y verificar recordatorios

1. Continuar conversación en WhatsApp:
   ```
   Sí, quiero empezar el martes
   ```

2. Bot responde con confirmación

3. **Verificar en base de datos** que se crearon recordatorios:
   ```bash
   python -c "from app.services.reminder_service import ReminderService; print(f'Recordatorios pendientes: {ReminderService().get_pending_reminders_count()}')"
   ```

   Deberías ver:
   ```
   Recordatorios pendientes: 5
   ```

### Test 3: Ver recordatorios en Redis Cloud

1. Abrir Redis Insight: https://cloud.redis.io/

2. Ir a tu database → Browser

3. Buscar keys: `celery*`

4. Deberías ver:
   ```
   celery-task-meta-xxxxx
   _kombu.binding.celery
   unacked_mutex
   ```

### Test 4: Simular envío de recordatorio (opcional)

Si quieres probar el envío sin esperar 24 horas:

```python
# En Python interactivo
from app.services.reminder_service import ReminderService
from datetime import datetime, timedelta

rs = ReminderService()

# Crear recordatorio para dentro de 1 minuto (para testing)
test_time = datetime.now() + timedelta(minutes=1)

reminder_id = rs._create_reminder(
    lead_id=1,  # Usar un lead_id que exista
    trial_week_id=1,
    clase_tipo='adultos_jiujitsu',
    class_datetime=test_time
)

print(f"Recordatorio de prueba creado: #{reminder_id}")
print(f"Se enviará a las: {test_time.strftime('%H:%M:%S')}")

# Esperar 1 minuto y verificar en WhatsApp
```

---

## Monitoreo en Tiempo Real

### Ver logs de cada componente:

**Flask (Terminal 2):**
```
[INFO] POST /webhook - 200
[INFO] Mensaje de +506XXXXXXXX: Quiero agendar
[INFO] Trial week programada: ID 5
```

**Celery Worker (Terminal 3):**
```
[INFO] Task check_and_send_reminders received
[INFO] Enviando recordatorio a +506XXXXXXXX
[INFO] Task check_and_send_reminders succeeded in 1.23s
```

**Celery Beat (Terminal 4):**
```
[INFO] Scheduler: Sending due task check-and-send-reminders
[INFO] check-and-send-reminders sent. id->5f3d2c1a
```

**Ngrok (Terminal 1):**
```
POST /webhook                  200 OK
```

---

## Flujo Completo de un Recordatorio

```
DIA 1: LUNES 11:00 AM
┌────────────────────────────────────────┐
│ Cliente: "Quiero probar JJ el martes"  │
└──────────────┬─────────────────────────┘
               ↓
         [Ngrok recibe]
               ↓
      [Flask procesa mensaje]
               ↓
   [AppointmentScheduler.book_trial_week()]
               ↓
┌────────────────────────────────────────┐
│ BD: trial_week creada                  │
│ BD: 5 class_reminders (status=pending) │
│     - Martes 18:00                     │
│     - Miércoles 18:00                  │
│     - Jueves 18:00                     │
│     - Viernes 18:00                    │
│     - Lunes 18:00                      │
└────────────────────────────────────────┘


DIA 1: LUNES 18:00 (24 horas antes)
┌────────────────────────────────────────┐
│ Celery Beat ejecuta cada hora          │
└──────────────┬─────────────────────────┘
               ↓
    [check_and_send_reminders()]
               ↓
    Busca: clases entre ahora+23h
           y ahora+25h
               ↓
    Encuentra: Martes 18:00
               ↓
┌────────────────────────────────────────┐
│ Redis Cloud: Encola tarea              │
└──────────────┬─────────────────────────┘
               ↓
       [Celery Worker procesa]
               ↓
    [ReminderService._send_reminder()]
               ↓
       [Twilio → WhatsApp]
               ↓
┌────────────────────────────────────────┐
│ Cliente recibe:                        │
│                                        │
│ "Recordatorio de clase                 │
│  Mañana Martes 12/11/2025              │
│  Hora: 18:00                           │
│  Jiu-Jitsu Adultos"                    │
└────────────────────────────────────────┘
               ↓
┌────────────────────────────────────────┐
│ BD: reminder_status = 'sent'           │
│     reminder_sent_at = '2025-11-11...' │
└────────────────────────────────────────┘
```

---

## Checklist de Sistema Funcionando

- [ ] Terminal 1: Ngrok mostrando "Forwarding" activo
- [ ] Terminal 2: Flask mostrando "Running on http://127.0.0.1:5000"
- [ ] Terminal 3: Celery Worker mostrando "celery@DESKTOP ready"
- [ ] Terminal 4: Celery Beat mostrando "beat: Starting..."
- [ ] Twilio webhook configurado con URL de Ngrok
- [ ] Envié mensaje de prueba por WhatsApp
- [ ] Bot respondió correctamente
- [ ] Agendé clase de prueba
- [ ] Verifico en BD que se crearon recordatorios
- [ ] Veo tareas en Redis Insight

---

## Troubleshooting

### Problema: Ngrok URL cambió
**Solución:**
1. Copiar nueva URL de Terminal 1
2. Actualizar en Twilio → WhatsApp sandbox → Webhook URL
3. Guardar

### Problema: Celery Worker no conecta a Redis Cloud
**Solución:**
```bash
cd backend
python test_redis_connection.py
```
Verificar que .env tiene las credenciales correctas.

### Problema: No recibo recordatorios
**Verificar:**
1. Celery Beat está corriendo (Terminal 4)
2. Hay recordatorios pendientes en BD
3. La clase está programada para ~24 horas desde ahora

**Forzar envío manual:**
```python
from app.tasks.reminder_tasks import check_and_send_reminders
result = check_and_send_reminders()
print(result)
```

### Problema: WhatsApp no recibe mensajes
**Verificar:**
1. Ngrok está corriendo (Terminal 1)
2. URL de Ngrok está en Twilio
3. Número está registrado en Twilio sandbox
4. Twilio tiene créditos/balance

---

## Para Detener el Sistema

Presionar `Ctrl+C` en cada terminal en este orden:

1. **Terminal 4** (Celery Beat) - Primero
2. **Terminal 3** (Celery Worker) - Segundo
3. **Terminal 2** (Flask) - Tercero
4. **Terminal 1** (Ngrok) - Último

---

## Comandos Rápidos de Referencia

```bash
# Verificar Redis Cloud
python test_redis_connection.py

# Ver recordatorios pendientes
python -c "from app.services.reminder_service import ReminderService; print(f'Pendientes: {ReminderService().get_pending_reminders_count()}')"

# Test completo del sistema
python test_complete_flow.py

# Verificar que Celery ve las tareas
celery -A app.celery_app inspect active

# Ver tareas programadas en Celery Beat
celery -A app.celery_app inspect scheduled

# Forzar ejecución de recordatorios ahora
python -c "from app.tasks.reminder_tasks import check_and_send_reminders; print(check_and_send_reminders())"
```

---

¡Sistema listo para producción! 🥋
