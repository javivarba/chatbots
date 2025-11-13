# Instalación y Configuración de ngrok para BJJ Mingo

## ¿Qué es ngrok y por qué lo necesitamos?

**ngrok** crea un túnel público hacia tu servidor local (localhost:5000), permitiendo que Twilio envíe webhooks de WhatsApp a tu aplicación.

**Sin ngrok:**
- Tu app corre en `localhost:5000`
- Twilio no puede acceder a localhost
- No puedes recibir mensajes de WhatsApp

**Con ngrok:**
- Tu app corre en `localhost:5000`
- ngrok crea una URL pública (ej: `https://abc123.ngrok.io`)
- Twilio envía mensajes a esa URL
- ngrok redirige a tu localhost:5000

---

## Instalación de ngrok (Windows)

### Método 1: Descarga Directa (Recomendado)

**PASO 1: Descargar ngrok**

1. Ve a: https://ngrok.com/download
2. Click en "Download for Windows"
3. Descarga el archivo `.zip`

**PASO 2: Extraer ngrok**

1. Busca el archivo descargado (ej: `ngrok-v3-stable-windows-amd64.zip`)
2. Click derecho > "Extraer todo..."
3. Extrae a una carpeta fácil de recordar, por ejemplo:
   - `C:\ngrok`
   - O `C:\Users\javiv\ngrok`

**PASO 3: Agregar ngrok al PATH (Opcional pero recomendado)**

Opción A - Usar ngrok desde su carpeta:
```powershell
# Navega a la carpeta donde extrajiste ngrok
cd C:\ngrok
.\ngrok http 5000
```

Opción B - Agregar al PATH para usar desde cualquier lugar:

1. Busca "Variables de entorno" en Windows
2. Click en "Editar las variables de entorno del sistema"
3. Click en "Variables de entorno"
4. En "Variables del sistema", busca "Path" y click "Editar"
5. Click "Nuevo"
6. Agrega la ruta donde extrajiste ngrok (ej: `C:\ngrok`)
7. Click "Aceptar" en todas las ventanas
8. **IMPORTANTE:** Cierra y vuelve a abrir PowerShell/Terminal

Ahora deberías poder ejecutar:
```powershell
ngrok http 5000
```

**PASO 4: Crear cuenta en ngrok (Gratis)**

1. Ve a: https://dashboard.ngrok.com/signup
2. Crea una cuenta gratuita
3. Verifica tu email

**PASO 5: Obtener tu authtoken**

1. Una vez con sesión iniciada, ve a: https://dashboard.ngrok.com/get-started/your-authtoken
2. Copia tu authtoken (algo como: `2abc...xyz`)

**PASO 6: Configurar authtoken**

En PowerShell/Terminal:
```powershell
# Si agregaste ngrok al PATH:
ngrok config add-authtoken TU_AUTHTOKEN_AQUI

# Si NO lo agregaste al PATH:
cd C:\ngrok
.\ngrok config add-authtoken TU_AUTHTOKEN_AQUI
```

---

### Método 2: Instalar con Chocolatey (Si ya tienes Chocolatey)

```powershell
# En PowerShell como Administrador
choco install ngrok
```

---

## Verificar Instalación

```powershell
ngrok version
```

Deberías ver algo como:
```
ngrok version 3.x.x
```

---

## Usar ngrok con tu aplicación

### PASO 1: Iniciar tu servidor Flask

En una terminal:
```powershell
cd "C:\Users\javiv\OneDrive\Desktop\Proyectos\bjj-chatbot\bjj-academy-bot\backend"
python app.py
# o
flask run
```

Tu aplicación debería estar corriendo en `http://localhost:5000`

### PASO 2: Iniciar ngrok en OTRA terminal

Abre una SEGUNDA terminal/PowerShell:
```powershell
ngrok http 5000
```

Verás algo como:
```
ngrok

Session Status                online
Account                       tu_cuenta (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123xyz.ngrok-free.app -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**IMPORTANTE:** Copia la URL de "Forwarding" (ej: `https://abc123xyz.ngrok-free.app`)

### PASO 3: Configurar webhook en Twilio

1. Ve a: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
2. En "WHEN A MESSAGE COMES IN", pega tu URL de ngrok + la ruta del webhook:
   ```
   https://abc123xyz.ngrok-free.app/webhook/whatsapp
   ```
3. Método: `POST`
4. Click "Save"

---

## Probar el Sistema Completo

### 1. Asegúrate de tener todo corriendo:

**Terminal 1 - Flask:**
```powershell
cd backend
python app.py
```

**Terminal 2 - ngrok:**
```powershell
ngrok http 5000
```

**Terminal 3 - Logs (opcional):**
```powershell
cd backend
tail -f logs/app.log  # En Windows usa: Get-Content logs/app.log -Wait
```

### 2. Envía un mensaje de WhatsApp

Desde **+50670150369**, envía un mensaje al número del Sandbox de Twilio:
```
Hola, quiero información sobre las clases
```

### 3. Verifica que funcione:

- ✅ Deberías recibir una respuesta del bot
- ✅ En los logs verás el mensaje procesado
- ✅ En ngrok (http://127.0.0.1:4040) verás las peticiones

---

## Solución de Problemas

### Error: "ngrok no se reconoce como comando"

**Solución:**
- Ejecuta ngrok desde su carpeta: `cd C:\ngrok` luego `.\ngrok http 5000`
- O agrega ngrok al PATH (ver PASO 3 arriba)

### Error: "ERROR:  authentication failed"

**Solución:**
```powershell
ngrok config add-authtoken TU_AUTHTOKEN
```
Obtén tu authtoken en: https://dashboard.ngrok.com/get-started/your-authtoken

### Error: "ERR_NGROK_108"

**Solución:**
- Cuenta gratuita de ngrok tiene límite de sesiones
- Cierra otras sesiones de ngrok abiertas
- O actualiza a plan de pago

### ngrok se cierra cuando cierro la terminal

**Solución:**
- Deja la terminal de ngrok abierta mientras desarrollas
- O ejecuta ngrok en background (requiere plan de pago)

### Twilio no puede conectarse a ngrok

**Solución:**
1. Verifica que ngrok esté corriendo
2. Verifica que la URL en Twilio sea correcta
3. Prueba la URL en tu navegador: `https://tu-url.ngrok.io/webhook/whatsapp`
   - Deberías ver una respuesta JSON

---

## Alternativas a ngrok (Opcional)

Si no quieres usar ngrok, otras opciones son:

### 1. **LocalTunnel** (Gratis, sin cuenta)
```powershell
npm install -g localtunnel
lt --port 5000
```

### 2. **Serveo** (Gratis, sin instalación)
```powershell
ssh -R 80:localhost:5000 serveo.net
```

### 3. **Deploy en producción** (Recomendado largo plazo)
- Heroku
- Railway
- Render
- DigitalOcean

---

## Resumen de Comandos Rápidos

```powershell
# 1. Iniciar Flask (Terminal 1)
cd backend
python app.py

# 2. Iniciar ngrok (Terminal 2)
ngrok http 5000

# 3. Copiar URL de ngrok
# https://abc123.ngrok-free.app

# 4. Configurar en Twilio
# https://abc123.ngrok-free.app/webhook/whatsapp

# 5. Probar enviando WhatsApp al Sandbox
```

---

## Próximos Pasos

Una vez que ngrok funcione:

1. ✅ Configura el webhook en Twilio
2. ✅ Prueba enviando mensajes de WhatsApp
3. ✅ Verifica que las notificaciones lleguen cuando alguien agenda
4. 🚀 Cuando estés listo, deploya en producción (sin ngrok)

---

## Soporte

- Documentación ngrok: https://ngrok.com/docs
- Dashboard ngrok: https://dashboard.ngrok.com
- Twilio Webhook docs: https://www.twilio.com/docs/usage/webhooks
