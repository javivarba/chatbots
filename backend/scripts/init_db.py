"""
Script para inicializar la base de datos con datos de prueba
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app import create_app, db
from app.models import Academy, Lead, LeadStatus, LeadSource, Conversation, Message, MessageDirection

def init_database():
    """Inicializa la base de datos con estructura y datos de prueba"""
    
    app = create_app('default')
    
    with app.app_context():
        print("🔄 Inicializando base de datos...")
        
        # Crear todas las tablas
        db.create_all()
        print("✅ Tablas creadas")
        
        # Verificar si ya hay datos
        if Academy.query.first():
            print("⚠️  La base de datos ya contiene datos. ¿Desea reiniciarla? (s/n): ", end="")
            response = input().lower()
            if response != 's':
                print("❌ Operación cancelada")
                return
            
            # Limpiar datos existentes
            print("🗑️  Limpiando datos existentes...")
            db.session.query(Message).delete()
            db.session.query(Conversation).delete()
            db.session.query(Lead).delete()
            db.session.query(Academy).delete()
            db.session.commit()
        
        # Crear academia de prueba
        print("📝 Creando academia de prueba...")
        academy = Academy(
            name="BJJ Mingo"
            slug="gb-costa-rica",
            email="info@gbcostarica.com",
            phone="+506 8888-9999",
            website="https://gbcostarica.com",
            
            # Dirección
            address_street="Avenida Central, Local 123",
            address_city="San José",
            address_state="San José",
            address_zip="10101",
            address_country="Costa Rica",
            timezone="America/Costa_Rica",
            
            # Información del negocio
            description="Academia líder de Brazilian Jiu-Jitsu en Costa Rica con más de 10 años de experiencia",
            instructor_name="Carlos Mendez",
            instructor_belt="Black Belt 3rd Degree",
            
            # Configuración de IA
            ai_context="""
            Somos Gracie Barra Costa Rica, la academia de BJJ más grande del país.
            Ofrecemos clases para todos los niveles: principiantes, intermedios y avanzados.
            También tenemos clases para niños desde los 4 años.
            Nuestros horarios son:
            - Lunes a Viernes: 6am-9am, 12pm-1pm, 5pm-9pm
            - Sábados: 9am-12pm
            Primera clase es GRATIS.
            Mensualidad: $120 adultos, $80 niños
            Ubicación: Avenida Central, San José (frente al parque central)
            """,
            
            # Horarios de negocio
            business_hours={
                "monday": {"open": "06:00", "close": "21:00"},
                "tuesday": {"open": "06:00", "close": "21:00"},
                "wednesday": {"open": "06:00", "close": "21:00"},
                "thursday": {"open": "06:00", "close": "21:00"},
                "friday": {"open": "06:00", "close": "21:00"},
                "saturday": {"open": "09:00", "close": "12:00"},
                "sunday": {"open": "", "close": ""}
            },
            
            # Tipos de clases
            class_types=["Principiantes", "Avanzado", "Competición", "Kids", "No-Gi"],
            
            # Precios
            pricing_info={
                "monthly_adult": 120,
                "monthly_kids": 80,
                "drop_in": 25,
                "trial": 0,
                "quarterly": 320
            },
            
            # Configuración de trial
            trial_class_enabled=True,
            trial_class_duration_days=7,
            
            # Configuración de seguimiento
            auto_followup_enabled=True,
            followup_delays_hours=[24, 72, 168],  # 1 día, 3 días, 1 semana
            
            # Estado
            is_active=True,
            subscription_plan='pro',
            subscription_status='active'
        )
        
        db.session.add(academy)
        db.session.commit()
        print(f"✅ Academia creada: {academy.name}")
        
        # Crear algunos leads de prueba
        print("📝 Creando leads de prueba...")
        
        leads_data = [
            {
                "name": "Juan Pérez",
                "phone": "+506 8888-1111",
                "email": "juan@email.com",
                "status": LeadStatus.NEW,
                "source": LeadSource.WHATSAPP,
                "goals": "Quiero ponerme en forma y aprender defensa personal"
            },
            {
                "name": "María González",
                "phone": "+506 8888-2222",
                "email": "maria@email.com",
                "status": LeadStatus.INTERESTED,
                "source": LeadSource.FACEBOOK,
                "goals": "Me interesa empezar BJJ, nunca he practicado artes marciales"
            },
            {
                "name": "Carlos Rodríguez",
                "phone": "+506 8888-3333",
                "status": LeadStatus.SCHEDULED,
                "source": LeadSource.INSTAGRAM,
                "trial_class_date": datetime.utcnow() + timedelta(days=2),
                "experience_level": "beginner"
            },
            {
                "name": "Ana Martínez",
                "phone": "+506 8888-4444",
                "email": "ana@email.com",
                "status": LeadStatus.CONVERTED,
                "source": LeadSource.WHATSAPP,
                "converted_date": datetime.utcnow() - timedelta(days=7)
            }
        ]
        
        for lead_data in leads_data:
            lead = Lead(academy_id=academy.id, **lead_data)
            lead.normalize_phone()
            lead.calculate_lead_score()
            db.session.add(lead)
        
        db.session.commit()
        print(f"✅ {len(leads_data)} leads creados")
        
        # Crear conversación de prueba
        print("📝 Creando conversación de prueba...")
        
        first_lead = Lead.query.first()
        conversation = Conversation(
            academy_id=academy.id,
            lead_id=first_lead.id,
            platform="whatsapp",
            session_id=f"session_{datetime.utcnow().timestamp()}",
            is_active=True
        )
        db.session.add(conversation)
        db.session.commit()
        
        # Agregar mensajes de prueba
        messages = [
            ("Hola, me gustaría información sobre las clases de BJJ", MessageDirection.INBOUND),
            ("¡Hola! Bienvenido a Gracie Barra Costa Rica. Me da mucho gusto que estés interesado en nuestras clases de Brazilian Jiu-Jitsu. ¿Has practicado algún arte marcial antes?", MessageDirection.OUTBOUND),
            ("No, sería mi primera vez", MessageDirection.INBOUND),
            ("¡Perfecto! Tenemos un programa especial para principiantes. Te invito a una clase de prueba GRATIS para que conozcas nuestro método. ¿Te gustaría agendar tu clase de prueba?", MessageDirection.OUTBOUND),
        ]
        
        for content, direction in messages:
            message = Message(
                conversation_id=conversation.id,
                content=content,
                direction=direction
            )
            db.session.add(message)
            conversation.message_count += 1
            if direction == MessageDirection.INBOUND:
                conversation.inbound_count += 1
            else:
                conversation.outbound_count += 1
        
        db.session.commit()
        print(f"✅ Conversación con {len(messages)} mensajes creada")
        
        # Mostrar resumen
        print("\n" + "="*50)
        print("📊 RESUMEN DE LA BASE DE DATOS")
        print("="*50)
        print(f"✅ Academias: {Academy.query.count()}")
        print(f"✅ Leads: {Lead.query.count()}")
        print(f"✅ Conversaciones: {Conversation.query.count()}")
        print(f"✅ Mensajes: {Message.query.count()}")
        print("="*50)
        print("\n✨ Base de datos inicializada exitosamente!")
        print(f"🌐 Puedes ver los datos en pgAdmin: http://localhost:5050")
        print(f"   Email: admin@bjjacademy.com")
        print(f"   Password: admin123")
        
        return True

if __name__ == "__main__":
    init_database()