"""
Unit tests for database utilities module.

DEPRECATED: These tests are for legacy SQLite utilities in app/utils/deprecated/database.py
They are excluded from pytest by default (see pytest.ini --ignore flag)

The project has been migrated to PostgreSQL with SQLAlchemy.
Use tests in test_message_handler.py, test_appointment_scheduler.py, etc. instead.
"""

import pytest
import sqlite3
from app.utils.deprecated.database import (
    DatabaseConfig,
    get_db_connection,
    get_db_cursor,
    execute_query,
    execute_insert,
    execute_update,
    table_exists,
    get_table_info
)


class TestDatabaseConfig:
    """Test DatabaseConfig singleton."""

    def test_singleton_instance(self):
        """Test that DatabaseConfig is a singleton."""
        config1 = DatabaseConfig()
        config2 = DatabaseConfig()
        assert config1 is config2

    def test_set_and_get_db_path(self, test_db):
        """Test setting and getting database path."""
        DatabaseConfig.set_db_path(test_db)
        assert DatabaseConfig.get_db_path() == test_db


class TestGetDbConnection:
    """Test get_db_connection context manager."""

    def test_connection_opens_and_closes(self, test_db):
        """Test that connection opens and closes properly."""
        with get_db_connection(db_path=test_db) as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)
            # Test that we can execute a query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_row_factory_enabled(self, test_db):
        """Test that row factory is enabled by default."""
        with get_db_connection(db_path=test_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM academy WHERE id = 1")
            row = cursor.fetchone()
            # Should be able to access by column name
            assert row['name'] == 'BJJ Mingo Test'

    def test_row_factory_disabled(self, test_db):
        """Test that row factory can be disabled."""
        with get_db_connection(db_path=test_db, row_factory=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM academy WHERE id = 1")
            row = cursor.fetchone()
            # Should be a tuple
            assert isinstance(row, tuple)
            assert row[0] == 'BJJ Mingo Test'

    def test_exception_handling(self, test_db):
        """Test that exceptions are properly handled."""
        with pytest.raises(sqlite3.OperationalError):
            with get_db_connection(db_path=test_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM non_existent_table")


class TestGetDbCursor:
    """Test get_db_cursor context manager."""

    def test_cursor_auto_commit(self, test_db):
        """Test that cursor auto-commits on success."""
        with get_db_cursor(db_path=test_db) as cursor:
            cursor.execute("""
                INSERT INTO lead (phone_number, name)
                VALUES ('+50699999999', 'Auto Commit Test')
            """)

        # Verify data was committed
        with get_db_connection(db_path=test_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM lead WHERE phone_number = '+50699999999'")
            result = cursor.fetchone()
            assert result['name'] == 'Auto Commit Test'

    def test_cursor_auto_rollback_on_error(self, test_db):
        """Test that cursor auto-rolls back on error."""
        try:
            with get_db_cursor(db_path=test_db) as cursor:
                cursor.execute("""
                    INSERT INTO lead (phone_number, name)
                    VALUES ('+50688888888', 'Rollback Test')
                """)
                # Force an error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify data was rolled back
        with get_db_connection(db_path=test_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM lead WHERE phone_number = '+50688888888'")
            result = cursor.fetchone()
            assert result['count'] == 0


class TestExecuteQuery:
    """Test execute_query helper function."""

    def test_execute_simple_query(self, test_db):
        """Test executing a simple SELECT query."""
        results = execute_query("SELECT * FROM academy WHERE id = ?", (1,), db_path=test_db)
        assert len(results) == 1
        assert results[0]['name'] == 'BJJ Mingo Test'

    def test_execute_query_no_results(self, test_db):
        """Test query with no results."""
        results = execute_query("SELECT * FROM academy WHERE id = ?", (999,), db_path=test_db)
        assert len(results) == 0

    def test_execute_query_multiple_results(self, test_db, sample_lead):
        """Test query with multiple results."""
        # Insert more leads
        with get_db_cursor(db_path=test_db) as cursor:
            cursor.execute("INSERT INTO lead (phone_number, name) VALUES ('+50611111111', 'Test 1')")
            cursor.execute("INSERT INTO lead (phone_number, name) VALUES ('+50622222222', 'Test 2')")

        results = execute_query("SELECT * FROM lead ORDER BY id", db_path=test_db)
        assert len(results) >= 3


class TestExecuteInsert:
    """Test execute_insert helper function."""

    def test_insert_returns_lastrowid(self, test_db):
        """Test that insert returns the last inserted row ID."""
        row_id = execute_insert(
            "INSERT INTO lead (phone_number, name) VALUES (?, ?)",
            ('+50677777777', 'Insert Test'),
            db_path=test_db
        )
        assert row_id > 0

        # Verify the insert
        results = execute_query("SELECT * FROM lead WHERE id = ?", (row_id,), db_path=test_db)
        assert len(results) == 1
        assert results[0]['name'] == 'Insert Test'


class TestExecuteUpdate:
    """Test execute_update helper function."""

    def test_update_returns_rowcount(self, test_db, sample_lead):
        """Test that update returns the number of affected rows."""
        affected = execute_update(
            "UPDATE lead SET name = ? WHERE id = ?",
            ('Updated Name', sample_lead),
            db_path=test_db
        )
        assert affected == 1

        # Verify the update
        results = execute_query("SELECT name FROM lead WHERE id = ?", (sample_lead,), db_path=test_db)
        assert results[0]['name'] == 'Updated Name'

    def test_delete_returns_rowcount(self, test_db, sample_lead):
        """Test that delete returns the number of affected rows."""
        affected = execute_update(
            "DELETE FROM lead WHERE id = ?",
            (sample_lead,),
            db_path=test_db
        )
        assert affected == 1

        # Verify the delete
        results = execute_query("SELECT * FROM lead WHERE id = ?", (sample_lead,), db_path=test_db)
        assert len(results) == 0


class TestTableExists:
    """Test table_exists helper function."""

    def test_table_exists_true(self, test_db):
        """Test checking for existing table."""
        assert table_exists('lead', db_path=test_db) is True
        assert table_exists('academy', db_path=test_db) is True

    def test_table_exists_false(self, test_db):
        """Test checking for non-existing table."""
        assert table_exists('non_existent_table', db_path=test_db) is False


class TestGetTableInfo:
    """Test get_table_info helper function."""

    def test_get_table_info(self, test_db):
        """Test getting table schema information."""
        info = get_table_info('lead', db_path=test_db)
        assert len(info) > 0

        # Extract column names
        columns = [row['name'] for row in info]
        assert 'id' in columns
        assert 'phone_number' in columns
        assert 'name' in columns
        assert 'status' in columns
