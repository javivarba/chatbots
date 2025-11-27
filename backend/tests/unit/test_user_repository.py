"""
Unit Tests for UserRepository
Testing Repository Pattern implementation
Created: 25/11/2025
"""

import pytest
from datetime import datetime
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app import db


@pytest.fixture
def user_repo():
    """Fixture para UserRepository"""
    return UserRepository()


@pytest.fixture
def sample_user(app):
    """Fixture para crear un usuario de prueba"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            role='staff',
            is_active=True,
            academy_id=1
        )
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
        yield user

        # Cleanup
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()


class TestUserRepositoryBasicCRUD:
    """Tests para operaciones CRUD básicas"""

    def test_create_user(self, app, user_repo):
        """Test crear usuario usando repository"""
        with app.app_context():
            user = user_repo.create_user(
                username='newuser',
                email='newuser@example.com',
                password='password123',
                role='staff',
                academy_id=1
            )

            assert user.id is not None
            assert user.username == 'newuser'
            assert user.email == 'newuser@example.com'
            assert user.role == 'staff'
            assert user.is_active is True
            assert user.check_password('password123') is True

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    def test_get_by_id(self, app, user_repo, sample_user):
        """Test obtener usuario por ID"""
        with app.app_context():
            user = user_repo.get_by_id(sample_user.id)

            assert user is not None
            assert user.id == sample_user.id
            assert user.username == sample_user.username

    def test_get_by_id_not_found(self, app, user_repo):
        """Test obtener usuario que no existe"""
        with app.app_context():
            user = user_repo.get_by_id(99999)
            assert user is None

    def test_update_user(self, app, user_repo, sample_user):
        """Test actualizar usuario"""
        with app.app_context():
            updated = user_repo.update(
                sample_user,
                email='updated@example.com',
                role='admin'
            )

            assert updated.email == 'updated@example.com'
            assert updated.role == 'admin'

            # Verificar que se guardó en DB
            user_from_db = user_repo.get_by_id(sample_user.id)
            assert user_from_db.email == 'updated@example.com'

    def test_delete_user(self, app, user_repo):
        """Test eliminar usuario"""
        with app.app_context():
            # Crear usuario temporal
            user = user_repo.create_user(
                username='todelete',
                email='delete@example.com',
                password='password123',
                role='staff'
            )
            user_id = user.id

            # Eliminar
            success = user_repo.delete(user)
            assert success is True

            # Verificar que ya no existe
            deleted_user = user_repo.get_by_id(user_id)
            assert deleted_user is None


class TestUserRepositoryQueries:
    """Tests para queries especializados"""

    def test_find_by_username(self, app, user_repo, sample_user):
        """Test buscar usuario por username"""
        with app.app_context():
            user = user_repo.find_by_username(sample_user.username)

            assert user is not None
            assert user.username == sample_user.username
            assert user.id == sample_user.id

    def test_find_by_username_not_found(self, app, user_repo):
        """Test buscar username que no existe"""
        with app.app_context():
            user = user_repo.find_by_username('nonexistent')
            assert user is None

    def test_find_by_email(self, app, user_repo, sample_user):
        """Test buscar usuario por email"""
        with app.app_context():
            user = user_repo.find_by_email(sample_user.email)

            assert user is not None
            assert user.email == sample_user.email
            assert user.id == sample_user.id

    def test_find_by_email_not_found(self, app, user_repo):
        """Test buscar email que no existe"""
        with app.app_context():
            user = user_repo.find_by_email('nonexistent@example.com')
            assert user is None

    def test_find_active_users(self, app, user_repo, sample_user):
        """Test buscar usuarios activos"""
        with app.app_context():
            active_users = user_repo.find_active_users()

            assert len(active_users) > 0
            assert all(user.is_active for user in active_users)
            assert any(user.id == sample_user.id for user in active_users)

    def test_find_by_role(self, app, user_repo, sample_user):
        """Test buscar usuarios por rol"""
        with app.app_context():
            staff_users = user_repo.find_by_role('staff')

            assert len(staff_users) > 0
            assert all(user.role == 'staff' for user in staff_users)

    def test_find_by_academy(self, app, user_repo, sample_user):
        """Test buscar usuarios por academia"""
        with app.app_context():
            academy_users = user_repo.find_by_academy(sample_user.academy_id)

            assert len(academy_users) > 0
            assert all(user.academy_id == sample_user.academy_id for user in academy_users)

    def test_username_exists(self, app, user_repo, sample_user):
        """Test verificar si username existe"""
        with app.app_context():
            exists = user_repo.username_exists(sample_user.username)
            assert exists is True

            not_exists = user_repo.username_exists('nonexistent')
            assert not_exists is False

    def test_email_exists(self, app, user_repo, sample_user):
        """Test verificar si email existe"""
        with app.app_context():
            exists = user_repo.email_exists(sample_user.email)
            assert exists is True

            not_exists = user_repo.email_exists('nonexistent@example.com')
            assert not_exists is False


class TestUserRepositoryPasswordOperations:
    """Tests para operaciones de password"""

    def test_update_password(self, app, user_repo, sample_user):
        """Test actualizar password"""
        with app.app_context():
            new_password = 'newpassword456'

            updated = user_repo.update_password(sample_user, new_password)

            assert updated.check_password(new_password) is True
            assert updated.check_password('testpassword123') is False

    def test_password_hashed_on_create(self, app, user_repo):
        """Test que password se hashea al crear usuario"""
        with app.app_context():
            user = user_repo.create_user(
                username='hashtest',
                email='hash@example.com',
                password='plaintext123',
                role='staff'
            )

            # Password no debe guardarse en texto plano
            assert user.password_hash != 'plaintext123'
            # Pero check_password debe funcionar
            assert user.check_password('plaintext123') is True

            # Cleanup
            db.session.delete(user)
            db.session.commit()


class TestUserRepositoryBusinessLogic:
    """Tests para métodos de lógica de negocio"""

    def test_update_last_login(self, app, user_repo, sample_user):
        """Test actualizar timestamp de último login"""
        with app.app_context():
            original_login = sample_user.last_login

            updated = user_repo.update_last_login(sample_user)

            assert updated.last_login is not None
            # Si no tenía login previo, ahora debería tener
            if original_login is None:
                assert updated.last_login is not None
            else:
                assert updated.last_login >= original_login

    def test_deactivate_user(self, app, user_repo, sample_user):
        """Test desactivar usuario"""
        with app.app_context():
            deactivated = user_repo.deactivate_user(sample_user)

            assert deactivated.is_active is False

            # Verificar que se guardó
            user_from_db = user_repo.get_by_id(sample_user.id)
            assert user_from_db.is_active is False

    def test_activate_user(self, app, user_repo, sample_user):
        """Test activar usuario"""
        with app.app_context():
            # Primero desactivar
            user_repo.deactivate_user(sample_user)

            # Luego activar
            activated = user_repo.activate_user(sample_user)

            assert activated.is_active is True

            # Verificar que se guardó
            user_from_db = user_repo.get_by_id(sample_user.id)
            assert user_from_db.is_active is True


class TestUserRepositoryValidation:
    """Tests para validación de datos"""

    def test_create_user_with_duplicate_username(self, app, user_repo, sample_user):
        """Test crear usuario con username duplicado debe fallar"""
        with app.app_context():
            with pytest.raises(Exception):
                user_repo.create_user(
                    username=sample_user.username,  # Username duplicado
                    email='different@example.com',
                    password='password123',
                    role='staff'
                )

    def test_create_user_with_duplicate_email(self, app, user_repo, sample_user):
        """Test crear usuario con email duplicado debe fallar"""
        with app.app_context():
            with pytest.raises(Exception):
                user_repo.create_user(
                    username='differentuser',
                    email=sample_user.email,  # Email duplicado
                    password='password123',
                    role='staff'
                )


class TestUserRepositoryCount:
    """Tests para operaciones de conteo"""

    def test_count_all(self, app, user_repo, sample_user):
        """Test contar todos los usuarios"""
        with app.app_context():
            count = user_repo.count()
            assert count > 0

    def test_count_with_filter(self, app, user_repo, sample_user):
        """Test contar con filtro"""
        with app.app_context():
            staff_count = user_repo.count(role='staff')
            assert staff_count > 0

    def test_exists(self, app, user_repo, sample_user):
        """Test verificar existencia con filtros"""
        with app.app_context():
            exists = user_repo.exists(username=sample_user.username)
            assert exists is True

            not_exists = user_repo.exists(username='nonexistent')
            assert not_exists is False
