"""
Pydantic Schemas para validación de input
Creado: 25/11/2025
"""

from .auth_schemas import (
    LoginRequest,
    ChangePasswordRequest,
    CreateUserRequest,
    RefreshTokenRequest
)

from .lead_schemas import (
    UpdateLeadStatusRequest,
    AddLeadNoteRequest,
    CreateLeadRequest,
    LeadFilterRequest
)

from .message_schemas import (
    IncomingMessageRequest,
    WhatsAppWebhookRequest
)

from .cache_schemas import (
    CacheInvalidateRequest,
    CacheInvalidatePatternRequest,
    CacheInvalidateKeysRequest
)

__all__ = [
    # Auth
    'LoginRequest',
    'ChangePasswordRequest',
    'CreateUserRequest',
    'RefreshTokenRequest',

    # Lead
    'UpdateLeadStatusRequest',
    'AddLeadNoteRequest',
    'CreateLeadRequest',
    'LeadFilterRequest',

    # Message
    'IncomingMessageRequest',
    'WhatsAppWebhookRequest',

    # Cache
    'CacheInvalidateRequest',
    'CacheInvalidatePatternRequest',
    'CacheInvalidateKeysRequest'
]
