"""
Pytest configuration and fixtures for BJJ Academy Bot tests - MIGRATED TO SQLALCHEMY
"""

import os
import sys
import pytest
from datetime import datetime

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


@pytest.fixture(scope='function')
def test_db():
    """
    Create a fresh test database for each test using SQLAlchemy.
    Uses in-memory SQLite database for fast testing.
    """
    import os
    from app import create_app, db
    from app.models import Academy

    # Force in-memory SQLite for tests
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

    # Create Flask app with in-memory SQLite
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.app_context():
        # Create all tables
        db.create_all()

        # Insert test academy with all required fields
        academy = Academy(
            id=1,
            name='BJJ Mingo Test',
            slug='bjj-mingo-test',  # Required field
            email='test@bjjmingo.com',  # Required field
            description='Test Academy',
            instructor_name='Test Instructor',
            instructor_belt='Black Belt',
            phone='+506-8888-8888',
            address_street='Test Street',
            address_city='Santo Domingo',
            created_at=datetime.now()
        )
        db.session.add(academy)
        db.session.commit()

        yield None  # Tests run here

        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_lead(test_db):
    """Create a sample lead for testing using SQLAlchemy."""
    from app import db
    from app.models import Lead, Academy, LeadStatus

    academy = Academy.query.first()

    lead = Lead(
        academy_id=academy.id,
        phone='+50612345678',
        name='Test User',
        status=LeadStatus.NEW,
        source='whatsapp',
        lead_score=5,
        created_at=datetime.now()
    )
    db.session.add(lead)
    db.session.commit()

    return lead.id


@pytest.fixture
def sample_conversation(test_db, sample_lead):
    """Create a sample conversation for testing using SQLAlchemy."""
    from app import db
    from app.models import Conversation, Academy

    academy = Academy.query.first()

    conversation = Conversation(
        lead_id=sample_lead,
        academy_id=academy.id,
        platform='whatsapp',  # Required field
        is_active=True,
        created_at=datetime.now(),
        last_message_at=datetime.now()
    )
    db.session.add(conversation)
    db.session.commit()

    return conversation.id


@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI client for testing."""
    mock_client = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.choices = [mocker.Mock()]
    mock_response.choices[0].message.content = "Test response from AI"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_twilio_client(mocker):
    """Mock Twilio client for testing."""
    mock_client = mocker.Mock()
    mock_message = mocker.Mock()
    mock_message.sid = "TEST_SID_123"
    mock_message.status = "sent"
    mock_client.messages.create.return_value = mock_message
    return mock_client
