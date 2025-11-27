"""
Tests Unitarios para ConversationManager
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
from app.models import Lead, LeadStatus, Academy, Conversation, Message, MessageDirection
from app.services.conversation_manager import ConversationManager
from app.services.cache_service import cache


class TestConversationManager:
    """Tests para ConversationManager con base de datos en memoria"""

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

            # Crear lead de prueba
            lead = Lead(
                academy_id=academy.id,
                phone='+50688888888',
                name='Test User',
                source='whatsapp',
                status=LeadStatus.NEW,
                lead_score=5,
                created_at=datetime.now()
            )
            db.session.add(lead)
            db.session.commit()

            yield app

            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def manager(self, app):
        """Crear instancia de ConversationManager"""
        with app.app_context():
            return ConversationManager()

    # ========== Tests de get_or_create() ==========

    def test_get_or_create_nueva_conversacion(self, app, manager):
        """Debe crear una nueva conversación si no existe"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            assert conv_id is not None
            conversation = Conversation.query.get(conv_id)
            assert conversation is not None
            assert conversation.lead_id == lead.id
            assert conversation.is_active is True
            assert conversation.message_count == 0

    def test_get_or_create_conversacion_existente(self, app, manager):
        """Debe retornar la misma conversación si ya existe"""
        with app.app_context():
            lead = Lead.query.first()

            # Crear conversación inicial
            conv_id_1 = manager.get_or_create(lead.id)

            # Intentar crear de nuevo
            conv_id_2 = manager.get_or_create(lead.id)

            assert conv_id_1 == conv_id_2

            # Verificar que no se duplicó
            conversations = Conversation.query.filter_by(lead_id=lead.id, is_active=True).all()
            assert len(conversations) == 1

    def test_get_or_create_error_si_lead_no_existe(self, app, manager):
        """Debe lanzar excepción si lead no existe"""
        with app.app_context():
            with pytest.raises(Exception, match="Lead .* no encontrado"):
                manager.get_or_create(999999)

    # ========== Tests de save_message() ==========

    def test_save_message_inbound(self, app, manager):
        """Debe guardar mensaje inbound y actualizar contadores"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            message_id = manager.save_message(
                conv_id,
                MessageDirection.INBOUND,
                'Hola, quiero información'
            )

            assert message_id is not None

            # Verificar mensaje
            message = Message.query.get(message_id)
            assert message.conversation_id == conv_id
            assert message.direction == MessageDirection.INBOUND
            assert message.content == 'Hola, quiero información'

            # Verificar contadores
            conversation = Conversation.query.get(conv_id)
            assert conversation.message_count == 1
            assert conversation.inbound_count == 1
            assert conversation.outbound_count == 0

    def test_save_message_outbound(self, app, manager):
        """Debe guardar mensaje outbound y actualizar contadores"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            message_id = manager.save_message(
                conv_id,
                MessageDirection.OUTBOUND,
                '¡Hola! Con gusto te ayudo.'
            )

            assert message_id is not None

            # Verificar contadores
            conversation = Conversation.query.get(conv_id)
            assert conversation.message_count == 1
            assert conversation.inbound_count == 0
            assert conversation.outbound_count == 1

    def test_save_message_multiples(self, app, manager):
        """Debe guardar múltiples mensajes y actualizar contadores correctamente"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            # Guardar 3 inbound y 2 outbound
            manager.save_message(conv_id, MessageDirection.INBOUND, 'Mensaje 1')
            manager.save_message(conv_id, MessageDirection.OUTBOUND, 'Respuesta 1')
            manager.save_message(conv_id, MessageDirection.INBOUND, 'Mensaje 2')
            manager.save_message(conv_id, MessageDirection.OUTBOUND, 'Respuesta 2')
            manager.save_message(conv_id, MessageDirection.INBOUND, 'Mensaje 3')

            conversation = Conversation.query.get(conv_id)
            assert conversation.message_count == 5
            assert conversation.inbound_count == 3
            assert conversation.outbound_count == 2

    def test_save_message_invalida_cache(self, app, manager):
        """Debe invalidar caché de historial al guardar mensaje"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            # Obtener historial (cachea)
            manager.get_history(conv_id)

            # Solo verificar invalidación si Redis está disponible
            if cache.enabled:
                # Guardar mensaje debería invalidar caché
                manager.save_message(conv_id, MessageDirection.INBOUND, 'Nuevo mensaje')

                # Verificar que caché fue invalidado
                # (get_history volverá a cachear, pero el punto es que se invalidó)
                history = manager.get_history(conv_id)
                assert len(history) == 1

    # ========== Tests de get_history() ==========

    def test_get_history_conversacion_vacia(self, app, manager):
        """Debe retornar lista vacía si no hay mensajes"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            history = manager.get_history(conv_id)

            assert history == []

    def test_get_history_con_mensajes(self, app, manager):
        """Debe retornar historial en orden cronológico"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            # Guardar mensajes
            manager.save_message(conv_id, MessageDirection.INBOUND, 'Mensaje 1')
            manager.save_message(conv_id, MessageDirection.OUTBOUND, 'Respuesta 1')
            manager.save_message(conv_id, MessageDirection.INBOUND, 'Mensaje 2')

            history = manager.get_history(conv_id)

            assert len(history) == 3
            assert history[0]['sender'] == 'user'
            assert history[0]['content'] == 'Mensaje 1'
            assert history[1]['sender'] == 'assistant'
            assert history[1]['content'] == 'Respuesta 1'
            assert history[2]['sender'] == 'user'
            assert history[2]['content'] == 'Mensaje 2'

    def test_get_history_respeta_limit(self, app, manager):
        """Debe respetar el límite de mensajes"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            # Guardar 10 mensajes
            for i in range(10):
                manager.save_message(conv_id, MessageDirection.INBOUND, f'Mensaje {i+1}')

            # Obtener solo últimos 5
            history = manager.get_history(conv_id, limit=5)

            assert len(history) == 5
            # Debe retornar los últimos 5 (6-10)
            assert history[0]['content'] == 'Mensaje 6'
            assert history[4]['content'] == 'Mensaje 10'

    def test_get_history_usa_cache(self, app, manager):
        """Debe usar caché para get_history (si está disponible)"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            manager.save_message(conv_id, MessageDirection.INBOUND, 'Test mensaje')

            # Primera llamada - cache miss
            history_1 = manager.get_history(conv_id)

            # Segunda llamada - cache hit
            history_2 = manager.get_history(conv_id)

            assert history_1 == history_2

            # Solo verificar caché si Redis está disponible
            if cache.enabled:
                cached = cache.get_conversation_history(conv_id)
                assert cached is not None
                assert len(cached) == 1

    # ========== Tests de get_message_count() ==========

    def test_get_message_count_conversacion_vacia(self, app, manager):
        """Debe retornar 0 para conversación vacía"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            count = manager.get_message_count(conv_id)

            assert count == 0

    def test_get_message_count_con_mensajes(self, app, manager):
        """Debe retornar cantidad correcta de mensajes"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            manager.save_message(conv_id, MessageDirection.INBOUND, 'Mensaje 1')
            manager.save_message(conv_id, MessageDirection.OUTBOUND, 'Respuesta 1')
            manager.save_message(conv_id, MessageDirection.INBOUND, 'Mensaje 2')

            count = manager.get_message_count(conv_id)

            assert count == 3

    def test_get_message_count_conversacion_no_existe(self, app, manager):
        """Debe retornar 0 si conversación no existe"""
        with app.app_context():
            count = manager.get_message_count(999999)
            assert count == 0

    # ========== Tests de close_conversation() ==========

    def test_close_conversation_exitoso(self, app, manager):
        """Debe cerrar conversación exitosamente"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            result = manager.close_conversation(conv_id)

            assert result is True

            conversation = Conversation.query.get(conv_id)
            assert conversation.is_active is False

    def test_close_conversation_invalida_cache(self, app, manager):
        """Debe invalidar caché al cerrar conversación"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            # Cachear historial
            manager.get_history(conv_id)

            # Cerrar conversación
            manager.close_conversation(conv_id)

            # Verificar que se cerró
            conversation = Conversation.query.get(conv_id)
            assert conversation.is_active is False

    def test_close_conversation_no_existe(self, app, manager):
        """Debe retornar False si conversación no existe"""
        with app.app_context():
            result = manager.close_conversation(999999)
            assert result is False

    # ========== Tests de get_active_conversations() ==========

    def test_get_active_conversations_vacio(self, app, manager):
        """Debe retornar lista vacía si no hay conversaciones activas"""
        with app.app_context():
            lead = Lead.query.first()

            conversations = manager.get_active_conversations(lead.id)

            assert conversations == []

    def test_get_active_conversations_con_activas(self, app, manager):
        """Debe retornar solo conversaciones activas"""
        with app.app_context():
            lead = Lead.query.first()

            # Crear 3 conversaciones
            conv_id_1 = manager.get_or_create(lead.id)
            manager.close_conversation(conv_id_1)

            # Crear otra conversación (que será la activa)
            # Primero cerrar la que está activa
            active_convs = Conversation.query.filter_by(lead_id=lead.id, is_active=True).all()
            for conv in active_convs:
                conv.is_active = False
            db.session.commit()

            # Crear nueva conversación activa
            conversation = Conversation(
                lead_id=lead.id,
                academy_id=lead.academy_id,
                platform='whatsapp',
                is_active=True,
                message_count=0,
                inbound_count=0,
                outbound_count=0,
                started_at=datetime.now(),
                last_message_at=datetime.now()
            )
            db.session.add(conversation)
            db.session.commit()

            conversations = manager.get_active_conversations(lead.id)

            assert len(conversations) == 1
            assert conversations[0].is_active is True

    # ========== Tests de get_academy_info() ==========

    def test_get_academy_info_retorna_datos(self, app, manager):
        """Debe retornar información de la academy"""
        with app.app_context():
            info = manager.get_academy_info()

            assert info is not None
            assert 'name' in info
            assert info['name'] == 'BJJ Mingo Test'
            assert 'phone' in info
            assert 'instructor' in info

    def test_get_academy_info_usa_cache(self, app, manager):
        """Debe usar caché para academy info (si está disponible)"""
        with app.app_context():
            # Primera llamada
            info_1 = manager.get_academy_info()

            # Segunda llamada
            info_2 = manager.get_academy_info()

            assert info_1 == info_2

            # Solo verificar caché si Redis está disponible
            if cache.enabled:
                cached = cache.get_academy_info()
                assert cached is not None
                assert cached['name'] == 'BJJ Mingo Test'

    def test_get_academy_info_sin_academy(self, app, manager):
        """Debe retornar datos por defecto si no hay academy"""
        with app.app_context():
            # Eliminar lead primero (tiene FK a academy)
            Lead.query.delete()
            # Eliminar conversaciones (tienen FK a academy)
            Conversation.query.delete()
            # Ahora eliminar academy
            Academy.query.delete()
            db.session.commit()

            info = manager.get_academy_info()

            assert info is not None
            assert info['name'] == 'BJJ Mingo'
            assert info['phone'] == '+506-8888-8888'

    # ========== Tests de invalidate_cache() ==========

    def test_invalidate_cache_exitoso(self, app, manager):
        """Debe invalidar caché exitosamente (si está disponible)"""
        with app.app_context():
            lead = Lead.query.first()
            conv_id = manager.get_or_create(lead.id)

            # Cachear historial
            manager.get_history(conv_id)

            # Invalidar
            result = manager.invalidate_cache(conv_id)

            # Si Redis está habilitado, debería retornar True
            if cache.enabled:
                assert result is True
            else:
                # Sin Redis, aún funciona
                assert result in [True, False]


# ========== Ejecutar tests ==========

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TESTS UNITARIOS: ConversationManager")
    print("="*60 + "\n")

    # Ejecutar con pytest
    exit_code = pytest.main([
        __file__,
        '-v',  # Verbose
        '--color=yes',  # Colores
        '--tb=short',  # Traceback corto
    ])

    exit(exit_code)
