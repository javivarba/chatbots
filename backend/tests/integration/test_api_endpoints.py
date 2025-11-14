"""
Integration tests for API endpoints.

Tests the complete flow of API requests including database interactions.
"""

import pytest
import json
from datetime import datetime, timedelta

from app import create_app
from app.utils.database import execute_insert, execute_query


@pytest.fixture
def app(test_db):
    """Create Flask app for integration testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = test_db
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
        - 5 new leads
        - 2 contacted leads
        - 3 interested leads
        - 1 scheduled appointment
        """
        # Create leads with different statuses
        leads_data = [
            ('+50611111111', 'User 1', 'new'),
            ('+50622222222', 'User 2', 'new'),
            ('+50633333333', 'User 3', 'contacted'),
            ('+50644444444', 'User 4', 'contacted'),
            ('+50655555555', 'User 5', 'interested'),
        ]

        lead_ids = []
        for phone, name, status in leads_data:
            lead_id = execute_insert(
                "INSERT INTO lead (phone_number, name, status) VALUES (?, ?, ?)",
                (phone, name, status),
                db_path=test_db
            )
            lead_ids.append(lead_id)

        # Create appointment for one lead
        execute_insert(
            """INSERT INTO appointment (lead_id, appointment_datetime, status, confirmed)
               VALUES (?, ?, 'scheduled', 1)""",
            (lead_ids[4], (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d 18:00:00')),
            db_path=test_db
        )

        # Get stats
        response = client.get('/api/stats')
        assert response.status_code == 200

        data = json.loads(response.data)

        # Verify stats
        assert data['total_leads'] == 5
        assert data['new'] == 2
        assert data['contacted'] == 2
        assert data['interested'] == 1
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
        # Step 1: Create lead via database
        lead_id = execute_insert(
            "INSERT INTO lead (phone_number, name, status, interest_level) VALUES (?, ?, ?, ?)",
            ('+50699999999', 'Flow Test', 'new', 5),
            db_path=test_db
        )

        # Create conversation
        conv_id = execute_insert(
            "INSERT INTO conversation (lead_id, academy_id, status) VALUES (?, 1, 'active')",
            (lead_id,),
            db_path=test_db
        )

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
            json={'status': 'interested'},
            content_type='application/json'
        )
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True

        # Verify status was updated
        leads = execute_query(
            "SELECT status FROM lead WHERE id = ?",
            (lead_id,),
            db_path=test_db
        )
        assert leads[0]['status'] == 'interested'

        # Step 5: Add note
        response = client.post(
            f'/api/leads/{lead_id}/add-note',
            json={'note': 'Integration test note'},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Verify note was added
        messages = execute_query(
            "SELECT * FROM message WHERE conversation_id = ? AND sender = 'admin'",
            (conv_id,),
            db_path=test_db
        )
        assert len(messages) >= 1
        assert any('Integration test note' in m['content'] for m in messages)

    def test_leads_filtering(self, client, test_db):
        """Test leads filtering by status."""
        # Create leads with different statuses
        statuses = ['new', 'contacted', 'interested', 'new', 'contacted']
        for i, status in enumerate(statuses):
            execute_insert(
                "INSERT INTO lead (phone_number, name, status) VALUES (?, ?, ?)",
                (f'+5061111111{i}', f'User {i}', status),
                db_path=test_db
            )

        # Filter by 'new' status
        response = client.get('/api/leads?status=new')
        assert response.status_code == 200
        leads = json.loads(response.data)

        # All returned leads should have 'new' status
        for lead in leads:
            assert lead['status'] == 'new'

        # Should have 2 new leads
        assert len(leads) == 2


@pytest.mark.integration
class TestAppointmentsIntegration:
    """Integration tests for appointments endpoint."""

    def test_appointments_list_with_lead_info(self, client, test_db):
        """Test appointments endpoint returns correct lead information."""
        # Create lead
        lead_id = execute_insert(
            "INSERT INTO lead (phone_number, name, status) VALUES (?, ?, ?)",
            ('+50688888888', 'Appointment Test User', 'interested'),
            db_path=test_db
        )

        # Create multiple appointments
        appointments_data = [
            ('2025-11-20 18:00:00', 'scheduled', 1),
            ('2025-11-22 18:00:00', 'scheduled', 0),
            ('2025-11-15 18:00:00', 'cancelled', 0),
        ]

        for datetime_str, status, confirmed in appointments_data:
            execute_insert(
                """INSERT INTO appointment (lead_id, appointment_datetime, status, confirmed)
                   VALUES (?, ?, ?, ?)""",
                (lead_id, datetime_str, status, confirmed),
                db_path=test_db
            )

        # Get appointments
        response = client.get('/api/appointments')
        assert response.status_code == 200

        appointments = json.loads(response.data)

        # Should not include cancelled appointments
        assert all(a['status'] != 'cancelled' for a in appointments)

        # Should have 2 scheduled appointments
        scheduled = [a for a in appointments if a['status'] == 'scheduled']
        assert len(scheduled) >= 2

        # Verify lead info is included
        for apt in scheduled:
            if apt['lead_phone'] == '+50688888888':
                assert apt['lead_name'] == 'Appointment Test User'
                assert apt['lead_id'] == lead_id


@pytest.mark.integration
@pytest.mark.slow
class TestCompleteAPIWorkflow:
    """Test complete API workflow scenarios."""

    def test_new_lead_to_appointment_workflow(self, client, test_db):
        """
        Test complete workflow from new lead to scheduled appointment.

        Workflow:
        1. Lead is created (via message handling - simulated here)
        2. Check stats - should show 1 new lead
        3. View lead detail
        4. Update lead to interested
        5. Book trial week (simulated)
        6. Check stats - should show 1 scheduled
        7. View appointments
        """
        # Step 1: Create lead
        lead_id = execute_insert(
            "INSERT INTO lead (phone_number, name, status, interest_level) VALUES (?, ?, ?, ?)",
            ('+50677777777', 'Workflow Test', 'new', 5),
            db_path=test_db
        )

        # Create conversation and messages
        conv_id = execute_insert(
            "INSERT INTO conversation (lead_id, academy_id, status) VALUES (?, 1, 'active')",
            (lead_id,),
            db_path=test_db
        )

        execute_insert(
            "INSERT INTO message (conversation_id, sender, content) VALUES (?, 'user', 'Hola')",
            (conv_id,),
            db_path=test_db
        )

        # Step 2: Check initial stats
        response = client.get('/api/stats')
        data = json.loads(response.data)
        assert data['new'] >= 1

        # Step 3: View lead detail
        response = client.get(f'/api/leads/{lead_id}')
        assert response.status_code == 200
        detail = json.loads(response.data)
        assert detail['lead']['status'] == 'new'
        assert len(detail['messages']) >= 1

        # Step 4: Update to interested
        response = client.post(
            f'/api/leads/{lead_id}/update-status',
            json={'status': 'interested'},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Step 5: Book trial week
        trial_id = execute_insert(
            """INSERT INTO trial_weeks (lead_id, clase_tipo, start_date, end_date, status)
               VALUES (?, 'jiu_jitsu_adultos', ?, ?, 'active')""",
            (lead_id, datetime.now().strftime('%Y-%m-%d'),
             (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')),
            db_path=test_db
        )

        # Create appointment
        execute_insert(
            """INSERT INTO appointment (lead_id, appointment_datetime, status, confirmed)
               VALUES (?, ?, 'scheduled', 1)""",
            (lead_id, (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 18:00:00')),
            db_path=test_db
        )

        # Step 6: Check updated stats
        response = client.get('/api/stats')
        data = json.loads(response.data)
        assert data['scheduled'] >= 1

        # Step 7: View appointments
        response = client.get('/api/appointments')
        appointments = json.loads(response.data)

        # Find our appointment
        our_apt = None
        for apt in appointments:
            if apt['lead_id'] == lead_id:
                our_apt = apt
                break

        assert our_apt is not None
        assert our_apt['status'] == 'scheduled'
        assert our_apt['confirmed'] == 1
        assert our_apt['lead_name'] == 'Workflow Test'
