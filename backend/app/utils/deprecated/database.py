"""
Database utilities for centralized SQLite connection management.

This module provides helper functions and context managers for consistent
database access across the application, preventing connection leaks and
ensuring proper resource cleanup.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration singleton."""

    _instance = None
    _db_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConfig, cls).__new__(cls)
        return cls._instance

    @classmethod
    def set_db_path(cls, db_path: str):
        """Set the database path to use for all connections."""
        cls._db_path = db_path
        logger.info(f"Database path set to: {db_path}")

    @classmethod
    def get_db_path(cls) -> str:
        """Get the current database path."""
        if cls._db_path is None:
            # Default to bjj_academy.db in current directory
            cls._db_path = os.path.join(os.getcwd(), 'bjj_academy.db')
            logger.warning(f"Using default database path: {cls._db_path}")
        return cls._db_path


@contextmanager
def get_db_connection(db_path: Optional[str] = None, row_factory: bool = True):
    """
    Context manager for database connections.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads")
            results = cursor.fetchall()

    Args:
        db_path: Optional path to database file. If None, uses configured path.
        row_factory: If True, use Row factory for dict-like access to columns.

    Yields:
        sqlite3.Connection: Database connection object
    """
    if db_path is None:
        db_path = DatabaseConfig.get_db_path()

    conn = None
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)

        if row_factory:
            conn.row_factory = sqlite3.Row

        logger.debug(f"Database connection opened: {db_path}")
        yield conn

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


@contextmanager
def get_db_cursor(db_path: Optional[str] = None, row_factory: bool = True):
    """
    Context manager that provides a database cursor.

    Automatically commits on success and rolls back on error.

    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("INSERT INTO leads (phone, name) VALUES (?, ?)", (phone, name))

    Args:
        db_path: Optional path to database file. If None, uses configured path.
        row_factory: If True, use Row factory for dict-like access to columns.

    Yields:
        sqlite3.Cursor: Database cursor object
    """
    if db_path is None:
        db_path = DatabaseConfig.get_db_path()

    conn = None
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)

        if row_factory:
            conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        logger.debug(f"Database cursor created: {db_path}")

        yield cursor

        conn.commit()
        logger.debug("Transaction committed")

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
            logger.debug("Transaction rolled back")
        raise

    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


def execute_query(query: str, params: tuple = (), db_path: Optional[str] = None) -> list:
    """
    Execute a SELECT query and return all results.

    Args:
        query: SQL query string
        params: Query parameters tuple
        db_path: Optional database path

    Returns:
        List of Row objects (dict-like access)
    """
    with get_db_cursor(db_path=db_path, row_factory=True) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_insert(query: str, params: tuple = (), db_path: Optional[str] = None) -> int:
    """
    Execute an INSERT query and return the last inserted row ID.

    Args:
        query: SQL INSERT query string
        params: Query parameters tuple
        db_path: Optional database path

    Returns:
        Last inserted row ID
    """
    with get_db_cursor(db_path=db_path) as cursor:
        cursor.execute(query, params)
        return cursor.lastrowid


def execute_update(query: str, params: tuple = (), db_path: Optional[str] = None) -> int:
    """
    Execute an UPDATE or DELETE query and return number of affected rows.

    Args:
        query: SQL UPDATE/DELETE query string
        params: Query parameters tuple
        db_path: Optional database path

    Returns:
        Number of affected rows
    """
    with get_db_cursor(db_path=db_path) as cursor:
        cursor.execute(query, params)
        return cursor.rowcount


def table_exists(table_name: str, db_path: Optional[str] = None) -> bool:
    """
    Check if a table exists in the database.

    Args:
        table_name: Name of the table to check
        db_path: Optional database path

    Returns:
        True if table exists, False otherwise
    """
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    result = execute_query(query, (table_name,), db_path=db_path)
    return len(result) > 0


def get_table_info(table_name: str, db_path: Optional[str] = None) -> list:
    """
    Get schema information for a table.

    Args:
        table_name: Name of the table
        db_path: Optional database path

    Returns:
        List of column information
    """
    query = f"PRAGMA table_info({table_name})"
    return execute_query(query, db_path=db_path)
