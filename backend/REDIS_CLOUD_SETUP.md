# Configuración de Redis Cloud para BJJ Mingo

## 📋 Paso a Paso para Configurar Redis Cloud

### Paso 1: Obtener Credenciales de Redis Cloud

1. **Ir a tu base de datos en Redis Cloud:**
   - URL: https://cloud.redis.io/#/databases/13737802/subscription/2994291/view-bdb/configuration

2. **Copiar la información de conexión:**

   En la pestaña **"Configuration"** encontrarás:

   ```
   📍 Public Endpoint: redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345
   🔑 Default user password: ••••••••••••
   ```

   Desglosado:
   - **Host**: `redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com`
   - **Port**: `12345` (el número después de `:`)
   - **Password**: Click en "Show" para ver la contraseña
   - **Username**: `default` (usualmente)

3. **Opcional: Ver en Redis Insight**
   - Si tienes Redis Insight instalado, verás estos mismos datos

---

### Paso 2: Actualizar el archivo `.env`

Abre el archivo `backend/.env` y agrega/actualiza estas líneas:

```bash
# Redis Cloud Configuration
REDIS_HOST=redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com
REDIS_PORT=12345
REDIS_PASSWORD=tu_password_real_aqui
REDIS_USERNAME=default

# Celery URLs (se construyen con los valores de arriba)
CELERY_BROKER_URL=redis://default:tu_password_real_aqui@redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345/0
CELERY_RESULT_BACKEND=redis://default:tu_password_real_aqui@redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345/1
```

**IMPORTANTE:**
- Reemplaza `redis-12345...` con tu endpoint real
- Reemplaza `12345` con tu puerto real
- Reemplaza `tu_password_real_aqui` con tu contraseña real

---

### Paso 3: Verificar la Conexión

#### Opción A: Desde Python (Rápido)

```python
# Ejecutar en terminal
cd backend
python -c "
import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Intentar conectar
r = redis.from_url(os.getenv('CELERY_BROKER_URL'))
print('Conectando a Redis Cloud...')
response = r.ping()
print(f'Respuesta: {response}')
print('✅ Conexión exitosa!')
"
```

#### Opción B: Desde Redis CLI

```bash
redis-cli -h redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com -p 12345 -a tu_password ping
```

Si responde `PONG`, la conexión funciona.

---

### Paso 4: Ejecutar el Sistema

**¡Ya no necesitas Docker ni iniciar Redis local!**

Tu Redis Cloud ya está corriendo 24/7, solo necesitas ejecutar:

#### Windows (3 Terminales):

**Terminal 1 - Flask:**
```bash
cd backend
python run.py
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
start_celery_worker.bat
```

**Terminal 3 - Celery Beat:**
```bash
cd backend
start_celery_beat.bat
```

#### O TODO EN UNO:

```bash
cd backend
run_all_dev.bat
```

---

## 🔍 Verificar que Funciona con Redis Cloud

### Test 1: Verificar conexión desde Python

```python
cd backend
python

>>> import redis
>>> import os
>>> from dotenv import load_dotenv
>>> load_dotenv()
>>> r = redis.from_url(os.getenv('CELERY_BROKER_URL'))
>>> r.ping()
True
>>> print("✅ Redis Cloud conectado!")
```

### Test 2: Ejecutar test del sistema

```bash
cd backend
python test_reminders_system.py
```

Deberías ver:
```
[OK] PASS - Redis
```

### Test 3: Ver datos en Redis Insight

1. Abre Redis Insight (app o web)
2. Conecta a tu base de datos
3. Una vez que Celery esté corriendo, verás:
   - **Keys**: `celery-task-meta-*` (resultados de tareas)
   - **Keys**: Lista de tareas en cola

---

## 📊 Ventajas de Usar Redis Cloud vs Local

| Característica | Redis Cloud | Redis Local |
|----------------|-------------|-------------|
| Disponibilidad | 24/7 automático | Debes iniciarlo manualmente |
| Persistencia | Automática | Manual |
| Backups | Automáticos | Manual |
| Escalabilidad | Fácil | Limitado |
| Monitoreo | Redis Insight | Limitado |
| Setup | Una vez | Cada vez que reinicias PC |

---

## 🛠️ Troubleshooting Redis Cloud

### Error: "Connection refused" o "Timeout"

**Causa:** Firewall o credenciales incorrectas

**Solución:**
1. Verificar que copiaste bien el endpoint completo
2. Verificar que el password no tenga espacios extra
3. Verificar que tu IP está en la whitelist (en Redis Cloud)
   - Ve a: Database → Security → Source IP/Subnet → Add IP
   - Agrega: `0.0.0.0/0` (permite todas las IPs - solo para desarrollo)

### Error: "Authentication failed"

**Causa:** Password incorrecto

**Solución:**
1. Ve a Redis Cloud → Database → Configuration
2. Click en "Show" para ver el password real
3. Cópialo exactamente (sin espacios)
4. Pégalo en `.env`

### Error: "WRONGPASS invalid username-password pair"

**Causa:** Redis ACL habilitado con usuario incorrecto

**Solución:**
1. Cambiar `REDIS_USERNAME=default` a `REDIS_USERNAME=` (vacío)
2. O usar solo el password en la URL:
   ```
   CELERY_BROKER_URL=redis://:tu_password@host:port/0
   ```
   (nota los `:` antes del password)

### Ver si hay datos en Redis Cloud

Desde Redis Insight o CLI:
```bash
# Ver todas las keys
redis-cli -h tu-host -p tu-port -a tu-password KEYS '*'

# Contar keys
redis-cli -h tu-host -p tu-port -a tu-password DBSIZE

# Ver info
redis-cli -h tu-host -p tu-port -a tu-password INFO
```

---

## 📱 Monitoreo en Redis Insight

### Ver Tareas de Celery

1. **Abrir Redis Insight** (web o app)
2. **Conectar a tu database**
3. **Browser tab** → Verás:
   - `celery-task-meta-*`: Resultados de tareas
   - `_kombu.binding.*`: Bindings de Celery
   - Listas con nombres de colas

### Ver Recordatorios en Tiempo Real

Cuando Celery esté procesando recordatorios, verás en Redis Insight:

```
Key: celery-task-meta-abc123...
Value: {
  "status": "SUCCESS",
  "result": {"sent": 3, "failed": 0},
  ...
}
```

---

## 🔐 Seguridad - Producción

Para producción, configura:

1. **Whitelist de IPs** en Redis Cloud
   - Solo permitir IP de tu servidor

2. **Variables de entorno seguras**
   - NO subir `.env` a GitHub
   - Usar secrets del servidor

3. **SSL/TLS**
   - Redis Cloud soporta conexiones SSL
   - URL: `rediss://` (con doble 's')

---

## 📚 Recursos Adicionales

- **Redis Cloud Docs**: https://docs.redis.com/latest/rc/
- **Redis Insight Docs**: https://docs.redis.com/latest/ri/
- **Celery con Redis**: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html

---

## ✅ Checklist de Configuración

- [ ] Copié endpoint de Redis Cloud
- [ ] Copié password (sin espacios)
- [ ] Actualicé `.env` con credenciales
- [ ] Probé conexión con Python
- [ ] Test `test_reminders_system.py` pasa
- [ ] Puedo ver datos en Redis Insight
- [ ] Celery Worker conecta exitosamente
- [ ] Celery Beat ejecuta tareas

---

¡Con Redis Cloud configurado, tu sistema de recordatorios estará activo 24/7 sin necesidad de mantener Redis corriendo en tu máquina local! 🎉
