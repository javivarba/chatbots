"""
Pytest configuration and fixtures for BJJ Academy Bot tests.
"""

import os
import sys
import pytest
import sqlite3
import tempfile
from datetime import datetime

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Avoid importing from app module at module level to prevent import errors
# Import will happen in fixtures that need it


@pytest.fixture(scope='session')
def test_db_path():
    """Create a temporary test database path."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = temp_db.name
    temp_db.close()
    yield db_path
    # Cleanup - try multiple times for Windows file locks
    for _ in range(3):
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
            break
        except PermissionError:
            import time
            time.sleep(0.1)
            continue


@pytest.fixture(scope='function')
def test_db(test_db_path):
    """
    Create a fresh test database for each test.
    Sets up the schema and returns the db path.
    """
    # Import here to avoid module-level import issues
    from app.utils.database import DatabaseConfig

    # Set the database path for the test
    DatabaseConfig.set_db_path(test_db_path)

    # Create schema
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Drop all tables first to ensure clean state
    cursor.execute("DROP TABLE IF EXISTS message")
    cursor.execute("DROP TABLE IF EXISTS appointment")
    cursor.execute("DROP TABLE IF EXISTS trial_weeks")
    cursor.execute("DROP TABLE IF EXISTS conversation")
    cursor.execute("DROP TABLE IF EXISTS lead")
    cursor.execute("DROP TABLE IF EXISTS leads")
    cursor.execute("DROP TABLE IF EXISTS academy")
    cursor.execute("DROP TABLE IF EXISTS academies")

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academy (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            instructor_name TEXT,
            instructor_belt TEXT,
            phone TEXT,
            address_street TEXT,
            address_city TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            academy_id INTEGER DEFAULT 1,
            phone_number TEXT NOT NULL UNIQUE,
            name TEXT,
            source TEXT DEFAULT 'whatsapp',
            status TEXT DEFAULT 'new',
            interest_level INTEGER DEFAULT 5,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (academy_id) REFERENCES academy(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            academy_id INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_message_at TEXT,
            FOREIGN KEY (lead_id) REFERENCES lead(id),
            FOREIGN KEY (academy_id) REFERENCES academy(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            intent_detected TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversation(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            appointment_datetime TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            confirmed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES lead(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trial_weeks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            clase_tipo TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES lead(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academies (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create 'leads' table (used by appointment_scheduler.py)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            academy_id INTEGER DEFAULT 1,
            phone TEXT NOT NULL UNIQUE,
            name TEXT,
            source TEXT DEFAULT 'whatsapp',
            status TEXT DEFAULT 'new',
            lead_score INTEGER DEFAULT 5,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (academy_id) REFERENCES academy(id)
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO academy (id, name, description, instructor_name, instructor_belt,
                            phone, address_street, address_city)
        VALUES (1, 'BJJ Mingo Test', 'Test Academy', 'Test Instructor', 'Black Belt',
                '+506-8888-8888', 'Test Street', 'Santo Domingo')
    """)

    cursor.execute("""
        INSERT INTO academies (id, name, phone)
        VALUES (1, 'BJJ Mingo Test', '+506-8888-8888')
    """)

    conn.commit()
    conn.close()

    yield test_db_path

    # Cleanup - clear all tables for next test
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM message")
    cursor.execute("DELETE FROM appointment")
    cursor.execute("DELETE FROM trial_weeks")
    cursor.execute("DELETE FROM conversation")
    cursor.execute("DELETE FROM lead")
    cursor.execute("DELETE FROM leads")
    conn.commit()
    conn.close()


@pytest.fixture
def sample_lead(test_db):
    """Create a sample lead for testing."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    # Insert into 'lead' table
    cursor.execute("""
        INSERT INTO lead (phone_number, name, status, interest_level)
        VALUES ('+50612345678', 'Test User', 'new', 5)
    """)
    # Also insert into 'leads' table for appointment_scheduler tests
    cursor.execute("""
        INSERT INTO leads (phone, name, status, lead_score)
        VALUES ('+50612345678', 'Test User', 'new', 5)
    """)
    conn.commit()
    lead_id = cursor.lastrowid
    conn.close()
    return lead_id


@pytest.fixture
def sample_conversation(test_db, sample_lead):
    """Create a sample conversation for testing."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversation (lead_id, academy_id, status)
        VALUES (?, 1, 'active')
    """, (sample_lead,))
    conn.commit()
    conv_id = cursor.lastrowid
    conn.close()
    return conv_id


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
