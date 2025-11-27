"""
Validation Utilities para Pydantic
Helpers y decorators para validación de request
Creado: 25/11/2025
"""

from functools import wraps
from flask import request, jsonify
from pydantic import BaseModel, ValidationError
from typing import Type, Union


def validate_json(schema: Type[BaseModel]):
    """
    Decorator para validar request.json con Pydantic schema

    Args:
        schema: Pydantic schema class para validar

    Usage:
        @app.route('/login', methods=['POST'])
        @validate_json(LoginRequest)
        def login(validated_data: LoginRequest):
            username = validated_data.username
            password = validated_data.password
            # Los datos ya están validados y sanitizados
            ...

    Returns:
        - 400 si la validación falla
        - Ejecuta función decorada si validación pasa
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Verificar que sea JSON
                if not request.is_json:
                    return jsonify({
                        'error': 'Content-Type debe ser application/json'
                    }), 400

                # Obtener datos
                data = request.get_json()

                if data is None:
                    return jsonify({
                        'error': 'Request body inválido o vacío'
                    }), 400

                # Validar con Pydantic
                validated = schema(**data)

                # Pasar datos validados a la función
                return f(validated, *args, **kwargs)

            except ValidationError as e:
                # Formatear errores de Pydantic de forma user-friendly
                errors = []
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc']) if error['loc'] else 'unknown'
                    message = error['msg']
                    errors.append(f"{field}: {message}")

                return jsonify({
                    'error': 'Validación fallida',
                    'details': errors
                }), 400

            except Exception as e:
                # Error inesperado
                return jsonify({
                    'error': 'Error procesando request',
                    'message': str(e)
                }), 400

        return decorated_function
    return decorator


def validate_args(schema: Type[BaseModel]):
    """
    Decorator para validar request.args (query params) con Pydantic schema

    Args:
        schema: Pydantic schema class para validar

    Usage:
        @app.route('/leads', methods=['GET'])
        @validate_args(LeadFilterRequest)
        def get_leads(validated_params: LeadFilterRequest):
            status = validated_params.status
            limit = validated_params.limit
            # Query params validados
            ...

    Returns:
        - 400 si la validación falla
        - Ejecuta función decorada si validación pasa
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Obtener query params
                data = request.args.to_dict()

                # Convertir tipos (query params siempre son strings)
                # Pydantic hará la conversión automática

                # Validar con Pydantic
                validated = schema(**data)

                # Pasar datos validados a la función
                return f(validated, *args, **kwargs)

            except ValidationError as e:
                # Formatear errores
                errors = []
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc']) if error['loc'] else 'unknown'
                    message = error['msg']
                    errors.append(f"{field}: {message}")

                return jsonify({
                    'error': 'Parámetros inválidos',
                    'details': errors
                }), 400

            except Exception as e:
                return jsonify({
                    'error': 'Error procesando parámetros',
                    'message': str(e)
                }), 400

        return decorated_function
    return decorator


def validate_form(schema: Type[BaseModel]):
    """
    Decorator para validar request.form con Pydantic schema

    Args:
        schema: Pydantic schema class para validar

    Usage:
        @app.route('/webhook', methods=['POST'])
        @validate_form(WhatsAppWebhookRequest)
        def webhook(validated_data: WhatsAppWebhookRequest):
            body = validated_data.Body
            from_number = validated_data.From
            # Form data validado
            ...

    Returns:
        - 400 si la validación falla
        - Ejecuta función decorada si validación pasa
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Obtener form data
                data = request.form.to_dict()

                # También incluir request.values para Twilio
                # (Twilio envía datos en form o query dependiendo del método)
                if not data:
                    data = request.values.to_dict()

                if not data:
                    return jsonify({
                        'error': 'Form data vacío'
                    }), 400

                # Validar con Pydantic
                validated = schema(**data)

                # Pasar datos validados a la función
                return f(validated, *args, **kwargs)

            except ValidationError as e:
                # Formatear errores
                errors = []
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc']) if error['loc'] else 'unknown'
                    message = error['msg']
                    errors.append(f"{field}: {message}")

                return jsonify({
                    'error': 'Form data inválido',
                    'details': errors
                }), 400

            except Exception as e:
                return jsonify({
                    'error': 'Error procesando form data',
                    'message': str(e)
                }), 400

        return decorated_function
    return decorator


def validate_request(
    schema: Type[BaseModel],
    source: str = 'json'
):
    """
    Decorator genérico para validar request con Pydantic schema

    Args:
        schema: Pydantic schema class
        source: 'json', 'form', 'args', o 'values'

    Usage:
        @app.route('/endpoint', methods=['POST'])
        @validate_request(MySchema, source='json')
        def my_endpoint(validated_data: MySchema):
            ...
    """
    if source == 'json':
        return validate_json(schema)
    elif source == 'form':
        return validate_form(schema)
    elif source == 'args':
        return validate_args(schema)
    elif source == 'values':
        # Para Twilio que usa request.values
        return validate_form(schema)
    else:
        raise ValueError(f"Source no soportado: {source}. Use 'json', 'form', 'args', o 'values'")
