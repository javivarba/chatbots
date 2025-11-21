"""
Integration tests for API endpoints - MIGRATED TO SQLALCHEMY

Tests the complete flow of API requests including database interactions.
NOTE: Simplified version - uses trial_class_date field instead of appointment/trial_weeks tables
"""

import pytest
import json
from datetime import datetime, timedelta

from app import create_app, db
from app.models import Lead, Conversation, Message, MessageDirection, LeadStatus, Academy


@pytest.fixture
def app(test_db):
    """Create Flask app for integration testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.mark.integration
class TestDashboardStatsIntegration:
    """Integration tests for dashboard stats endpoint."""

    def test_stats_with_real_data_flow(self, client, test_db):
        """
        Test stats endpoint with realistic data scenario.

        Scenario:
        - 2 new leads
        - 2 contacted leads
        - 1 interested lead with scheduled trial
        """
        academy = Academy.query.first()

        # Create leads with different statuses using SQLAlchemy
        leads_data = [
            ('+50611111111', 'User 1', LeadStatus.NEW, None),
            ('+50622222222', 'User 2', LeadStatus.NEW, None),
            ('+50633333333', 'User 3', LeadStatus.CONTACTED, None),
            ('+50644444444', 'User 4', LeadStatus.CONTACTED, None),
            ('+50655555555', 'User 5', LeadStatus.SCHEDULED, datetime.now() + timedelta(days=2)),
        ]

        for phone, name, status, trial_date in leads_data:
            lead = Lead(
                academy_id=academy.id,
                phone=phone,
                name=name,
                status=status,
                source='whatsapp',
                lead_score=5,
                trial_class_date=trial_date,
                created_at=datetime.now()
            )
            db.session.add(lead)

        db.session.commit()

        # Get stats
        response = client.get('/api/stats')
        assert response.status_code == 200

        data = json.loads(response.data)

        # Verify stats
        assert data['total_leads'] == 5
        assert data['new'] == 2
        assert data['contacted'] == 2
        assert data['scheduled'] == 1
        assert data['conversion_rate'] == 20.0  # 1/5 = 20%


@pytest.mark.integration
class TestLeadsEndpointIntegration:
    """Integration tests for leads endpoints."""

    def test_complete_lead_management_flow(self, client, test_db):
        """
        Test complete lead management flow.

        Flow:
        1. Create lead
        2. Get lead list
        3. Get lead detail
        4. Update lead status
        5. Add note to lead
        """
        academy = Academy.query.first()

        # Step 1: Create lead using SQLAlchemy
        lead = Lead(
            academy_id=academy.id,
            phone='+50699999999',
            name='Flow Test',
            status=LeadStatus.NEW,
            source='whatsapp',
            lead_score=5,
            created_at=datetime.now()
        )
        db.session.add(lead)
        db.session.commit()
        lead_id = lead.id

        # Create conversation
        conv = Conversation(
            lead_id=lead_id,
            is_active=True,
            created_at=datetime.now(),
            last_message_at=datetime.now()
        )
        db.session.add(conv)
        db.session.commit()

        # Step 2: Get lead list
        response = client.get('/api/leads')
        assert response.status_code == 200
        leads = json.loads(response.data)
        assert len(leads) >= 1
        assert any(l['phone'] == '+50699999999' for l in leads)

        # Step 3: Get lead detail
        response = client.get(f'/api/leads/{lead_id}')
        assert response.status_code == 200
        detail = json.loads(response.data)
        assert detail['lead']['id'] == lead_id
        assert detail['lead']['name'] == 'Flow Test'
        assert 'messages' in detail
        assert 'appointments' in detail

        # Step 4: Update lead status
        response = client.post(
            f'/api/leads/{lead_id}/update-status',
            json={'status': LeadStatus.INTERESTED},
            content_type='application/json'
        )
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True

        # Verify status was updated using SQLAlchemy
        lead = Lead.query.get(lead_id)
        assert lead.status == LeadStatus.INTERESTED

        # Step 5: Add note
        response = client.post(
            f'/api/leads/{lead_id}/add-note',
            json={'note': 'Integration test note'},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Verify note was added
        messages = Message.query.filter_by(
            conversation_id=conv.id,
            direction=MessageDirection.OUTBOUND
        ).all()
        assert len(messages) >= 1
        assert any('Integration test note' in m.content for m in messages)

    def test_leads_filtering(self, client, test_db):
        """Test leads filtering by status."""
        academy = Academy.query.first()

        # Create leads with different statuses
        statuses = [LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.INTERESTED, LeadStatus.NEW, LeadStatus.CONTACTED]
        for i, status in enumerate(statuses):
            lead = Lead(
                academy_id=academy.id,
                phone=f'+5061111111{i}',
                name=f'User {i}',
                status=status,
                source='whatsapp',
                lead_score=5,
                created_at=datetime.now()
            )
            db.session.add(lead)

        db.session.commit()

        # Filter by 'new' status
        response = client.get(f'/api/leads?status={LeadStatus.NEW}')
        assert response.status_code == 200
        leads = json.loads(response.data)

        # All returned leads should have 'new' status
        for lead in leads:
            assert lead['status'] == LeadStatus.NEW

        # Should have 2 new leads
        assert len(leads) == 2


@pytest.mark.integration
class TestAppointmentsIntegration:
    """Integration tests for appointments endpoint."""

    def test_appointments_list_with_lead_info(self, client, test_db):
        """Test appointments endpoint returns correct lead information."""
        academy = Academy.query.first()

        # Create lead using SQLAlchemy
        lead = Lead(
            academy_id=academy.id,
            phone='+50688888888',
            name='Appointment Test User',
            status=LeadStatus.SCHEDULED,
            source='whatsapp',
            lead_score=8,
            trial_class_date=datetime.strptime('2025-11-20 18:00:00', '%Y-%m-%d %H:%M:%S'),
            created_at=datetime.now()
        )
        db.session.add(lead)
        db.session.commit()

        # Get appointments
        response = client.get('/api/appointments')
        assert response.status_code == 200

        appointments = json.loads(response.data)

        # Should have at least 1 appointment
        assert len(appointments) >= 1

        # Find our appointment
        our_apt = next((a for a in appointments if a['lead_phone'] == '+50688888888'), None)
        assert our_apt is not None
        assert our_apt['lead_name'] == 'Appointment Test User'
        assert our_apt['lead_id'] == lead.id
        assert our_apt['status'] == LeadStatus.SCHEDULED


@pytest.mark.integration
@pytest.mark.slow
class TestCompleteAPIWorkflow:
    """Test complete API workflow scenarios."""

    def test_new_lead_to_appointment_workflow(self, client, test_db):
        """
        Test complete workflow from new lead to scheduled appointment.

        Workflow:
        1. Lead is created
        2. Check stats - should show 1 new lead
        3. View lead detail
        4. Update lead to interested
        5. Schedule trial (set trial_class_date)
        6. Check stats - should show 1 scheduled
        7. View appointments
        """
        academy = Academy.query.first()

        # Step 1: Create lead
        lead = Lead(
            academy_id=academy.id,
            phone='+50677777777',
            name='Workflow Test',
            status=LeadStatus.NEW,
            source='whatsapp',
            lead_score=5,
            created_at=datetime.now()
        )
        db.session.add(lead)
        db.session.commit()
        lead_id = lead.id

        # Create conversation and messages
        conv = Conversation(
            lead_id=lead_id,
            is_active=True,
            created_at=datetime.now(),
            last_message_at=datetime.now()
        )
        db.session.add(conv)
        db.session.commit()

        msg = Message(
            conversation_id=conv.id,
            direction=MessageDirection.INBOUND,
            content='Hola',
            created_at=datetime.now()
        )
        db.session.add(msg)
        db.session.commit()

        # Step 2: Check initial stats
        response = client.get('/api/stats')
        data = json.loads(response.data)
        assert data['new'] >= 1

        # Step 3: View lead detail
        response = client.get(f'/api/leads/{lead_id}')
        assert response.status_code == 200
        detail = json.loads(response.data)
        assert detail['lead']['status'] == LeadStatus.NEW
        assert len(detail['messages']) >= 1

        # Step 4: Update to interested
        response = client.post(
            f'/api/leads/{lead_id}/update-status',
            json={'status': LeadStatus.INTERESTED},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Step 5: Schedule trial (simulate booking)
        lead = Lead.query.get(lead_id)
        lead.status = LeadStatus.SCHEDULED
        lead.trial_class_date = datetime.now() + timedelta(days=1)
        lead.lead_score = 9
        db.session.commit()

        # Step 6: Check updated stats
        response = client.get('/api/stats')
        data = json.loads(response.data)
        assert data['scheduled'] >= 1

        # Step 7: View appointments
        response = client.get('/api/appointments')
        appointments = json.loads(response.data)

        # Find our appointment
        our_apt = next((a for a in appointments if a['lead_id'] == lead_id), None)
        assert our_apt is not None
        assert our_apt['status'] == LeadStatus.SCHEDULED
        assert our_apt['confirmed'] is True  # Scheduled status implies confirmed
        assert our_apt['lead_name'] == 'Workflow Test'
