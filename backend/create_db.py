from app import create_app, db
from app.models import Academy, Lead, Conversation, Message, TeamMember

app = create_app('default')

with app.app_context():
    print('🔄 Creando base de datos SQLite...')
    
    # Crear todas las tablas
    db.create_all()
    
    print('✅ Tablas creadas exitosamente!')
    
    # Verificar qué tablas se crearon
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print('\n📊 Tablas en la base de datos:')
    for table in tables:
        print(f'  - {table}')
