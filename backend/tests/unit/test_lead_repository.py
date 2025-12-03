"""
Unit Tests for LeadRepository
Testing Repository Pattern implementation
Created: 25/11/2025
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.repositories.lead_repository import LeadRepository
from app.models import Lead, LeadStatus, Academy


class TestLeadRepositoryBasicCRUD:
    """Tests para operaciones CRUD básicas"""

    @pytest.fixture
    def app(self):
        """Crear aplicación Flask de prueba"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with app.app_context():
            db.create_all()

            # Crear academy de prueba
            academy = Academy(
                name='BJJ Mingo Test',
                slug='bjj-mingo-test',
                email='test@bjjmingo.com',
                phone='+506-8888-8888',
                address_street='Test Street',
                address_city='Test City',
                instructor_name='Test Instructor',
                description='Test Academy'
            )
            db.session.add(academy)
            db.session.commit()

            yield app

            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def lead_repo(self):
        """Fixture para LeadRepository"""
        return LeadRepository()

    @pytest.fixture
    def sample_lead(self, app):
        """Fixture para crear un lead de prueba"""
        with app.app_context():
            lead = Lead(
                phone='+50612345678',
                name='Test User',
                source='whatsapp',
                status=LeadStatus.NEW,
                lead_score=0,
                academy_id=1
            )
            db.session.add(lead)
            db.session.commit()
            yield lead

            # Cleanup
            try:
                db.session.delete(lead)
                db.session.commit()
            except:
                db.session.rollback()

    def test_create_lead(self, app, lead_repo):
        """Test crear lead usando repository"""
        with app.app_context():
            lead = lead_repo.create_lead(
                phone='+50699887766',
                name='New Test Lead',
                source='whatsapp',
                academy_id=1
            )

            assert lead.id is not None
            assert lead.phone == '+50699887766'
            assert lead.name == 'New Test Lead'
            assert lead.status == LeadStatus.NEW
            assert lead.lead_score == 0

            # Cleanup
            db.session.delete(lead)
            db.session.commit()

    def test_get_by_id(self, app, lead_repo, sample_lead):
        """Test obtener lead por ID"""
        with app.app_context():
            lead = lead_repo.get_by_id(sample_lead.id)

            assert lead is not None
            assert lead.id == sample_lead.id
            assert lead.phone == sample_lead.phone

    def test_get_by_id_not_found(self, app, lead_repo):
        """Test obtener lead que no existe"""
        with app.app_context():
            lead = lead_repo.get_by_id(99999)
            assert lead is None

    def test_find_by_phone(self, app, lead_repo, sample_lead):
        """Test buscar lead por teléfono"""
        with app.app_context():
            lead = lead_repo.find_by_phone(sample_lead.phone)

            assert lead is not None
            assert lead.phone == sample_lead.phone
            assert lead.name == sample_lead.name

    def test_find_by_phone_not_found(self, app, lead_repo):
        """Test buscar teléfono que no existe"""
        with app.app_context():
            lead = lead_repo.find_by_phone('+50600000000')
            assert lead is None

    def test_update_lead(self, app, lead_repo, sample_lead):
        """Test actualizar lead"""
        with app.app_context():
            updated = lead_repo.update(
                sample_lead,
                name='Updated Name',
                lead_score=8
            )

            assert updated.name == 'Updated Name'
            assert updated.lead_score == 8

            # Verificar que se guardó en DB
            lead_from_db = lead_repo.get_by_id(sample_lead.id)
            assert lead_from_db.name == 'Updated Name'
            assert lead_from_db.lead_score == 8

    def test_delete_lead(self, app, lead_repo):
        """Test eliminar lead"""
        with app.app_context():
            # Crear lead temporal
            lead = lead_repo.create_lead(
                phone='+50611111111',
                name='To Delete',
                source='whatsapp',
                academy_id=1
            )
            lead_id = lead.id

            # Eliminar
            success = lead_repo.delete(lead)
            assert success is True

            # Verificar que ya no existe
            deleted_lead = lead_repo.get_by_id(lead_id)
            assert deleted_lead is None


class TestLeadRepositoryQueries:
    """Tests para queries especializados"""

    def test_find_by_status(self, app, lead_repo, sample_lead):
        """Test buscar leads por status"""
        with app.app_context():
            leads = lead_repo.find_by_status(LeadStatus.NEW)

            assert len(leads) > 0
            assert all(lead.status == LeadStatus.NEW for lead in leads)

    def test_find_by_academy(self, app, lead_repo, sample_lead):
        """Test buscar leads por academia"""
        with app.app_context():
            leads = lead_repo.find_by_academy(sample_lead.academy_id)

            assert len(leads) > 0
            assert all(lead.academy_id == sample_lead.academy_id for lead in leads)

    def test_phone_exists(self, app, lead_repo, sample_lead):
        """Test verificar si teléfono existe"""
        with app.app_context():
            exists = lead_repo.phone_exists(sample_lead.phone)
            assert exists is True

            not_exists = lead_repo.phone_exists('+50600000000')
            assert not_exists is False

    def test_count_by_status(self, app, lead_repo):
        """Test contar leads por status"""
        with app.app_context():
            counts = lead_repo.count_by_status()

            assert isinstance(counts, dict)
            # Debería tener al menos un lead NEW del fixture
            assert LeadStatus.NEW in counts

    def test_get_recent_leads(self, app, lead_repo, sample_lead):
        """Test obtener leads recientes"""
        with app.app_context():
            leads = lead_repo.get_recent_leads(limit=5)

            assert len(leads) <= 5
            # Verificar orden descendente por created_at
            if len(leads) > 1:
                for i in range(len(leads) - 1):
                    assert leads[i].created_at >= leads[i + 1].created_at


class TestLeadRepositoryBusinessLogic:
    """Tests para métodos de lógica de negocio"""

    def test_update_status(self, app, lead_repo, sample_lead):
        """Test actualizar status del lead"""
        with app.app_context():
            updated = lead_repo.update_status(
                sample_lead,
                LeadStatus.INTERESTED
            )

            assert updated.status == LeadStatus.INTERESTED
            assert updated.updated_at is not None

    def test_update_lead_score(self, app, lead_repo, sample_lead):
        """Test actualizar lead score"""
        with app.app_context():
            updated = lead_repo.update_lead_score(sample_lead, 7)

            assert updated.lead_score == 7

    def test_update_lead_score_validation(self, app, lead_repo, sample_lead):
        """Test validación de lead score (debe ser 0-10)"""
        with app.app_context():
            with pytest.raises(ValueError):
                lead_repo.update_lead_score(sample_lead, 11)

            with pytest.raises(ValueError):
                lead_repo.update_lead_score(sample_lead, -1)

    def test_schedule_trial_class(self, app, lead_repo, sample_lead):
        """Test agendar clase de prueba"""
        with app.app_context():
            trial_date = datetime.now() + timedelta(days=2)

            updated = lead_repo.schedule_trial_class(
                sample_lead,
                trial_date
            )

            assert updated.trial_class_date is not None
            assert updated.status == LeadStatus.SCHEDULED
            assert updated.trial_class_date == trial_date

    def test_update_last_contact(self, app, lead_repo, sample_lead):
        """Test actualizar último contacto"""
        with app.app_context():
            original_contact = sample_lead.last_contact_date

            updated = lead_repo.update_last_contact(sample_lead)

            assert updated.last_contact_date is not None
            # Si no tenía contacto previo, ahora debería tener
            if original_contact is None:
                assert updated.last_contact_date is not None

    def test_find_hot_leads(self, app, lead_repo):
        """Test buscar hot leads (score >= 7)"""
        with app.app_context():
            # Crear lead con score alto
            hot_lead = lead_repo.create_lead(
                phone='+50622222222',
                name='Hot Lead',
                source='whatsapp',
                academy_id=1
            )
            lead_repo.update_lead_score(hot_lead, 9)

            hot_leads = lead_repo.find_hot_leads(min_score=7)

            assert len(hot_leads) > 0
            assert all(lead.lead_score >= 7 for lead in hot_leads)

            # Cleanup
            db.session.delete(hot_lead)
            db.session.commit()

    def test_find_needs_followup(self, app, lead_repo):
        """Test buscar leads que necesitan seguimiento"""
        with app.app_context():
            # Crear lead con contacto antiguo
            old_lead = lead_repo.create_lead(
                phone='+50633333333',
                name='Old Contact',
                source='whatsapp',
                academy_id=1
            )

            # Simular contacto hace 5 días
            old_date = datetime.now() - timedelta(days=5)
            lead_repo.update(old_lead, last_contact_date=old_date)

            needs_followup = lead_repo.find_needs_followup(days=3)

            # Debería incluir el lead que creamos
            assert any(lead.id == old_lead.id for lead in needs_followup)

            # Cleanup
            db.session.delete(old_lead)
            db.session.commit()

    def test_find_scheduled_leads(self, app, lead_repo):
        """Test buscar leads con clases agendadas"""
        with app.app_context():
            # Crear lead con clase agendada
            scheduled_lead = lead_repo.create_lead(
                phone='+50644444444',
                name='Scheduled Lead',
                source='whatsapp',
                academy_id=1
            )
            trial_date = datetime.now() + timedelta(days=1)
            lead_repo.schedule_trial_class(scheduled_lead, trial_date)

            scheduled_leads = lead_repo.find_scheduled_leads()

            assert len(scheduled_leads) > 0
            assert all(lead.trial_class_date is not None for lead in scheduled_leads)
            assert any(lead.id == scheduled_lead.id for lead in scheduled_leads)

            # Cleanup
            db.session.delete(scheduled_lead)
            db.session.commit()


class TestLeadRepositoryCount:
    """Tests para operaciones de conteo"""

    def test_count_all(self, app, lead_repo, sample_lead):
        """Test contar todos los leads"""
        with app.app_context():
            count = lead_repo.count()
            assert count > 0

    def test_count_with_filter(self, app, lead_repo, sample_lead):
        """Test contar con filtro"""
        with app.app_context():
            new_count = lead_repo.count(status=LeadStatus.NEW)
            assert new_count > 0

    def test_exists(self, app, lead_repo, sample_lead):
        """Test verificar existencia con filtros"""
        with app.app_context():
            exists = lead_repo.exists(phone=sample_lead.phone)
            assert exists is True

            not_exists = lead_repo.exists(phone='+50600000000')
            assert not_exists is False
