"""
Message Schemas para validación con Pydantic
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import html


class WhatsAppWebhookRequest(BaseModel):
    """
    Schema para webhook de WhatsApp (Twilio)

    Validaciones:
    - Body: mensaje sanitizado, max 4000 caracteres
    - From: número de teléfono
    - ProfileName: nombre del perfil (opcional)
    """
    Body: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Contenido del mensaje"
    )
    From: str = Field(
        ...,
        min_length=8,
        description="Número de teléfono del remitente"
    )
    ProfileName: Optional[str] = Field(
        None,
        max_length=100,
        description="Nombre del perfil de WhatsApp"
    )
    MessageSid: Optional[str] = Field(
        None,
        description="ID del mensaje de Twilio"
    )

    @field_validator('Body')
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        """
        Sanitizar mensaje para prevenir XSS
        Escapar HTML pero mantener contenido
        """
        sanitized = html.escape(v.strip())

        # Validar que no esté vacío después de sanitizar
        if not sanitized:
            raise ValueError('El mensaje no puede estar vacío')

        return sanitized

    @field_validator('From')
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        """Normalizar número de teléfono"""
        import re
        # Remover todo excepto dígitos y +
        normalized = re.sub(r'[^\d+]', '', v)

        # Validar formato mínimo
        if len(normalized) < 8:
            raise ValueError('Número de teléfono inválido')

        return normalized

    @field_validator('ProfileName')
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitizar nombre del perfil"""
        if v:
            return html.escape(v.strip())
        return v

    model_config = {
        "str_strip_whitespace": True,
        "populate_by_name": True,  # Permite usar alias
        "json_schema_extra": {
            "examples": [
                {
                    "Body": "Hola, quiero información",
                    "From": "whatsapp:+50670150369",
                    "ProfileName": "Juan Pérez",
                    "MessageSid": "SM1234567890"
                }
            ]
        }
    }


class IncomingMessageRequest(BaseModel):
    """
    Schema simplificado para mensajes entrantes procesados

    Después de pasar por el webhook, este es el formato interno
    """
    phone_number: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="Número de teléfono normalizado"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Contenido del mensaje sanitizado"
    )
    name: Optional[str] = Field(
        None,
        max_length=100,
        description="Nombre del usuario"
    )

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {
                    "phone_number": "+50670150369",
                    "message": "Quiero información sobre las clases",
                    "name": "Juan Pérez"
                }
            ]
        }
    }
