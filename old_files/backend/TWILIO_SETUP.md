# Configuración de Twilio para Notificaciones WhatsApp

## Estado Actual

✅ Código del sistema de notificaciones implementado correctamente
✅ Twilio library instalada
✅ Credenciales configuradas en .env
❌ Número de WhatsApp de Twilio necesita configuración

## Error Detectado

```
Error: The 'From' number whatsapp:+14155238886 is not a valid phone number
```

**Causa:** El número configurado no está activo o no es válido en tu cuenta de Twilio.

## Soluciones

### Opción 1: Usar Twilio Sandbox (GRATIS - Para Pruebas)

El Sandbox de Twilio te permite probar WhatsApp sin costo, pero tiene limitaciones:
- Solo puedes enviar mensajes a números que hayas registrado en el sandbox
- Debes "unirte" al sandbox desde cada número que quiera recibir mensajes

**Pasos:**

1. **Acceder a Twilio Console:**
   - Ve a: https://console.twilio.com/
   - Inicia sesión con tu cuenta

2. **Configurar WhatsApp Sandbox:**
   - En el menú lateral: `Messaging` > `Try it out` > `Send a WhatsApp message`
   - O directo: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

3. **Obtener tu código de Sandbox:**
   - Verás un código único, por ejemplo: `join animal-cat`
   - Anota tu número de Sandbox (ej: `+1 415 523 8886`)

4. **Registrar el número +50670150369:**
   - Desde el WhatsApp de +50670150369, envía un mensaje a: `+1 415 523 8886`
   - Mensaje exacto: `join [tu-código]` (por ejemplo: `join animal-cat`)
   - Recibirás confirmación de Twilio

5. **Actualizar .env con el número correcto:**
   ```bash
   # Busca en la consola de Twilio el número exacto del Sandbox
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

6. **Probar nuevamente:**
   ```bash
   cd backend
   python quick_test.py
   ```

### Opción 2: WhatsApp Business API (PRODUCCIÓN - Requiere Aprobación)

Para producción, necesitás un número de WhatsApp Business aprobado por Twilio.

**Requisitos:**
- Cuenta de Twilio con billing habilitado
- Número de teléfono propio para WhatsApp Business
- Proceso de aprobación de Facebook/Meta
- Costo: Variable según uso

**Pasos:**

1. **Upgrade a Twilio Paid Account:**
   - Ve a: https://console.twilio.com/billing
   - Agrega información de pago

2. **Solicitar WhatsApp Business:**
   - `Messaging` > `WhatsApp` > `Senders`
   - Click en "Create a Sender"
   - Llena el formulario con información de tu negocio

3. **Proceso de aprobación:**
   - Facebook/Meta revisará tu solicitud (1-3 días hábiles)
   - Necesitarás proporcionar:
     - Nombre del negocio
     - Sitio web
     - Logo
     - Descripción de uso

4. **Configurar número aprobado:**
   - Una vez aprobado, obtendrás un número
   - Actualizar `.env`:
     ```bash
     TWILIO_WHATSAPP_NUMBER=whatsapp:+[tu-numero-aprobado]
     ```

### Opción 3: Modo de Desarrollo (Sin Twilio - Solo Logs)

Si solo querés probar el flujo sin enviar mensajes reales:

El sistema ya está configurado para funcionar sin Twilio. Simplemente:

1. **Las notificaciones se registrarán en logs** en lugar de enviarse por WhatsApp
2. **Todo el flujo funcionará** (registro de leads, agendamiento, etc.)
3. **Logs mostrarán** el contenido completo del mensaje que se enviaría

**Para probar en modo desarrollo:**
```bash
cd backend
python -c "
from app.services.notification_service import NotificationService
notifier = NotificationService()
print('Twilio disponible:', notifier.twilio_available)
result = notifier.test_notification()
print(result)
"
```

## Verificar Configuración Actual de Twilio

Para ver el estado de tu cuenta de Twilio:

```bash
cd backend
python -c "
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()
client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

# Listar números de WhatsApp disponibles
print('Numeros de WhatsApp en tu cuenta:')
for number in client.messaging.v1.services.list():
    print(f'  - {number.sid}')
"
```

## Recomendación

Para **BJJ Mingo en producción**, te recomiendo:

1. **Corto plazo (Ahora):** Usar Twilio Sandbox
   - ✅ Gratis
   - ✅ Funciona inmediatamente
   - ❌ Solo para números registrados
   - ❌ Incluye "Sent from your Twilio Sandbox" en mensajes

2. **Mediano plazo (1-2 meses):** Migrar a WhatsApp Business API
   - ✅ Número propio
   - ✅ Sin limitaciones
   - ✅ Mensajes profesionales
   - ❌ Requiere aprobación
   - ❌ Tiene costo

## Siguiente Paso Recomendado

**OPCIÓN 1 - TWILIO SANDBOX (Más rápido):**

1. Ve a: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Copia tu código de sandbox
3. Desde +50670150369, envía WhatsApp a +1 415 523 8886 con: `join [código]`
4. Ejecuta: `python quick_test.py`

**OPCIÓN 2 - MODO DESARROLLO (Sin costos, sin WhatsApp real):**

El sistema ya funciona sin Twilio. Todas las notificaciones se registran en logs.
Simplemente continuá usando el sistema y revisá los logs para ver las notificaciones.

## Soporte

Si necesitás ayuda:
- Documentación Twilio: https://www.twilio.com/docs/whatsapp/quickstart
- Twilio Support: https://support.twilio.com/
