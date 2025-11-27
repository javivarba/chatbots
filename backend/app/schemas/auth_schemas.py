"""
Authentication Schemas para validación con Pydantic
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


class LoginRequest(BaseModel):
    """
    Schema para login

    Validaciones:
    - username: 3-80 caracteres, trimmed
    - password: 8-128 caracteres
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=80,
        description="Nombre de usuario"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password del usuario"
    )

    model_config = {
        "str_strip_whitespace": True,  # Auto-trim espacios
        "json_schema_extra": {
            "examples": [
                {
                    "username": "admin",
                    "password": "Admin123456"
                }
            ]
        }
    }


class RefreshTokenRequest(BaseModel):
    """
    Schema para refresh token (si se necesita body en el futuro)
    Por ahora el refresh token va en el header
    """
    pass


class ChangePasswordRequest(BaseModel):
    """
    Schema para cambio de password

    Validaciones:
    - current_password: min 8 caracteres
    - new_password: min 8 caracteres, debe contener letra y número
    """
    current_password: str = Field(
        ...,
        min_length=8,
        description="Password actual"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Nuevo password"
    )

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validar fortaleza del password"""
        if not any(c.isdigit() for c in v):
            raise ValueError('El password debe contener al menos un número')
        if not any(c.isalpha() for c in v):
            raise ValueError('El password debe contener al menos una letra')
        return v

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {
                    "current_password": "OldPassword123",
                    "new_password": "NewPassword456"
                }
            ]
        }
    }


class CreateUserRequest(BaseModel):
    """
    Schema para crear usuario

    Validaciones:
    - username: 3-80 caracteres, único
    - email: formato email válido
    - password: min 8 caracteres con letra y número
    - role: admin, staff, o readonly
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=80,
        description="Nombre de usuario (único)"
    )
    email: EmailStr = Field(
        ...,
        description="Email del usuario (único)"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password del usuario"
    )
    role: str = Field(
        default='staff',
        pattern=r'^(admin|staff|readonly)$',
        description="Rol del usuario"
    )
    academy_id: Optional[int] = Field(
        default=None,
        description="ID de la academia asociada"
    )

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validar fortaleza del password"""
        if not any(c.isdigit() for c in v):
            raise ValueError('El password debe contener al menos un número')
        if not any(c.isalpha() for c in v):
            raise ValueError('El password debe contener al menos una letra')
        return v

    @field_validator('username')
    @classmethod
    def username_valid(cls, v: str) -> str:
        """Validar formato de username"""
        # Solo permitir letras, números, guiones y guiones bajos
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username solo puede contener letras, números, guiones y guiones bajos')
        return v.lower()  # Normalizar a minúsculas

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {
                    "username": "john_doe",
                    "email": "john@bjjacademy.com",
                    "password": "SecurePass123",
                    "role": "staff",
                    "academy_id": 1
                }
            ]
        }
    }
