"""
Lead Schemas para validación con Pydantic
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


class UpdateLeadStatusRequest(BaseModel):
    """
    Schema para actualizar status de lead

    Validaciones:
    - status: debe ser uno de los valores permitidos
    """
    status: str = Field(
        ...,
        pattern=r'^(new|contacted|interested|scheduled|converted|lost)$',
        description="Nuevo status del lead"
    )

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {"status": "interested"},
                {"status": "scheduled"}
            ]
        }
    }


class AddLeadNoteRequest(BaseModel):
    """
    Schema para agregar nota a lead

    Validaciones:
    - note: 1-1000 caracteres, trimmed
    - sanitizado para prevenir XSS
    """
    note: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Contenido de la nota"
    )

    @field_validator('note')
    @classmethod
    def sanitize_note(cls, v: str) -> str:
        """Sanitizar nota para prevenir XSS"""
        import html
        # Escapar HTML pero mantener el contenido
        return html.escape(v.strip())

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {"note": "Cliente muy interesado, llamar mañana"},
                {"note": "Preguntó por clases de striking"}
            ]
        }
    }


class CreateLeadRequest(BaseModel):
    """
    Schema para crear lead manualmente

    Validaciones:
    - phone: formato válido, normalizado
    - name: max 100 caracteres
    - email: formato email válido (opcional)
    - source: whatsapp, web, phone, o referral
    """
    phone: str = Field(
        ...,
        min_length=8,
        max_length=20,
        pattern=r'^\+?[\d\s\-()]+$',
        description="Número de teléfono"
    )
    name: Optional[str] = Field(
        None,
        max_length=100,
        description="Nombre del lead"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email del lead"
    )
    source: str = Field(
        default='whatsapp',
        pattern=r'^(whatsapp|web|phone|referral)$',
        description="Origen del lead"
    )

    @field_validator('phone')
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        """Normalizar número de teléfono"""
        # Remover todo excepto dígitos y +
        normalized = re.sub(r'[^\d+]', '', v)

        # Validar que tenga al menos 8 dígitos
        digits_only = re.sub(r'[^\d]', '', normalized)
        if len(digits_only) < 8:
            raise ValueError('El teléfono debe tener al menos 8 dígitos')

        return normalized

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitizar nombre"""
        if v:
            import html
            return html.escape(v.strip())
        return v

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {
                    "phone": "+506 7015-0369",
                    "name": "Juan Pérez",
                    "email": "juan@example.com",
                    "source": "web"
                },
                {
                    "phone": "70150369",
                    "name": "María López",
                    "source": "referral"
                }
            ]
        }
    }


class LeadFilterRequest(BaseModel):
    """
    Schema para filtros de leads (query params)

    Validaciones:
    - status: opcional, debe ser valor válido
    - source: opcional, debe ser valor válido
    - limit: 1-1000 (protección contra queries grandes)
    """
    status: Optional[str] = Field(
        None,
        pattern=r'^(new|contacted|interested|scheduled|converted|lost)$',
        description="Filtrar por status"
    )
    source: Optional[str] = Field(
        None,
        pattern=r'^(whatsapp|web|phone|referral)$',
        description="Filtrar por fuente"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Número máximo de resultados"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Número de resultados a saltar"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"status": "interested", "limit": 50},
                {"source": "whatsapp", "limit": 100, "offset": 0}
            ]
        }
    }
