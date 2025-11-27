"""
User Model para autenticación JWT
Creado: 24/11/2025
"""

from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """
    Modelo de Usuario para acceso al dashboard

    Roles:
    - admin: Acceso completo (crear usuarios, modificar todo)
    - staff: Acceso limitado (ver y editar leads, no borrar)
    - readonly: Solo lectura
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # admin, staff, readonly
    academy_id = db.Column(db.Integer, db.ForeignKey('academies.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relación con Academy
    academy = db.relationship('Academy', backref='users', lazy=True)

    def set_password(self, password: str):
        """
        Hashear y guardar password

        Args:
            password: Password en texto plano
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Verificar password

        Args:
            password: Password en texto plano

        Returns:
            True si el password es correcto
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """
        Serializar usuario a dict (sin password)

        Returns:
            Dict con datos del usuario
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'academy_id': self.academy_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
