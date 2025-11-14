# Tests - BJJ Academy Bot

Suite completa de tests unitarios e integración para el BJJ Academy Bot.

## 📁 Estructura

```
tests/
├── unit/                           # Tests unitarios (66 tests)
│   ├── test_database.py           # Database utilities (17 tests)
│   ├── test_message_handler.py    # Message processing (18 tests)
│   ├── test_appointment_scheduler.py  # Booking system (15 tests)
│   └── test_dashboard_routes.py   # API endpoints (16 tests)
│
├── integration/                    # Tests de integración (11 tests)
│   ├── test_message_flow.py       # Flujo completo de mensajes (6 tests)
│   └── test_api_endpoints.py      # API endpoints integración (5 tests)
│
├── conftest.py                     # Fixtures compartidos
└── README.md                       # Esta documentación
```

## 🚀 Ejecutar Tests

### Todos los tests
```bash
cd backend
pytest
```

### Solo tests unitarios
```bash
pytest tests/unit/
```

### Solo tests de integración
```bash
pytest tests/integration/
```

### Tests específicos por módulo
```bash
# Database
pytest tests/unit/test_database.py

# Message Handler
pytest tests/unit/test_message_handler.py

# Appointment Scheduler
pytest tests/unit/test_appointment_scheduler.py

# Dashboard Routes
pytest tests/unit/test_dashboard_routes.py
```

### Con coverage
```bash
pytest --cov=app --cov-report=html
# Ver reporte en htmlcov/index.html
```

### Marcadores (markers)
```bash
# Solo tests de integración
pytest -m integration

# Excluir tests lentos
pytest -m "not slow"

# Solo tests unitarios
pytest -m unit
```

## 📊 Cobertura

### Tests Unitarios (66 tests)

#### Database Module (17 tests)
- ✅ `DatabaseConfig` - Singleton pattern y configuración
- ✅ `get_db_connection()` - Context manager para conexiones
- ✅ `get_db_cursor()` - Context manager con auto-commit/rollback
- ✅ Helper functions: `execute_query`, `execute_insert`, `execute_update`
- ✅ Utility functions: `table_exists`, `get_table_info`

#### Message Handler (18 tests)
- ✅ Inicialización y configuración
- ✅ Creación/obtención de leads
- ✅ Creación/obtención de conversaciones
- ✅ Guardado de mensajes
- ✅ Obtención de información (leads, academy)
- ✅ Historial de conversación
- ✅ Actualización de status de leads
- ✅ Procesamiento de mensajes (con mocks de OpenAI)

#### Appointment Scheduler (15 tests)
- ✅ Inicialización y carga de horarios
- ✅ Parseo de horas (AM/PM, 24h)
- ✅ Cálculo de próxima clase
- ✅ Booking de semana de prueba
- ✅ Prevención de duplicados
- ✅ Integración con notificaciones (mocked)
- ✅ Formateo de mensajes
- ✅ Flujos completos de integración

#### Dashboard Routes (16 tests)
- ✅ `/api/stats` - Estadísticas generales
- ✅ `/api/leads` - Lista de leads con filtros
- ✅ `/api/leads/<id>` - Detalle de lead
- ✅ `/api/leads/<id>/update-status` - Actualizar status
- ✅ `/api/leads/<id>/add-note` - Agregar notas
- ✅ `/api/appointments` - Lista de citas
- ✅ `determine_next_action()` - Lógica de próxima acción

### Tests de Integración (11 tests)

#### Message Flow (6 tests)
- ✅ Flujo completo para nuevo usuario
- ✅ Usuario existente consultando clases
- ✅ Booking de semana de prueba
- ✅ Prevención de duplicados
- ✅ Journey completo de usuario (saludo → consulta → booking)
- ✅ Mantenimiento de contexto en conversación

#### API Endpoints (5 tests)
- ✅ Stats con datos reales
- ✅ Gestión completa de lead (CRUD)
- ✅ Filtrado de leads
- ✅ Lista de appointments con info de leads
- ✅ Workflow completo (lead → appointment)

## 🔧 Fixtures Disponibles

### `test_db`
Base de datos temporal con schema completo. Se limpia después de cada test.

```python
def test_example(test_db):
    # test_db contiene path a BD temporal con tablas creadas
    execute_query("SELECT * FROM lead", db_path=test_db)
```

### `sample_lead`
Lead de prueba pre-creado.

```python
def test_with_lead(test_db, sample_lead):
    # sample_lead es el ID del lead creado
    assert sample_lead > 0
```

### `sample_conversation`
Conversación de prueba asociada a `sample_lead`.

```python
def test_with_conversation(test_db, sample_lead, sample_conversation):
    # sample_conversation es el ID de la conversación
    pass
```

### `mock_openai_client`
Mock de cliente OpenAI para tests sin API calls.

```python
def test_with_ai(mock_openai_client):
    # mock ya configurado con respuesta de prueba
    pass
```

### `mock_twilio_client`
Mock de cliente Twilio para tests sin enviar SMS reales.

```python
def test_with_twilio(mock_twilio_client):
    # mock ya configurado
    pass
```

## ⚠️ Notas Importantes

### SQLite en Windows
Los tests en batch pueden tener problemas de file locking en Windows. Cada test individual funciona correctamente.

**Solución recomendada para CI/CD:**
- Usar PostgreSQL en lugar de SQLite
- Ejecutar tests en Linux/Docker
- Ejecutar tests uno por uno en Windows si es necesario

### Mocks vs Real APIs
- **OpenAI**: Todos los tests usan mocks. No se hacen llamadas reales a la API.
- **Twilio**: Todos los tests usan mocks. No se envían SMS reales.
- **Database**: Se usa SQLite temporal real, no mocks.

### Variables de Entorno
Los tests usan variables de entorno mockeadas. No necesitas configurar `.env` para ejecutar tests.

## 📝 Agregar Nuevos Tests

### Test Unitario
```python
# tests/unit/test_my_module.py
import pytest
from app.my_module import MyClass

class TestMyClass:
    """Test MyClass functionality."""

    def test_my_method(self, test_db):
        """Test my_method does X."""
        obj = MyClass()
        obj.db_path = test_db

        result = obj.my_method()

        assert result == expected_value
```

### Test de Integración
```python
# tests/integration/test_my_flow.py
import pytest

@pytest.mark.integration
class TestMyFlow:
    """Test complete flow for X."""

    def test_complete_flow(self, test_db, mock_openai_client):
        """Test end-to-end flow."""
        # Setup
        # Execute
        # Verify
        pass
```

## 🎯 Próximos Pasos

- [ ] Agregar tests para notificaciones (cuando se implemente)
- [ ] Tests de performance/load
- [ ] Tests de seguridad
- [ ] Configurar CI/CD para ejecutar tests automáticamente
- [ ] Mejorar coverage a >90%

## 📚 Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/example/markers.html)
