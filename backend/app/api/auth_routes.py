"""
Authentication Routes para JWT
Creado: 24/11/2025
Rate Limited: 25/11/2025
Refactored with Repository Pattern: 25/11/2025
Pydantic Validation: 25/11/2025
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from datetime import datetime
from app import limiter
from app.repositories.user_repository import UserRepository
from app.schemas import LoginRequest, ChangePasswordRequest
from app.utils.validation import validate_json

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize repository
user_repo = UserRepository()


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Máximo 5 intentos de login por minuto
@validate_json(LoginRequest)  # ✅ Validación automática con Pydantic
def login(validated_data: LoginRequest):
    """
    Login con username/password
    Rate Limit: 5 intentos por minuto para prevenir brute force

    Request Body (validado con Pydantic):
        {
            "username": "admin",  # 3-80 chars, trimmed
            "password": "password"  # min 8 chars
        }

    Returns:
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "user": {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin"
            }
        }
    """
    # Los datos ya están validados por Pydantic
    username = validated_data.username  # Ya trimmed y validado
    password = validated_data.password  # Ya validado (min 8 chars)

    # Buscar usuario usando repository
    user = user_repo.find_by_username(username)

    if not user:
        return jsonify({'error': 'Credenciales inválidas'}), 401

    # Verificar password
    if not user.check_password(password):
        return jsonify({'error': 'Credenciales inválidas'}), 401

    # Verificar si está activo
    if not user.is_active:
        return jsonify({'error': 'Usuario inactivo'}), 403

    # Crear tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    # Actualizar último login usando repository
    user = user_repo.update_last_login(user)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@limiter.limit("10 per minute")  # Limitar refresh token requests
@jwt_required(refresh=True)
def refresh():
    """
    Renovar access token usando refresh token
    Rate Limit: 10 requests por minuto

    Headers:
        Authorization: Bearer <refresh_token>

    Returns:
        {
            "access_token": "eyJ..."
        }
    """
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)

    return jsonify({
        'access_token': access_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Obtener usuario actual autenticado

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            ...
        }
    """
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)

    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    if not user.is_active:
        return jsonify({'error': 'Usuario inactivo'}), 403

    return jsonify(user.to_dict()), 200


@auth_bp.route('/change-password', methods=['POST'])
@limiter.limit("3 per hour")  # Limitar cambios de password
@jwt_required()
@validate_json(ChangePasswordRequest)  # ✅ Validación automática con Pydantic
def change_password(validated_data: ChangePasswordRequest):
    """
    Cambiar password del usuario actual
    Rate Limit: 3 intentos por hora

    Headers:
        Authorization: Bearer <access_token>

    Request Body (validado con Pydantic):
        {
            "current_password": "old_password",  # min 8 chars
            "new_password": "new_password"  # min 8 chars, letra + número
        }

    Returns:
        {
            "message": "Password actualizado exitosamente"
        }
    """
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)

    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    # Los datos ya están validados por Pydantic
    current_password = validated_data.current_password
    new_password = validated_data.new_password  # Ya validado: min 8, letra + número

    # Verificar password actual
    if not user.check_password(current_password):
        return jsonify({'error': 'Password actual incorrecto'}), 401

    # Actualizar password usando repository
    user = user_repo.update_password(user, new_password)

    return jsonify({'message': 'Password actualizado exitosamente'}), 200
