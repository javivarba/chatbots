"""
Unit tests for Dashboard API routes - MIGRATED TO SQLALCHEMY
"""

import pytest
import json
from datetime import datetime
from app import create_app, db
from app.models import Lead, Conversation, Message, MessageDirection, LeadStatus


@pytest.fixture
def app(test_db):
    """Create Flask app for testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestStatsEndpoint:
    """Test /api/stats endpoint."""

    def test_get_stats_empty_db(self, client, test_db):
        """Test getting stats with empty database."""
        response = client.get('/api/stats')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'total_leads' in data
        assert 'scheduled' in data
        assert 'needs_followup' in data
        assert 'conversion_rate' in data

    def test_get_stats_with_data(self, client, test_db, sample_lead):
        """Test getting stats with data."""
        response = client.get('/api/stats')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['total_leads'] >= 1
        assert data['new'] >= 1


class TestLeadsEndpoint:
    """Test /api/leads endpoint."""

    def test_get_leads_empty(self, client, test_db):
        """Test getting leads from empty database."""
        response = client.get('/api/leads')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_get_leads_with_data(self, client, test_db, sample_lead):
        """Test getting leads with data."""
        response = client.get('/api/leads')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data) >= 1

        # Verify lead structure
        lead = data[0]
        assert 'id' in lead
        assert 'phone' in lead
        assert 'name' in lead
        assert 'status' in lead
        assert 'next_action' in lead

    def test_get_leads_with_status_filter(self, client, test_db):
        """Test filtering leads by status."""
        # Add leads with different statuses using SQLAlchemy
        from app.models import Academy
        academy = Academy.query.first()

        lead1 = Lead(
            academy_id=academy.id,
            phone='+50611111111',
            name='User 1',
            status=LeadStatus.NEW,
            source='whatsapp',
            lead_score=5,
            created_at=datetime.now()
        )
        lead2 = Lead(
            academy_id=academy.id,
            phone='+50622222222',
            name='User 2',
            status=LeadStatus.CONTACTED,
            source='whatsapp',
            lead_score=6,
            created_at=datetime.now()
        )
        db.session.add(lead1)
        db.session.add(lead2)
        db.session.commit()

        response = client.get('/api/leads?status=new')
        assert response.status_code == 200

        data = json.loads(response.data)
        # All leads should have 'new' status
        for lead in data:
            assert lead['status'] == LeadStatus.NEW


class TestLeadDetailEndpoint:
    """Test /api/leads/<id> endpoint."""

    def test_get_lead_detail(self, client, test_db, sample_lead):
        """Test getting lead detail."""
        response = client.get(f'/api/leads/{sample_lead}')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'lead' in data
        assert 'messages' in data
        assert 'appointments' in data

        # Verify lead data
        lead = data['lead']
        assert lead['id'] == sample_lead
        assert lead['phone'] == '+50612345678'

    def test_get_lead_detail_not_found(self, client, test_db):
        """Test getting non-existent lead."""
        response = client.get('/api/leads/9999')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert 'error' in data


class TestUpdateLeadStatusEndpoint:
    """Test /api/leads/<id>/update-status endpoint."""

    def test_update_status_success(self, client, test_db, sample_lead):
        """Test successfully updating lead status."""
        response = client.post(
            f'/api/leads/{sample_lead}/update-status',
            json={'status': LeadStatus.INTERESTED},
            content_type='application/json'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['status'] == LeadStatus.INTERESTED

    def test_update_status_missing_status(self, client, test_db, sample_lead):
        """Test updating status without providing status."""
        response = client.post(
            f'/api/leads/{sample_lead}/update-status',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data


class TestAddLeadNoteEndpoint:
    """Test /api/leads/<id>/add-note endpoint."""

    def test_add_note_success(self, client, test_db, sample_lead, sample_conversation):
        """Test successfully adding a note."""
        response = client.post(
            f'/api/leads/{sample_lead}/add-note',
            json={'note': 'Test note content'},
            content_type='application/json'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True

    def test_add_note_missing_note(self, client, test_db, sample_lead):
        """Test adding note without note content."""
        response = client.post(
            f'/api/leads/{sample_lead}/add-note',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data


class TestAppointmentsEndpoint:
    """Test /api/appointments endpoint."""

    def test_get_appointments_empty(self, client, test_db):
        """Test getting appointments from empty database."""
        response = client.get('/api/appointments')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_get_appointments_with_data(self, client, test_db, sample_lead):
        """Test getting appointments with data."""
        # Set trial_class_date for the lead using SQLAlchemy
        lead = Lead.query.get(sample_lead)
        lead.trial_class_date = datetime.strptime('2025-11-20 18:00:00', '%Y-%m-%d %H:%M:%S')
        lead.status = LeadStatus.SCHEDULED
        db.session.commit()

        response = client.get('/api/appointments')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data) >= 1

        # Verify appointment structure
        appointment = data[0]
        assert 'id' in appointment
        assert 'datetime' in appointment
        assert 'status' in appointment
        assert 'lead_name' in appointment
        assert 'lead_phone' in appointment


class TestDetermineNextAction:
    """Test determine_next_action helper function."""

    def test_next_action_with_appointment(self, client, test_db):
        """Test next action when lead has appointment."""
        from app.api.dashboard_routes import determine_next_action

        action = determine_next_action(
            status=LeadStatus.NEW,
            interest_level=5,
            days_since_contact=None,
            last_sender='user',
            next_appointment='2025-11-20 18:00:00'
        )

        assert action['action'] == 'confirm_appointment'
        assert action['priority'] == 'high'

    def test_next_action_respond_to_user(self, client, test_db):
        """Test next action when user sent last message."""
        from app.api.dashboard_routes import determine_next_action

        action = determine_next_action(
            status=LeadStatus.NEW,
            interest_level=5,
            days_since_contact=1,
            last_sender='user',
            next_appointment=None
        )

        assert action['action'] == 'respond'
        assert action['priority'] == 'urgent'

    def test_next_action_followup_hot_lead(self, client, test_db):
        """Test next action for hot lead needing followup."""
        from app.api.dashboard_routes import determine_next_action

        action = determine_next_action(
            status=LeadStatus.INTERESTED,
            interest_level=8,
            days_since_contact=4,
            last_sender='assistant',
            next_appointment=None
        )

        assert action['action'] == 'followup_hot'
        assert action['priority'] == 'high'

    def test_next_action_schedule(self, client, test_db):
        """Test next action for interested lead without appointment."""
        from app.api.dashboard_routes import determine_next_action

        action = determine_next_action(
            status=LeadStatus.INTERESTED,
            interest_level=9,
            days_since_contact=1,
            last_sender='assistant',
            next_appointment=None
        )

        assert action['action'] == 'schedule'
        assert action['priority'] == 'high'
