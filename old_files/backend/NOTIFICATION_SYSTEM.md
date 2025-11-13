# Sistema de Notificaciones - BJJ Mingo

## Descripción General

El sistema de notificaciones envía alertas automáticas al staff de la academia cuando un nuevo prospecto agenda una clase de prueba a través del chatbot de WhatsApp.

## Flujo Modificado

### Antes (con link de calendario)
1. Cliente acepta clase de prueba
2. Bot genera link de Google Calendar
3. Bot envía link al cliente
4. Cliente debe agregar al calendario manualmente

### Ahora (con notificaciones al staff)
1. Cliente acepta clase de prueba
2. Bot registra la semana de prueba en la BD
3. **Bot envía notificación automática al WhatsApp de la academia (+50670150369)**
4. Bot confirma al cliente que la academia lo contactará
5. Staff recibe toda la información del prospecto instantáneamente

## Componentes Implementados

### 1. Configuración - `academy_info.py`
```python
ACADEMY_INFO = {
    ...
    'notification_phone': '+50670150369',  # Número para recibir notificaciones
    ...
}
```

### 2. Servicio de Notificaciones - `notification_service.py`

**Funcionalidad principal:**
- Envía notificaciones por WhatsApp usando Twilio
- Construye mensajes informativos con todos los datos del prospecto
- Maneja errores y fallbacks

**Métodos clave:**
- `notify_new_trial_booking(lead_info, trial_info)`: Envía notificación principal
- `test_notification()`: Prueba el sistema

**Formato del mensaje de notificación:**
```
🔔 NUEVO PROSPECTO - SEMANA DE PRUEBA

👤 Prospecto:
• Nombre: Juan Pérez
• Teléfono: +506-1234-5678
• Estado: trial_scheduled

🥋 Clase Agendada:
• Tipo: Jiu-Jitsu Adultos
• Días: Lunes a Viernes
• Horario: 18:00
• Inicio: 21/10/2025

📝 Notas:
Agendado vía WhatsApp

⏰ Registrado: 21/10/2025 14:30

---
BJJ Mingo - Sistema de Notificaciones
```

### 3. Scheduler Modificado - `appointment_scheduler.py`

**Cambios principales:**
- Integra `NotificationService` en el constructor
- Método `book_trial_week()` ahora:
  1. Registra la semana de prueba
  2. Envía notificación al staff
  3. Retorna mensaje de confirmación al cliente (SIN link de calendario)

**Nuevo mensaje al cliente:**
```
✅ ¡SEMANA DE PRUEBA CONFIRMADA!

📋 Detalles:
- Clase: Jiu-Jitsu Adultos
- Días: Lunes a Viernes
- Hora: 18:00
- Primera clase: Lunes 22/10/2025
- Válido hasta: 28/10/2025

📍 Ubicación: Santo Domingo de Heredia
🗺️ Waze: https://waze.com/ul/hd1u0y3qpc

👕 Qué traer:
- Ropa deportiva cómoda
- Sin zapatos
- Agua
- Si tenés gi, podés traerlo

🎯 La academia te contactará pronto para confirmar tu asistencia.

📞 Cualquier duda: +506-8888-8888

¡Te esperamos! 🥋
```

### 4. Message Handler - `message_handler.py`

**Ya estaba correctamente integrado:**
- Detecta intención de agendamiento
- Llama a `scheduler.book_trial_week()`
- El scheduler automáticamente envía las notificaciones

## Configuración Necesaria

### Variables de Entorno (.env)

```bash
# Twilio (requerido para notificaciones)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# OpenAI (para el chatbot)
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
```

### Instalación de Dependencias

```bash
pip install twilio
```

## Pruebas

### Script de Prueba Interactivo

Ejecutar desde `backend/`:

```bash
python scripts/test_notification.py
```

**Opciones disponibles:**
1. Probar solo el servicio de notificaciones (envía mensaje de prueba)
2. Probar el flujo completo (crea lead, agenda clase, envía notificación)
3. Salir

### Prueba Manual desde Python

```python
from app.services.notification_service import NotificationService

# Inicializar
notifier = NotificationService()

# Datos de prueba
lead_info = {
    'name': 'Juan Pérez',
    'phone': '+506-1234-5678',
    'status': 'trial_scheduled'
}

trial_info = {
    'clase_nombre': 'Jiu-Jitsu Adultos',
    'start_date': '2025-10-22',
    'dias_texto': 'Lunes a Viernes',
    'hora': '18:00',
    'notes': 'Mensaje de prueba'
}

# Enviar notificación
result = notifier.notify_new_trial_booking(lead_info, trial_info)
print(result)
```

## Verificación

### Checklist después de implementar:

- [x] Número de notificación configurado en `academy_info.py`
- [x] `notification_service.py` creado y funcional
- [x] `appointment_scheduler.py` modificado
- [x] Mensaje al cliente actualizado (sin link de calendario)
- [x] Variables de Twilio en `.env`
- [ ] Twilio configurado y probado
- [ ] Prueba de notificación exitosa
- [ ] Prueba del flujo completo exitosa

### Logs a revisar:

```bash
# Al inicializar el scheduler
✅ NotificationService integrado en AppointmentScheduler

# Al agendar una clase
[BOOKING] Intención de agendamiento detectada
[BOOKING] Semana de prueba registrada
✅ Notificación enviada al staff para lead {lead_id}

# Si hay problemas
⚠️ NotificationService no disponible
⚠️ No se pudo enviar notificación: {razón}
```

## Troubleshooting

### Notificaciones no se envían

1. **Verificar credenciales de Twilio:**
   ```python
   import os
   print(os.getenv('TWILIO_ACCOUNT_SID'))
   print(os.getenv('TWILIO_AUTH_TOKEN'))
   print(os.getenv('TWILIO_WHATSAPP_NUMBER'))
   ```

2. **Verificar formato del número:**
   - Debe incluir código de país: `+50670150369`
   - Twilio lo convierte a: `whatsapp:+50670150369`

3. **Revisar sandbox de Twilio:**
   - En desarrollo, el número receptor debe estar registrado en el sandbox
   - Enviar mensaje "join [código]" al número de WhatsApp de Twilio

4. **Verificar logs:**
   ```bash
   # Buscar errores en los logs
   grep "NotificationService" logs/app.log
   grep "Error enviando" logs/app.log
   ```

### El flujo funciona pero no llega la notificación

1. Verificar que el número esté habilitado en Twilio Sandbox
2. Verificar límites de mensajes en Twilio
3. Revisar el estado del mensaje en Twilio Console

## Beneficios del Nuevo Sistema

✅ **Notificación instantánea** - El staff sabe inmediatamente cuando hay un nuevo prospecto

✅ **Información completa** - Nombre, teléfono, clase de interés, todo en un mensaje

✅ **Mejor seguimiento** - El staff puede contactar proactivamente al prospecto

✅ **Registro automático** - Todo queda registrado en la base de datos

✅ **Experiencia del cliente** - Mensaje claro de que la academia lo contactará

## Próximas Mejoras (Opcionales)

- [ ] Email de backup además de WhatsApp
- [ ] Dashboard web para ver notificaciones
- [ ] Confirmación de lectura
- [ ] Integración con Google Calendar del staff
- [ ] Recordatorios automáticos antes de la clase
- [ ] Seguimiento automático si no asiste

## Soporte

Para problemas o preguntas sobre el sistema de notificaciones:
1. Revisar logs del sistema
2. Ejecutar script de prueba
3. Verificar configuración de Twilio
4. Consultar documentación de Twilio: https://www.twilio.com/docs/whatsapp
