"""
Migration script to create class_reminders table
Run this with: python -m migrations.create_class_reminders_table
"""

import sys
import os

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(backend_path))

from app import create_app, db

def run_migration():
    """Create the class_reminders table"""
    app = create_app()

    with app.app_context():
        # Import models to register them
        from app.models import ClassReminder, Academy, Lead

        print("Creating class_reminders table...")

        # Create the table
        db.create_all()

        print("OK: class_reminders table created successfully!")

        # Verify table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'class_reminders' in tables:
            print("OK: Verified - class_reminders table exists in database")

            # Show table structure
            columns = inspector.get_columns('class_reminders')
            print("\nTable structure:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")

            # Show indexes
            indexes = inspector.get_indexes('class_reminders')
            if indexes:
                print("\nIndexes:")
                for index in indexes:
                    print(f"  - {index['name']}: {index['column_names']}")
        else:
            print("ERROR: class_reminders table was not created")
            return False

        return True

if __name__ == '__main__':
    try:
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
