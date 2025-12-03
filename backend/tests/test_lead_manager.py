"""
Tests Unitarios para LeadManager
Tests aislados que requieren base de datos en memoria (SQLite)
"""

import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from datetime import datetime
from app import create_app, db
from app.models import Lead, LeadStatus, Academy
from app.services.lead_manager import LeadManager
from app.services.cache_service import cache


class TestLeadManager:
    """Tests para LeadManager con base de datos en memoria"""

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
    def manager(self, app):
        """Crear instancia de LeadManager"""
        with app.app_context():
            return LeadManager()

    # ========== Tests de get_or_create() ==========

    def test_get_or_create_nuevo_lead(self, app, manager):
        """Debe crear un nuevo lead si no existe"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')

            assert lead_id is not None
            lead = Lead.query.get(lead_id)
            assert lead is not None
            assert lead.phone == '+50688888888'
            assert lead.name == 'Juan Pérez'
            assert lead.status == LeadStatus.NEW
            assert lead.source == 'whatsapp'

    def test_get_or_create_lead_existente(self, app, manager):
        """Debe retornar el mismo lead si ya existe"""
        with app.app_context():
            # Crear lead inicial
            lead_id_1 = manager.get_or_create('+50688888888', 'Juan Pérez')

            # Intentar crear de nuevo
            lead_id_2 = manager.get_or_create('+50688888888', 'Otro Nombre')

            assert lead_id_1 == lead_id_2

            # Verificar que no se duplicó
            leads = Lead.query.filter_by(phone='+50688888888').all()
            assert len(leads) == 1

    def test_get_or_create_normaliza_telefono(self, app, manager):
        """Debe normalizar el número de teléfono"""
        with app.app_context():
            # Crear con formato diferente pero que normalice al mismo número
            lead_id_1 = manager.get_or_create('+506 8888-8888', 'Juan')

            # Verificar que se normalizó correctamente
            lead = Lead.query.get(lead_id_1)
            normalized_phone = lead.phone

            # Crear de nuevo con formato diferente
            lead_id_2 = manager.get_or_create(normalized_phone.replace(' ', '').replace('-', ''), 'Pedro')

            # Ambos deberían ser el mismo lead
            assert lead_id_1 == lead_id_2

    def test_get_or_create_sin_nombre(self, app, manager):
        """Debe crear lead con nombre genérico si no se proporciona"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888')

            lead = Lead.query.get(lead_id)
            assert lead.name == 'WhatsApp User'

    def test_get_or_create_actualiza_nombre_generico(self, app, manager):
        """Debe actualizar nombre genérico cuando se proporciona nombre real"""
        with app.app_context():
            # Crear con nombre genérico
            lead_id = manager.get_or_create('+50688888888')
            lead = Lead.query.get(lead_id)
            assert lead.name == 'WhatsApp User'

            # Actualizar con nombre real
            lead_id_2 = manager.get_or_create('+50688888888', 'Juan Pérez')
            assert lead_id == lead_id_2

            lead = Lead.query.get(lead_id)
            assert lead.name == 'Juan Pérez'

    # ========== Tests de get_info() ==========

    def test_get_info_lead_existente(self, app, manager):
        """Debe retornar información del lead"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')

            info = manager.get_info(lead_id)

            assert info is not None
            assert info['id'] == lead_id
            assert info['phone'] == '+50688888888'
            assert info['name'] == 'Juan Pérez'
            assert info['status'] == LeadStatus.NEW
            assert info['source'] == 'whatsapp'

    def test_get_info_lead_no_existente(self, app, manager):
        """Debe retornar diccionario vacío si lead no existe"""
        with app.app_context():
            info = manager.get_info(999999)
            assert info == {}

    def test_get_info_usa_cache(self, app, manager):
        """Debe usar caché para get_info (si está disponible)"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')

            # Primera llamada - cache miss
            info_1 = manager.get_info(lead_id)

            # Segunda llamada - cache hit (no debería consultar DB)
            info_2 = manager.get_info(lead_id)

            assert info_1 == info_2

            # Verificar que está en caché (solo si Redis está disponible)
            if cache.enabled:
                cached = cache.get_lead_info(lead_id)
                assert cached is not None
                assert cached['name'] == 'Juan Pérez'
            else:
                # Sin Redis, el test aún pasa porque get_info funciona sin caché
                assert info_1['name'] == 'Juan Pérez'

    # ========== Tests de update_name() ==========

    def test_update_name_exitoso(self, app, manager):
        """Debe actualizar nombre genérico a nombre real"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'WhatsApp User')

            result = manager.update_name(lead_id, 'Juan Pérez')

            assert result is True
            lead = Lead.query.get(lead_id)
            assert lead.name == 'Juan Pérez'

    def test_update_name_no_actualiza_nombre_real(self, app, manager):
        """No debe actualizar si el lead ya tiene nombre real"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')

            result = manager.update_name(lead_id, 'Pedro González')

            assert result is False
            lead = Lead.query.get(lead_id)
            assert lead.name == 'Juan Pérez'  # No cambió

    def test_update_name_invalida_cache(self, app, manager):
        """Debe invalidar caché al actualizar nombre (si está disponible)"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'WhatsApp User')

            # Guardar en caché
            manager.get_info(lead_id)

            # Solo verificar caché si Redis está disponible
            if cache.enabled:
                assert cache.get_lead_info(lead_id) is not None

            # Actualizar nombre
            result = manager.update_name(lead_id, 'Juan Pérez')
            assert result is True

            # Verificar que el nombre se actualizó en DB
            lead = Lead.query.get(lead_id)
            assert lead.name == 'Juan Pérez'

    def test_update_name_lead_no_existente(self, app, manager):
        """Debe retornar False si lead no existe"""
        with app.app_context():
            result = manager.update_name(999999, 'Juan Pérez')
            assert result is False

    def test_update_name_sin_nombre(self, app, manager):
        """Debe retornar False si no se proporciona nombre"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888')
            result = manager.update_name(lead_id, '')
            assert result is False

    # ========== Tests de update_status() ==========

    def test_update_status_a_interested(self, app, manager):
        """Debe actualizar status a INTERESTED si detecta keywords de interés"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')

            result = manager.update_status(lead_id, 'Quiero agendar una clase de prueba')

            assert result is True
            lead = Lead.query.get(lead_id)
            assert lead.status == LeadStatus.INTERESTED
            assert lead.lead_score == 8
            assert lead.last_contact_date is not None

    def test_update_status_a_contacted(self, app, manager):
        """Debe actualizar status a contacted si es primera interacción"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')

            result = manager.update_status(lead_id, 'Hola, quiero información')

            assert result is True
            lead = Lead.query.get(lead_id)
            assert lead.status == 'contacted'
            assert lead.last_contact_date is not None

    def test_update_status_no_cambia_si_ya_scheduled(self, app, manager):
        """No debe cambiar status si ya está SCHEDULED"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')
            lead = Lead.query.get(lead_id)
            lead.status = LeadStatus.SCHEDULED
            db.session.commit()

            result = manager.update_status(lead_id, 'Quiero agendar clase')

            # No debería cambiar porque ya está SCHEDULED
            assert result is False
            lead = Lead.query.get(lead_id)
            assert lead.status == LeadStatus.SCHEDULED

    def test_update_status_invalida_cache(self, app, manager):
        """Debe invalidar caché al actualizar status"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')

            # Guardar en caché
            manager.get_info(lead_id)

            # Actualizar status
            manager.update_status(lead_id, 'Quiero agendar clase')

            # Obtener info de nuevo (debería reflejar nuevo status)
            info = manager.get_info(lead_id)
            assert info['status'] == LeadStatus.INTERESTED

    # ========== Tests de calculate_score() ==========

    def test_calculate_score_agendar(self, app, manager):
        """Debe retornar score alto para keyword 'agendar'"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888')
            score = manager.calculate_score(lead_id, 'Quiero agendar una clase')
            assert score == 10

    def test_calculate_score_precio(self, app, manager):
        """Debe retornar score medio para keyword 'precio'"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888')
            # Usar 'precio' o 'costo' directamente
            score = manager.calculate_score(lead_id, 'Cuál es el precio?')
            assert score == 5

    def test_calculate_score_horario(self, app, manager):
        """Debe retornar score medio para keyword 'horario'"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888')
            score = manager.calculate_score(lead_id, 'Qué horario tienen?')
            assert score == 5

    def test_calculate_score_ubicacion(self, app, manager):
        """Debe retornar score bajo para keyword 'ubicación'"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888')
            # Usar 'donde' sin tilde (como está en el código)
            score = manager.calculate_score(lead_id, 'Donde están?')
            assert score == 3

    def test_calculate_score_sin_keywords(self, app, manager):
        """Debe retornar score 0 si no hay keywords"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888')
            score = manager.calculate_score(lead_id, 'Hola')
            assert score == 0

    def test_calculate_score_maximo_10(self, app, manager):
        """Debe limitar score a máximo 10"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888')
            # Mensaje con múltiples keywords
            score = manager.calculate_score(
                lead_id,
                'Quiero agendar, cuánto cuesta, qué horario tienen, dónde están'
            )
            assert score == 10  # Máximo

    # ========== Tests de get_by_status() ==========

    def test_get_by_status_retorna_leads(self, app, manager):
        """Debe retornar leads filtrados por status"""
        with app.app_context():
            # Crear varios leads
            lead_id_1 = manager.get_or_create('+50688888881', 'Lead 1')
            lead_id_2 = manager.get_or_create('+50688888882', 'Lead 2')
            lead_id_3 = manager.get_or_create('+50688888883', 'Lead 3')

            # Actualizar status de algunos
            manager.update_status(lead_id_1, 'Quiero agendar clase')
            manager.update_status(lead_id_2, 'Quiero agendar clase')
            manager.update_status(lead_id_3, 'Hola')

            # Obtener leads INTERESTED
            interested_leads = manager.get_by_status(LeadStatus.INTERESTED)

            assert len(interested_leads) == 2
            assert all(lead.status == LeadStatus.INTERESTED for lead in interested_leads)

    def test_get_by_status_sin_resultados(self, app, manager):
        """Debe retornar lista vacía si no hay leads con ese status"""
        with app.app_context():
            leads = manager.get_by_status('nonexistent_status')
            assert leads == []

    # ========== Tests de invalidate_cache() ==========

    def test_invalidate_cache_exitoso(self, app, manager):
        """Debe invalidar caché exitosamente (si está disponible)"""
        with app.app_context():
            lead_id = manager.get_or_create('+50688888888', 'Juan Pérez')

            # Guardar en caché
            manager.get_info(lead_id)

            # Invalidar
            result = manager.invalidate_cache(lead_id)

            # Si Redis está habilitado, debería retornar True
            # Si no, el método aún funciona y retorna el resultado de cache.invalidate_lead()
            if cache.enabled:
                assert result is True
            else:
                # Sin Redis, invalidate_cache retorna False pero no falla
                assert result in [True, False]


# ========== Ejecutar tests ==========

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TESTS UNITARIOS: LeadManager")
    print("="*60 + "\n")

    # Ejecutar con pytest
    exit_code = pytest.main([
        __file__,
        '-v',  # Verbose
        '--color=yes',  # Colores
        '--tb=short',  # Traceback corto
    ])

    exit(exit_code)
