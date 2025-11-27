# 🔐 RECOMENDACIONES DE SEGURIDAD PARA PRODUCCIÓN

**Fecha:** 24/11/2025
**Status:** 📋 Pre-Producción Security Audit
**Prioridad:** ⚠️ CRÍTICO - Implementar antes de producción

---

## 📋 TABLA DE CONTENIDOS

1. [Dashboard sin Autenticación](#1-dashboard-sin-autenticación)
2. [Falta de Repository Pattern](#2-falta-de-repository-pattern)
3. [Vulnerabilidad a Inyecciones](#3-vulnerabilidad-a-inyecciones)
4. [Vulnerabilidades Adicionales Detectadas](#4-vulnerabilidades-adicionales-detectadas)
5. [Plan de Implementación](#5-plan-de-implementación)

---

## 1. 🔓 DASHBOARD SIN AUTENTICACIÓN

### 🔴 VULNERABILIDAD CRÍTICA

**Severidad:** CRÍTICA
**Archivo afectado:** [`app/api/dashboard_routes.py`](app/api/dashboard_routes.py)

**Problema:**
```python
@dashboard_bp.route('/stats')  # ❌ SIN AUTENTICACIÓN
def get_stats():
    # Cualquiera puede acceder a datos sensibles
    return jsonify({
        'total_leads': total_leads,
        'conversion_rate': conversion_rate
    })
```

**Endpoints expuestos sin protección:**
```
GET  /api/stats                          → Estadísticas generales
GET  /api/leads                          → Lista completa de leads (nombres, teléfonos)
GET  /api/leads/<id>                     → Detalle de lead (conversaciones completas)
POST /api/leads/<id>/update-status       → Modificar status de leads
POST /api/leads/<id>/add-note            → Agregar notas
GET  /api/appointments                   → Lista de citas
POST /api/cache/clear                    → Limpiar caché (DoS potencial)
POST /api/cache/invalidate/*             → Invalidar caché
```

**Riesgo:**
- ✅ **Exposición de datos personales** (nombres, teléfonos, conversaciones)
- ✅ **GDPR/Privacy violations**
- ✅ **Modificación no autorizada** de datos
- ✅ **DoS attack** (limpieza masiva de caché)

---

### ✅ SOLUCIÓN RECOMENDADA: JWT Authentication

#### Opción 1: Flask-JWT-Extended (RECOMENDADO)

**Por qué Flask-JWT-Extended:**
- ✅ Mantiene a Flask
- ✅ JWT stateless (no requiere sesiones)
- ✅ Refresh tokens automáticos
- ✅ Fácil de implementar
- ✅ Producción-ready

**Instalación:**
```bash
pip install flask-jwt-extended
```

**Implementación:**

##### 1. Configuración Inicial

```python
# app/__init__.py
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)

    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # Cambiar en .env
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    jwt = JWTManager(app)

    # ... resto de configuración
```

##### 2. Modelo de Usuario

```python
# app/models/user.py
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='admin')  # admin, staff, readonly
    academy_id = db.Column(db.Integer, db.ForeignKey('academies.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

##### 3. Rutas de Autenticación

```python
# app/api/auth_routes.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login con username/password"""
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({'error': 'Username y password requeridos'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenciales inválidas'}), 401

    if not user.is_active:
        return jsonify({'error': 'Usuario inactivo'}), 403

    # Crear tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    # Actualizar último login
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Renovar access token usando refresh token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token})

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtener usuario actual"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    })
```

##### 4. Proteger Dashboard Routes

```python
# app/api/dashboard_routes.py
from flask_jwt_extended import jwt_required, get_jwt_identity

@dashboard_bp.route('/stats')
@jwt_required()  # ✅ PROTEGIDO
def get_stats():
    user_id = get_jwt_identity()
    # ... resto del código

@dashboard_bp.route('/leads')
@jwt_required()  # ✅ PROTEGIDO
def get_leads():
    user_id = get_jwt_identity()
    # ... resto del código

@dashboard_bp.route('/leads/<int:lead_id>/update-status', methods=['POST'])
@jwt_required()  # ✅ PROTEGIDO
def update_lead_status(lead_id):
    user_id = get_jwt_identity()
    # Verificar permisos
    # ... resto del código
```

##### 5. Role-Based Access Control (RBAC)

```python
# app/utils/decorators.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.user import User

def role_required(required_role):
    """Decorator para verificar rol del usuario"""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user:
                return jsonify({'error': 'Usuario no encontrado'}), 404

            if user.role != required_role and user.role != 'admin':
                return jsonify({'error': 'Permisos insuficientes'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Uso:
@dashboard_bp.route('/cache/clear', methods=['POST'])
@role_required('admin')  # ✅ SOLO ADMINS
def clear_cache():
    # Solo admins pueden limpiar caché
    pass
```

##### 6. Variables de Entorno

```env
# .env
JWT_SECRET_KEY=super-secret-cambiar-en-produccion-min-32-chars
```

**Generar secret key seguro:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

### 📊 Comparación de Opciones

| Feature | Flask-JWT-Extended | Flask-Login | OAuth2 |
|---------|-------------------|-------------|---------|
| Complejidad | Baja | Media | Alta |
| Stateless | ✅ Sí | ❌ No (sesiones) | ✅ Sí |
| Mobile-friendly | ✅ Sí | ❌ No | ✅ Sí |
| API REST | ✅ Perfecto | ⚠️ Regular | ✅ Perfecto |
| Refresh tokens | ✅ Sí | ❌ No | ✅ Sí |
| Producción-ready | ✅ Sí | ✅ Sí | ⚠️ Complejo |

**Recomendación:** Flask-JWT-Extended para tu caso de uso.

---

## 2. 🏗️ FALTA DE REPOSITORY PATTERN

### 🟡 VULNERABILIDAD MEDIA

**Severidad:** MEDIA (Deuda técnica + acoplamiento)
**Archivos afectados:**
- `dashboard_routes.py`
- `lead_manager.py`
- `conversation_manager.py`

**Problema:**

Acceso directo a SQLAlchemy en múltiples lugares:

```python
# ❌ ANTI-PATTERN: Acceso directo en routes
@dashboard_bp.route('/stats')
def get_stats():
    total_leads = Lead.query.count()  # Acoplamiento directo a SQLAlchemy
    status_counts = db.session.query(Lead.status, func.count(Lead.id))...
```

**Problemas:**
- ❌ **Acoplamiento alto** a SQLAlchemy
- ❌ **Difícil de testear** (requiere BD real)
- ❌ **Código duplicado** en múltiples lugares
- ❌ **Difícil de cambiar** BD o ORM
- ❌ **SQL injection potencial** si se usan strings dinámicos

---

### ✅ SOLUCIÓN RECOMENDADA: Repository Pattern

#### Por qué Repository Pattern:

- ✅ **Abstracción de persistencia** - Cambiar BD sin tocar lógica
- ✅ **Testabilidad** - Mock del repository fácilmente
- ✅ **Centralización** - Queries complejas en un solo lugar
- ✅ **Seguridad** - Validación centralizada
- ✅ **Mantenibilidad** - Un lugar para cambios

#### Implementación:

##### 1. Base Repository

```python
# app/repositories/base_repository.py
from typing import Generic, TypeVar, Optional, List
from app import db

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    Repository base con operaciones CRUD genéricas
    Abstrae SQLAlchemy del resto de la aplicación
    """

    def __init__(self, model_class: T):
        self.model_class = model_class

    def get_by_id(self, id: int) -> Optional[T]:
        """Obtener por ID"""
        return self.model_class.query.get(id)

    def get_all(self, limit: int = None) -> List[T]:
        """Obtener todos"""
        query = self.model_class.query
        if limit:
            query = query.limit(limit)
        return query.all()

    def filter_by(self, **kwargs) -> List[T]:
        """Filtrar por campos"""
        return self.model_class.query.filter_by(**kwargs).all()

    def create(self, **kwargs) -> T:
        """Crear nuevo registro"""
        instance = self.model_class(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, instance: T, **kwargs) -> T:
        """Actualizar registro existente"""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.updated_at = datetime.utcnow()
        db.session.commit()
        return instance

    def delete(self, instance: T) -> bool:
        """Eliminar registro"""
        try:
            db.session.delete(instance)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def count(self) -> int:
        """Contar registros"""
        return self.model_class.query.count()
```

##### 2. Lead Repository

```python
# app/repositories/lead_repository.py
from app.repositories.base_repository import BaseRepository
from app.models import Lead, LeadStatus
from datetime import datetime, timedelta
from typing import List, Optional

class LeadRepository(BaseRepository[Lead]):
    """Repository especializado para Leads"""

    def __init__(self):
        super().__init__(Lead)

    def get_by_phone(self, phone: str) -> Optional[Lead]:
        """Buscar lead por teléfono"""
        return self.model_class.query.filter_by(phone=phone).first()

    def get_by_status(self, status: LeadStatus) -> List[Lead]:
        """Obtener leads por status"""
        return self.model_class.query.filter_by(status=status).all()

    def get_scheduled(self) -> List[Lead]:
        """Obtener leads con clase agendada"""
        return self.model_class.query.filter(
            Lead.status == LeadStatus.SCHEDULED
        ).all()

    def get_needs_followup(self, days: int = 3) -> List[Lead]:
        """Obtener leads que necesitan seguimiento"""
        threshold = datetime.utcnow() - timedelta(days=days)
        return self.model_class.query.filter(
            Lead.status.notin_([LeadStatus.SCHEDULED, LeadStatus.CONVERTED]),
            (Lead.last_contact_date == None) | (Lead.last_contact_date < threshold)
        ).all()

    def get_stats(self) -> dict:
        """Obtener estadísticas de leads"""
        from sqlalchemy import func

        total = self.count()
        scheduled = self.model_class.query.filter_by(status=LeadStatus.SCHEDULED).count()
        needs_followup = len(self.get_needs_followup())

        status_counts = db.session.query(
            Lead.status, func.count(Lead.id)
        ).group_by(Lead.status).all()

        return {
            'total': total,
            'scheduled': scheduled,
            'needs_followup': needs_followup,
            'by_status': {status: count for status, count in status_counts},
            'conversion_rate': round((scheduled / total * 100) if total > 0 else 0, 1)
        }
```

##### 3. Actualizar Dashboard Routes

```python
# app/api/dashboard_routes.py
from app.repositories.lead_repository import LeadRepository
from flask_jwt_extended import jwt_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

# Inicializar repository
lead_repo = LeadRepository()

@dashboard_bp.route('/stats')
@jwt_required()  # ✅ PROTEGIDO
def get_stats():
    """Obtener estadísticas - USANDO REPOSITORY"""
    stats = lead_repo.get_stats()  # ✅ Sin acceso directo a SQLAlchemy
    return jsonify(stats)

@dashboard_bp.route('/leads')
@jwt_required()  # ✅ PROTEGIDO
def get_leads():
    """Obtener leads - USANDO REPOSITORY"""
    status_filter = request.args.get('status')

    if status_filter:
        leads = lead_repo.get_by_status(status_filter)
    else:
        leads = lead_repo.get_all()

    # Formatear respuesta
    return jsonify([format_lead(lead) for lead in leads])
```

##### 4. Actualizar LeadManager

```python
# app/services/lead_manager.py
from app.repositories.lead_repository import LeadRepository

class LeadManager:
    """Manager de leads - USA REPOSITORY"""

    def __init__(self):
        self.repository = LeadRepository()  # ✅ Dependency Injection

    def get_or_create(self, phone: str, name: str = None) -> int:
        """Obtener o crear lead"""
        lead = self.repository.get_by_phone(phone)

        if not lead:
            lead = self.repository.create(
                phone=phone,
                name=name,
                status=LeadStatus.NEW,
                source='whatsapp'
            )

        return lead.id
```

---

## 3. 💉 VULNERABILIDAD A INYECCIONES

### 🟡 VULNERABILIDAD MEDIA-ALTA

**Severidad:** MEDIA-ALTA
**Archivos afectados:** Todos los que usan input de usuario

### 3.1 SQL Injection

**Estado actual:** ✅ **PROTEGIDO** (gracias a SQLAlchemy ORM)

SQLAlchemy usa **parámetros preparados** automáticamente:

```python
# ✅ SEGURO: SQLAlchemy parametriza automáticamente
Lead.query.filter_by(phone=phone_number).first()

# ✅ SEGURO: Parámetros son escapados
Lead.query.filter(Lead.status == user_input).all()
```

**⚠️ PELIGRO:** Si usas SQL raw:

```python
# ❌ VULNERABLE a SQL Injection
db.session.execute(f"SELECT * FROM leads WHERE phone = '{phone}'")

# ✅ SEGURO: Usar parámetros
db.session.execute(
    "SELECT * FROM leads WHERE phone = :phone",
    {'phone': phone}
)
```

**Recomendación:** ✅ **Mantener uso de ORM**, nunca usar SQL raw con f-strings.

---

### 3.2 Command Injection

**⚠️ RIESGO POTENCIAL**

Verifica si hay uso de `os.system()`, `subprocess`, `eval()`:

```python
# ❌ VULNERABLE
import os
filename = request.json.get('filename')
os.system(f"cat {filename}")  # Command injection!

# ✅ SEGURO
import subprocess
subprocess.run(['cat', filename], check=True)  # Lista de args, no shell
```

**Auditoría realizada:** No encontré uso de `os.system()` o `eval()` en tu código actual. ✅

---

### 3.3 NoSQL Injection (Redis)

**⚠️ RIESGO EN CACHE**

```python
# app/services/cache_service.py

# ⚠️ POTENCIAL RIESGO
def get(self, key):
    # Si 'key' viene de input de usuario sin validar...
    return redis_client.get(key)

# ✅ SEGURO: Validar formato de key
def get(self, key):
    # Validar que key tenga formato esperado
    if not re.match(r'^[a-zA-Z0-9:_-]+$', key):
        raise ValueError("Invalid cache key format")
    return redis_client.get(key)
```

**Recomendación:**

```python
# app/services/cache_service.py
import re

class CacheService:
    VALID_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9:_-]+$')

    def _validate_key(self, key: str) -> bool:
        """Validar formato de key de caché"""
        if not self.VALID_KEY_PATTERN.match(key):
            raise ValueError(f"Invalid cache key format: {key}")
        return True

    def get(self, key: str):
        self._validate_key(key)  # ✅ Validar antes de usar
        return self.redis.get(key)

    def set(self, key: str, value, ttl=3600):
        self._validate_key(key)  # ✅ Validar antes de usar
        return self.redis.setex(key, ttl, value)
```

---

### 3.4 XSS (Cross-Site Scripting)

**Estado:** ✅ **PROTEGIDO** (API REST sin renderizado HTML)

Tu backend es API REST (JSON), no renderiza HTML directamente.

**⚠️ RIESGO:** Si el frontend no sanitiza al mostrar mensajes:

```javascript
// ❌ VULNERABLE en frontend
document.innerHTML = message.content;  // XSS!

// ✅ SEGURO en frontend
document.textContent = message.content;
// O usar framework como React que sanitiza automáticamente
```

**Recomendación:** Documentar que el frontend debe sanitizar contenido HTML.

---

### 3.5 Path Traversal

**Estado:** ✅ **NO APLICA** (no hay lectura de archivos desde input de usuario)

No encontré código que lea archivos basado en input de usuario.

---

## 4. 🔍 VULNERABILIDADES ADICIONALES DETECTADAS

### 4.1 Secrets en Código

**🔴 CRÍTICO**

**Problema:**

```python
# ❌ EXPUESTO: Secrets en .env commitado
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
REDIS_PASSWORD=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Solución:**

1. **Rotar TODOS los secrets inmediatamente**
2. **Usar .env.example en lugar de .env en git**
3. **Agregar .env a .gitignore** (verificar que esté)
4. **Usar gestores de secrets en producción:**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Google Secret Manager

```bash
# .gitignore
*.env
.env.local
.env.production
```

---

### 4.2 Rate Limiting

**🟡 VULNERABILIDAD MEDIA**

**Problema:** No hay rate limiting en endpoints

**Riesgo:**
- DoS attacks
- Brute force en login
- Spam de API

**Solución: Flask-Limiter**

```bash
pip install Flask-Limiter
```

```python
# app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL')  # Usar Redis para tracking
)

# app/api/auth_routes.py
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # ✅ Max 5 intentos por minuto
def login():
    # ...
```

---

### 4.3 CORS No Configurado

**🟡 VULNERABILIDAD MEDIA**

**Problema:** CORS puede estar abierto o no configurado

**Solución:**

```bash
pip install flask-cors
```

```python
# app/__init__.py
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # Configurar CORS restrictivo
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://tudominio.com",
                "https://www.tudominio.com"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
```

---

### 4.4 Logging de Datos Sensibles

**🟡 VULNERABILIDAD MEDIA**

**Problema:** Logs pueden contener datos sensibles

```python
# ❌ VULNERABLE
logger.info(f"Login attempt: {username}, {password}")  # Password en logs!
logger.info(f"Lead created: {lead.phone}, {lead.email}")  # PII en logs!
```

**Solución:**

```python
# ✅ SEGURO
logger.info(f"Login attempt: {username}")  # Sin password
logger.info(f"Lead created: ID {lead.id}")  # Sin PII

# O usar enmascaramiento
def mask_phone(phone):
    return phone[:3] + "****" + phone[-2:] if phone else None

logger.info(f"Lead created: {mask_phone(lead.phone)}")
```

---

### 4.5 HTTPS/TLS

**🔴 CRÍTICO EN PRODUCCIÓN**

**Recomendación:**
- ✅ Usar HTTPS en producción (Let's Encrypt gratuito)
- ✅ Redirigir HTTP → HTTPS
- ✅ HSTS headers

```python
# app/__init__.py
@app.before_request
def before_request():
    if not request.is_secure and app.config['ENV'] == 'production':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
```

---

### 4.6 Input Validation

**🟡 VULNERABILIDAD MEDIA**

**Problema:** Falta validación de inputs

**Solución: Pydantic o Marshmallow**

```bash
pip install pydantic
```

```python
# app/schemas/lead_schema.py
from pydantic import BaseModel, validator, Field
import re

class LeadCreateSchema(BaseModel):
    phone: str = Field(..., min_length=8, max_length=15)
    name: str = Field(None, max_length=100)
    email: str = Field(None, regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')

    @validator('phone')
    def validate_phone(cls, v):
        # Validar formato de teléfono
        if not re.match(r'^\+?[0-9]{8,15}$', v):
            raise ValueError('Invalid phone format')
        return v

# Uso en routes:
@dashboard_bp.route('/leads', methods=['POST'])
@jwt_required()
def create_lead():
    try:
        data = LeadCreateSchema(**request.json)  # ✅ Valida automáticamente
        lead = lead_repo.create(**data.dict())
        return jsonify({'id': lead.id}), 201
    except ValidationError as e:
        return jsonify({'errors': e.errors()}), 400
```

---

## 5. 📋 PLAN DE IMPLEMENTACIÓN

### Fase 1: CRÍTICO (Antes de producción)

**Prioridad 1 - Implementar AHORA:**

1. **✅ Autenticación JWT** (2-3 días)
   - Instalar Flask-JWT-Extended
   - Crear modelo User
   - Implementar login/refresh
   - Proteger todos los endpoints del dashboard
   - Crear usuario admin inicial

2. **✅ Rotar Secrets** (1 hora)
   - Generar nuevos API keys (OpenAI, Twilio)
   - Generar nuevo JWT_SECRET_KEY
   - Actualizar Redis password
   - Remover .env de git history

3. **✅ HTTPS** (1 día)
   - Configurar certificado SSL (Let's Encrypt)
   - Forzar HTTPS en producción
   - Configurar HSTS headers

4. **✅ Rate Limiting** (1 día)
   - Instalar Flask-Limiter
   - Configurar límites en login (5/min)
   - Configurar límites en API (50/hora)

---

### Fase 2: IMPORTANTE (Primera semana)

**Prioridad 2:**

5. **✅ Repository Pattern** (3-4 días)
   - Implementar BaseRepository
   - Crear LeadRepository
   - Crear ConversationRepository
   - Migrar LeadManager a usar repository
   - Migrar dashboard_routes a usar repository

6. **✅ Input Validation** (2 días)
   - Instalar Pydantic
   - Crear schemas para Lead, User, etc.
   - Validar inputs en todos los endpoints

7. **✅ CORS Configuración** (1 hora)
   - Instalar Flask-CORS
   - Configurar origins permitidos
   - Configurar headers permitidos

8. **✅ Logging Seguro** (1 día)
   - Implementar enmascaramiento de PII
   - Remover logs de passwords
   - Configurar niveles de log apropiados

---

### Fase 3: MEJORAS (Segunda semana)

**Prioridad 3:**

9. **✅ Auditoría de Seguridad** (2 días)
   - Scan de dependencias (safety, bandit)
   - OWASP ZAP scanning
   - Penetration testing manual

10. **✅ Monitoring y Alertas** (2 días)
    - Sentry para error tracking
    - Logs centralizados (CloudWatch, Datadog)
    - Alertas de intentos de login fallidos

11. **✅ Backup y Recovery** (1 día)
    - Backup automático de PostgreSQL
    - Plan de disaster recovery
    - Testing de restore

---

## 📊 CHECKLIST DE SEGURIDAD PRE-PRODUCCIÓN

### Autenticación y Autorización
- [ ] JWT implementado en todos los endpoints del dashboard
- [ ] Usuario admin creado con password fuerte
- [ ] Refresh tokens configurados
- [ ] Role-based access control implementado
- [ ] Endpoints sensibles requieren rol admin

### Secrets y Configuración
- [ ] Todos los secrets rotados
- [ ] .env en .gitignore
- [ ] .env.example documentado
- [ ] JWT_SECRET_KEY generado (min 32 chars)
- [ ] Secrets manager configurado (producción)

### Red y Comunicación
- [ ] HTTPS configurado
- [ ] HTTP → HTTPS redirect
- [ ] HSTS headers configurados
- [ ] CORS configurado restrictivamente
- [ ] Rate limiting en login y API

### Datos y Persistencia
- [ ] Repository pattern implementado
- [ ] Input validation con Pydantic
- [ ] SQL queries parametrizadas (ORM)
- [ ] Cache keys validadas
- [ ] Backup automático configurado

### Logging y Monitoring
- [ ] PII enmascarado en logs
- [ ] Passwords nunca loggeados
- [ ] Error tracking (Sentry)
- [ ] Alertas de seguridad configuradas
- [ ] Logs centralizados

### Testing
- [ ] Tests de seguridad (SQL injection, XSS, etc.)
- [ ] Penetration testing realizado
- [ ] Dependency scan (safety check)
- [ ] OWASP ZAP scan
- [ ] Load testing con rate limits

---

## 🛠️ HERRAMIENTAS RECOMENDADAS

### Seguridad
```bash
# Scan de dependencias vulnerables
pip install safety
safety check

# Static analysis
pip install bandit
bandit -r app/

# OWASP Dependency Check
pip install owasp-dependency-check
```

### Testing de Seguridad
- **OWASP ZAP** - Web app security scanner
- **Burp Suite Community** - Manual penetration testing
- **sqlmap** - SQL injection testing

---

## 📚 REFERENCIAS

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Flask-JWT-Extended Docs](https://flask-jwt-extended.readthedocs.io/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

---

**Última actualización:** 24/11/2025
**Próxima revisión:** Antes de deployment a producción
