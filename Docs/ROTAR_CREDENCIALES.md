# 🔐 Guía de Rotación de Credenciales

## ⚠️ ADVERTENCIA
Tu archivo `.env` fue commiteado a Git en septiembre 2025 y contiene credenciales sensibles.
Aunque `.env` está ahora en `.gitignore`, el historial de Git lo contiene.

---

## 📋 Credenciales a Rotar

### 1. OpenAI API Key ⚡ URGENTE
**Expuesta:** `sk-proj-T_cCUi...`
**Riesgo:** Alguien puede usar tu API key para generar llamadas costosas

**PASOS:**
1. Ve a https://platform.openai.com/api-keys
2. Haz clic en tu API key actual
3. Haz clic en "Revoke" o "Delete" para INVALIDAR la key expuesta
4. Crea una nueva API key:
   - Clic en "+ Create new secret key"
   - Nombre: "BJJ Bot Production - 2025"
   - Permisos: Solo lo necesario (Chat Completions)
5. COPIA la nueva key (solo se muestra una vez)
6. Actualiza `backend/.env`:
   ```bash
   OPENAI_API_KEY=sk-proj-NUEVA_KEY_AQUI
   ```

**Verificación:**
```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); from openai import OpenAI; client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); print('✅ OpenAI key válida')"
```

---

### 2. Twilio Credentials ⚡ URGENTE
**Expuestas:**
- Account SID: `ACef289d5e1f787e4cc365962d535457e7`
- Auth Token: `73b94324a662b5fb32625bd07d0654b0`

**Riesgo:** Alguien puede enviar SMS/WhatsApp desde tu cuenta

**PASOS:**
1. Ve a https://console.twilio.com/
2. Navega a "Account" → "API keys & tokens"
3. En "Auth Tokens" section:
   - Haz clic en "Create new Auth Token"
   - O revoca el token actual y crea uno nuevo
4. COPIA el nuevo Auth Token
5. Actualiza `backend/.env`:
   ```bash
   TWILIO_AUTH_TOKEN=NUEVO_TOKEN_AQUI
   ```

**NOTA:** El Account SID es público y no necesita rotarse, pero el Auth Token SÍ.

**Verificación:**
```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); from twilio.rest import Client; client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN')); print('✅ Twilio credentials válidas')"
```

---

### 3. Redis Cloud Password 🔸 IMPORTANTE
**Expuesta:** `ic3X6uAgSkTMk4OqezEk1GT48XIjmZWM`
**Host:** `redis-19503.c262.us-east-1-3.ec2.cloud.redislabs.com`

**Riesgo:** Alguien puede acceder a tu Redis y ver/modificar datos de caché

**PASOS:**
1. Ve a https://app.redislabs.com/
2. Selecciona tu database "redis-19503"
3. Ve a "Configuration" → "Security"
4. Cambia la contraseña:
   - Opción 1: Regenerar password automático
   - Opción 2: Establecer password custom
5. COPIA el nuevo password
6. Actualiza `backend/.env`:
   ```bash
   REDIS_PASSWORD=NUEVO_PASSWORD_AQUI
   CELERY_BROKER_URL=redis://default:NUEVO_PASSWORD_AQUI@redis-19503.c262.us-east-1-3.ec2.cloud.redislabs.com:19503/0
   CELERY_RESULT_BACKEND=redis://default:NUEVO_PASSWORD_AQUI@redis-19503.c262.us-east-1-3.ec2.cloud.redislabs.com:19503/1
   ```

**Verificación:**
```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); import redis; r = redis.from_url(os.getenv('CELERY_BROKER_URL')); r.ping(); print('✅ Redis connection válida')"
```

---

### 4. PostgreSQL Password 🟡 BAJA PRIORIDAD
**Expuesta:** `12122021` (localhost)

**Riesgo:** Solo accesible localmente, pero es buena práctica cambiarla

**PASOS:**
1. Abre pgAdmin o tu cliente PostgreSQL
2. Conéctate al servidor PostgreSQL
3. Click derecho en "postgres" user → "Properties"
4. Pestaña "Definition" → Cambia password
5. Usa un password fuerte (ej: generado aleatoriamente)
6. Actualiza `backend/.env`:
   ```bash
   DATABASE_URL=postgresql://postgres:NUEVO_PASSWORD@localhost:5432/bjj_academy
   ```

**Generador de password fuerte:**
```bash
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(24)))"
```

**Verificación:**
```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); engine.connect(); print('✅ PostgreSQL connection válida')"
```

---

### 5. Flask SECRET_KEY 🟡 BAJA PRIORIDAD
**Expuesta:** `dev-secret-key-change-in-production-123456789`

**Riesgo:** Sesiones de usuario podrían ser vulneradas

**PASOS:**
1. Genera una nueva SECRET_KEY:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Actualiza `backend/.env`:
   ```bash
   SECRET_KEY=NUEVO_SECRET_KEY_GENERADO
   ```

**NOTA:** Esto invalidará todas las sesiones activas de usuarios.

---

## 🔒 Paso 2: Asegurar el Repositorio

### Opción A: Mantener Historial (Recomendado para repos colaborativos)

```bash
# 1. Asegurar que .env está en .gitignore (ya está)
cat .gitignore | grep ".env"

# 2. Remover .env del tracking (sin borrar el archivo)
git rm --cached backend/.env

# 3. Commit el cambio
git add .gitignore
git commit -m "security: Remove .env from Git tracking (credentials rotated)"

# 4. Push
git push origin chatbotPostgre
```

**⚠️ IMPORTANTE:** El `.env` seguirá en el historial de Git, pero:
- Las credenciales YA fueron rotadas (inválidas)
- Nuevos commits NO tendrán el archivo
- Para limpieza completa del historial, ver Opción B

### Opción B: Limpiar Historial Completamente (Avanzado)

**⚠️ PELIGRO:** Esto reescribe la historia de Git y puede causar problemas si otros tienen clones.

```bash
# Usar BFG Repo-Cleaner o git filter-repo
# 1. Instalar BFG
# Windows: scoop install bfg
# Mac: brew install bfg

# 2. Clonar repo espejo
git clone --mirror https://github.com/javivarba/chatbots.git chatbots-mirror
cd chatbots-mirror

# 3. Limpiar .env del historial
bfg --delete-files .env

# 4. Limpiar refs
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 5. Force push (CUIDADO)
git push --force

# SOLO si estás seguro y no hay otros colaboradores
```

---

## 📝 Paso 3: Crear .env.example

Crea un archivo de ejemplo SIN credenciales reales:

```bash
# backend/.env.example
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=+1234567890

DATABASE_URL=postgresql://user:password@localhost:5432/dbname

REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_USERNAME=default

CELERY_BROKER_URL=redis://default:password@host:port/0
CELERY_RESULT_BACKEND=redis://default:password@host:port/1
```

Luego commit:
```bash
git add backend/.env.example
git commit -m "docs: Add .env.example template"
```

---

## ✅ Checklist de Verificación

Después de rotar todas las credenciales:

- [ ] OpenAI key antigua revocada
- [ ] OpenAI key nueva funciona
- [ ] Twilio auth token nuevo funciona
- [ ] Redis password cambiado y funciona
- [ ] PostgreSQL password cambiado (opcional)
- [ ] Flask SECRET_KEY generado
- [ ] `.env` removido de Git tracking
- [ ] `.env.example` creado y commiteado
- [ ] Sistema funciona con nuevas credenciales
- [ ] Tests pasan (`pytest`)
- [ ] Flujo completo funciona (`python test_flow_simple.py`)

---

## 🚀 Verificación Final

```bash
# Correr tests
cd backend
pytest

# Test manual del flujo
python test_flow_simple.py

# Verificar que .env NO está tracked
git status | grep ".env"  # Debe decir "untracked" o no aparecer
```

---

## 📞 Monitoreo Post-Rotación

**Primeras 24 horas:**
1. Monitorear uso de OpenAI API: https://platform.openai.com/usage
2. Monitorear Twilio usage: https://console.twilio.com/usage
3. Revisar logs de Redis para actividad sospechosa

**Si detectas actividad sospechosa:**
- Contacta soporte del servicio inmediatamente
- Revoca credenciales adicionales
- Cambia passwords de cuentas asociadas

---

## 📚 Referencias

- [OWASP Secret Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Git Filter Repo](https://github.com/newren/git-filter-repo)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [GitHub: Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)

---

**Generado:** $(date)
**Proyecto:** BJJ Academy Bot
**Estado:** 🔴 CREDENCIALES EXPUESTAS - ROTACIÓN URGENTE
