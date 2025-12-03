"""
Cache Schemas para validación con Pydantic
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class CacheInvalidateRequest(BaseModel):
    """
    Schema base para invalidar caché

    Validaciones:
    - action: pattern, keys, o all
    """
    action: str = Field(
        ...,
        pattern=r'^(pattern|keys|all)$',
        description="Tipo de invalidación"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"action": "all"},
                {"action": "pattern"},
                {"action": "keys"}
            ]
        }
    }


class CacheInvalidatePatternRequest(CacheInvalidateRequest):
    """
    Schema para invalidar caché por patrón

    Validaciones:
    - pattern: max 100 caracteres, formato seguro
    """
    action: str = Field(default="pattern", pattern=r'^pattern$')
    pattern: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Patrón para buscar keys (ej: lead:*)"
    )

    @field_validator('pattern')
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Validar que el patrón sea seguro"""
        # Solo permitir caracteres seguros
        import re
        if not re.match(r'^[a-zA-Z0-9:_*\-]+$', v):
            raise ValueError('Patrón contiene caracteres no permitidos')
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "action": "pattern",
                    "pattern": "lead:*"
                },
                {
                    "action": "pattern",
                    "pattern": "conversation:*"
                }
            ]
        }
    }


class CacheInvalidateKeysRequest(CacheInvalidateRequest):
    """
    Schema para invalidar caché por lista de keys específicas

    Validaciones:
    - keys: lista de 1-100 keys, cada una max 200 caracteres
    """
    action: str = Field(default="keys", pattern=r'^keys$')
    keys: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista de keys a invalidar"
    )

    @field_validator('keys')
    @classmethod
    def validate_keys(cls, v: List[str]) -> List[str]:
        """Validar cada key individualmente"""
        import re
        for key in v:
            # Validar longitud
            if len(key) > 200:
                raise ValueError(f'Key demasiado larga: {key[:50]}...')

            # Validar formato seguro
            if not re.match(r'^[a-zA-Z0-9:_\-]+$', key):
                raise ValueError(f'Key contiene caracteres no permitidos: {key}')

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "action": "keys",
                    "keys": ["lead:1", "lead:2", "conversation:5"]
                }
            ]
        }
    }
