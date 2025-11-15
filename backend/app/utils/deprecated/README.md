# Deprecated Utilities

Este directorio contiene utilidades obsoletas que ya no se usan en producción pero se mantienen por compatibilidad con tests antiguos.

## `database.py`

**DEPRECATED** - Ya no se usa en producción.

- **Razón:** Migrado completamente a SQLAlchemy ORM
- **Fecha de deprecación:** Noviembre 2025
- **Reemplazo:** Usar `app.models` y SQLAlchemy directamente
- **Tests que lo usan:** `tests/unit/test_database.py` (solo para testear el código legacy)

### Migración

Si necesitas usar funcionalidad de base de datos, usa SQLAlchemy:

```python
# Antes (SQLite directo - DEPRECATED)
from app.utils.database import execute_query
leads = execute_query("SELECT * FROM leads WHERE status = ?", ('new',))

# Ahora (SQLAlchemy - RECOMENDADO)
from app.models import Lead, LeadStatus
leads = Lead.query.filter_by(status=LeadStatus.NEW).all()
```

## Eliminación Futura

Estos archivos se eliminarán completamente en una versión futura cuando:
1. Todos los tests legacy se migren a SQLAlchemy
2. No haya referencias en el código de producción
3. Se confirme que no hay dependencias externas
