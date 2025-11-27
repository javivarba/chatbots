# Repository Pattern - BJJ Academy Bot

## ✅ Implementación Completada

**Fecha:** 25 de noviembre de 2025
**Status:** Implementación completa y testeada exitosamente

---

## 📋 Resumen Ejecutivo

Se implementó el **Repository Pattern** para abstraer la capa de acceso a datos del BJJ Academy Bot. La implementación incluye:

- ✅ BaseRepository genérico con operaciones CRUD
- ✅ 5 repositorios especializados (User, Lead, Conversation, Message, Academy)
- ✅ Refactorización completa de auth_routes y dashboard_routes
- ✅ Tests automatizados pasando

**Resultado:** Código más limpio, testeable y mantenible.

---

## 🎯 ¿Qué es el Repository Pattern?

El **Repository Pattern** es un patrón de diseño que **abstrae la lógica de acceso a datos** de la lógica de negocio.

### Sin Repository Pattern (Antes)

```python
# Acceso directo a la base de datos en el controller
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    user = User.query.filter_by(username=username).first()  # ❌ Acoplamiento directo

    if user and user.check_password(password):
        user.last_login = datetime.utcnow()
        db.session.commit()  # ❌ Lógica de persistencia mezclada
        return jsonify({'token': create_token(user.id)})
```

### Con Repository Pattern (Ahora)

```python
# Abstracción con repository
user_repo = UserRepository()

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    user = user_repo.find_by_username(username)  # ✅ Abstracción clara

    if user and user.check_password(password):
        user = user_repo.update_last_login(user)  # ✅ Repository maneja persistencia
        return jsonify({'token': create_token(user.id)})
```

---

## 🏗️ Arquitectura

### Estructura de Carpetas

```
backend/
└── app/
    ├── models/           # Modelos SQLAlchemy
    │   ├── user.py
    │   ├── lead.py
    │   └── conversation.py
    │
    └── repositories/     # 🆕 Capa de repositorios
        ├── __init__.py
        ├── base_repository.py           # Generic CRUD
        ├── user_repository.py           # User-specific queries
        ├── lead_repository.py           # Lead-specific queries
        ├── conversation_repository.py   # Conversation + Message
        └── academy_repository.py        # Academy + TeamMember
```

### Capas de la Aplicación

```
┌────────────────────────────────────────┐
│         ROUTES (Controllers)           │  ← auth_routes.py, dashboard_routes.py
│  @app.route('/api/users')              │
│  def get_users():                      │
│      users = user_repo.get_all()       │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│         REPOSITORIES (Data Layer)      │  ← user_repository.py, lead_repository.py
│  class UserRepository:                 │
│      def get_all(self):                │
│          return User.query.all()       │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│         MODELS (SQLAlchemy ORM)        │  ← user.py, lead.py
│  class User(db.Model):                 │
│      id = db.Column(db.Integer, ...)   │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│         DATABASE (PostgreSQL)          │
│  users table, leads table, etc.        │
└────────────────────────────────────────┘
```

---

## 📚 Repositorios Implementados

### 1. BaseRepository (Genérico)

**Ubicación:** `app/repositories/base_repository.py`

**Operaciones CRUD:**

```python
class BaseRepository(Generic[T]):
    # CREATE
    create(**attributes) → T
    bulk_create(entities_data) → List[T]

    # READ
    get_by_id(id) → Optional[T]
    get_all(limit, offset) → List[T]
    find_by(**filters) → List[T]
    find_one_by(**filters) → Optional[T]

    # UPDATE
    update(entity, **attributes) → T
    refresh(entity) → T

    # DELETE
    delete(entity) → bool
    delete_by_id(id) → bool

    # UTILITIES
    count(**filters) → int
    exists(**filters) → bool
```

**Ejemplo de Uso:**

```python
# Cualquier repository hereda de BaseRepository
class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

# Usar métodos genéricos
user_repo = UserRepository()
user = user_repo.get_by_id(1)
all_users = user_repo.get_all()
admin_users = user_repo.find_by(role='admin')
```

### 2. UserRepository

**Ubicación:** `app/repositories/user_repository.py`

**Métodos Personalizados:**

```python
class UserRepository(BaseRepository[User]):
    # Find methods
    find_by_username(username) → Optional[User]
    find_by_email(email) → Optional[User]
    find_active_users() → List[User]
    find_by_role(role) → List[User]
    find_by_academy(academy_id) → List[User]

    # Create methods
    create_user(username, email, password, role, academy_id) → User

    # Update methods
    update_password(user, new_password) → User
    update_last_login(user) → User
    activate_user(user) → User
    deactivate_user(user) → User

    # Check methods
    username_exists(username) → bool
    email_exists(email) → bool
```

**Ejemplo de Uso:**

```python
user_repo = UserRepository()

# Login
user = user_repo.find_by_username('admin')
if user and user.check_password(password):
    user = user_repo.update_last_login(user)

# Create user
new_user = user_repo.create_user(
    username='javi',
    email='javi@academy.com',
    password='SecurePass123',
    role='staff'
)

# Check existence
if user_repo.username_exists('javi'):
    print("Username already taken")
```

### 3. LeadRepository

**Ubicación:** `app/repositories/lead_repository.py`

**Métodos Personalizados:**

```python
class LeadRepository(BaseRepository[Lead]):
    # Find methods
    find_by_phone(phone) → Optional[Lead]
    find_by_status(status, limit) → List[Lead]
    find_by_academy(academy_id) → List[Lead]
    find_scheduled_leads() → List[Lead]
    find_needs_followup(days=3) → List[Lead]
    find_hot_leads(min_score=7) → List[Lead]
    get_recent_leads(limit=10) → List[Lead]

    # Create methods
    create_lead(phone, name, source, academy_id) → Lead

    # Update methods
    update_status(lead, new_status) → Lead
    update_lead_score(lead, score) → Lead
    schedule_trial_class(lead, trial_date) → Lead
    update_last_contact(lead) → Lead

    # Stats methods
    count_by_status() → dict
    phone_exists(phone) → bool
```

**Ejemplo de Uso:**

```python
lead_repo = LeadRepository()

# Get dashboard stats
total_leads = lead_repo.count()
hot_leads = lead_repo.find_hot_leads(min_score=8)
needs_followup = lead_repo.find_needs_followup(days=3)
status_counts = lead_repo.count_by_status()

# Update lead
lead = lead_repo.find_by_phone('+1234567890')
lead = lead_repo.update_status(lead, LeadStatus.SCHEDULED)
lead = lead_repo.update_lead_score(lead, 9)
```

### 4. ConversationRepository + MessageRepository

**Ubicación:** `app/repositories/conversation_repository.py`

**ConversationRepository:**

```python
class ConversationRepository(BaseRepository[Conversation]):
    find_by_lead(lead_id) → List[Conversation]
    find_active_conversation(lead_id) → Optional[Conversation]
    get_or_create_conversation(lead_id) → Conversation
    close_conversation(conversation) → Conversation
    reopen_conversation(conversation) → Conversation
    update_last_message_time(conversation) → Conversation
```

**MessageRepository:**

```python
class MessageRepository(BaseRepository[Message]):
    find_by_conversation(conversation_id, limit, offset) → List[Message]
    get_conversation_history(conversation_id, limit=10) → List[Message]
    get_last_message(conversation_id) → Optional[Message]
    create_message(conversation_id, content, direction) → Message
    count_messages_in_conversation(conversation_id) → int
    find_inbound_messages(conversation_id) → List[Message]
    find_outbound_messages(conversation_id) → List[Message]
```

**Ejemplo de Uso:**

```python
conv_repo = ConversationRepository()
msg_repo = MessageRepository()

# Get or create conversation
conversation = conv_repo.get_or_create_conversation(lead_id=1)

# Add message
msg_repo.create_message(
    conversation_id=conversation.id,
    content="Hola! Quiero información sobre las clases",
    direction=MessageDirection.INBOUND
)

# Get conversation history
history = msg_repo.get_conversation_history(conversation.id, limit=10)
last_msg = msg_repo.get_last_message(conversation.id)
```

### 5. AcademyRepository + TeamMemberRepository

**Ubicación:** `app/repositories/academy_repository.py`

**AcademyRepository:**

```python
class AcademyRepository(BaseRepository[Academy]):
    find_by_name(name) → Optional[Academy]
    get_first_academy() → Optional[Academy]
    create_academy(name, location, phone, schedule) → Academy
```

**TeamMemberRepository:**

```python
class TeamMemberRepository(BaseRepository[TeamMember]):
    find_by_academy(academy_id) → List[TeamMember]
    find_by_name(name) → Optional[TeamMember]
    create_team_member(academy_id, name, role, bio) → TeamMember
    get_academy_instructors(academy_id) → List[TeamMember]
```

---

## 🔄 Refactorización Realizada

### auth_routes.py

**Antes:**
```python
from app import db
from app.models.user import User

user = User.query.filter_by(username=username).first()
user.last_login = datetime.utcnow()
db.session.commit()
```

**Después:**
```python
from app.repositories.user_repository import UserRepository

user_repo = UserRepository()

user = user_repo.find_by_username(username)
user = user_repo.update_last_login(user)
```

### dashboard_routes.py

**Antes:**
```python
from app import db
from app.models import Lead

total_leads = Lead.query.count()
scheduled = Lead.query.filter(Lead.status == LeadStatus.SCHEDULED).count()
```

**Después:**
```python
from app.repositories.lead_repository import LeadRepository

lead_repo = LeadRepository()

total_leads = lead_repo.count()
scheduled = lead_repo.count(status=LeadStatus.SCHEDULED)
```

---

## ✅ Beneficios del Repository Pattern

### 1. **Separación de Responsabilidades**

```python
# ❌ Antes: Controller conoce detalles de la BD
@app.route('/users')
def get_users():
    users = User.query.filter_by(is_active=True).order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])

# ✅ Ahora: Controller delega en repository
@app.route('/users')
def get_users():
    users = user_repo.find_active_users()
    return jsonify([u.to_dict() for u in users])
```

### 2. **Testabilidad**

```python
# Fácil de mockear en tests
def test_login():
    # Mock repository
    mock_repo = Mock(spec=UserRepository)
    mock_repo.find_by_username.return_value = fake_user

    # Test controller con mock
    response = login_controller(mock_repo)
    assert response.status_code == 200
```

### 3. **Reusabilidad**

```python
# Mismas queries reutilizadas en múltiples lugares
# Dashboard
hot_leads = lead_repo.find_hot_leads()

# API endpoint
hot_leads = lead_repo.find_hot_leads()

# Background task
hot_leads = lead_repo.find_hot_leads()
```

### 4. **Cambios Centralizados**

```python
# Cambiar query solo en un lugar
class LeadRepository:
    def find_hot_leads(self, min_score=7):
        # Cambiar de >= 7 a >= 8
        return self.find_by(lead_score__gte=8)  # ✅ Cambio en un solo lugar
```

### 5. **Queries Complejas Encapsuladas**

```python
# Query compleja escondida en repository
def find_needs_followup(self, days=3):
    cutoff_date = datetime.now() - timedelta(days=days)
    return db.session.query(Lead).filter(
        and_(
            Lead.status.notin_([LeadStatus.SCHEDULED, LeadStatus.CONVERTED]),
            or_(
                Lead.last_contact_date == None,
                Lead.last_contact_date < cutoff_date
            )
        )
    ).all()

# Controller simple
needs_followup = lead_repo.find_needs_followup(days=3)  # ✅ Fácil de entender
```

---

## 📊 Métricas de Implementación

### Archivos Creados

- ✅ `app/repositories/__init__.py`
- ✅ `app/repositories/base_repository.py` (250 líneas)
- ✅ `app/repositories/user_repository.py` (150 líneas)
- ✅ `app/repositories/lead_repository.py` (200 líneas)
- ✅ `app/repositories/conversation_repository.py` (180 líneas)
- ✅ `app/repositories/academy_repository.py` (100 líneas)

**Total:** ~880 líneas de código de repositorios

### Archivos Refactorizados

- ✅ `app/api/auth_routes.py` - 4 endpoints refactorizados
- ✅ `app/api/dashboard_routes.py` - 6 endpoints refactorizados

### Tests

- ✅ `test_auth_flow.py` - Todos los tests pasan ✓
- ✅ Dashboard routes funcionando correctamente ✓

---

## 🚀 Uso en Nuevos Endpoints

### Template para Nuevos Endpoints

```python
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.repositories.user_repository import UserRepository

bp = Blueprint('users', __name__)
user_repo = UserRepository()

@bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all active users"""
    users = user_repo.find_active_users()
    return jsonify([user.to_dict() for user in users])

@bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get user by ID"""
    user = user_repo.get_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict())

@bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create new user"""
    data = request.json

    # Validate
    if user_repo.username_exists(data['username']):
        return jsonify({'error': 'Username already exists'}), 400

    # Create using repository
    user = user_repo.create_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role=data.get('role', 'staff')
    )

    return jsonify(user.to_dict()), 201
```

---

## 🔮 Próximos Pasos (Opcional)

### 1. Actualizar Services

Migrar `app/services/` para usar repositorios:

```python
# message_processor.py
class MessageProcessor:
    def __init__(self):
        self.lead_repo = LeadRepository()
        self.conv_repo = ConversationRepository()
        self.msg_repo = MessageRepository()
```

### 2. Unit Tests para Repositorios

```python
# test_repositories.py
def test_user_repository_find_by_username():
    repo = UserRepository()
    user = repo.find_by_username('admin')
    assert user is not None
    assert user.username == 'admin'
```

### 3. Repository Interfaces (Type Hints)

```python
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        pass
```

---

## 📝 Changelog

### v1.0.0 - 25 de noviembre de 2025

- ✅ Implementación completa de BaseRepository
- ✅ 5 repositorios especializados creados
- ✅ auth_routes refactorizado
- ✅ dashboard_routes refactorizado
- ✅ Todos los tests pasando
- ✅ Documentación completa

---

**Implementado por:** Claude (Anthropic)
**Revisado por:** Javi
**Fecha:** 25 de noviembre de 2025

✅ **REPOSITORY PATTERN IMPLEMENTADO EXITOSAMENTE**
