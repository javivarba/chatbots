from app import create_app, db
from app.models import Academy

app = create_app('default')

with app.app_context():
    print("\n=== ACTUALIZANDO DATOS DE LA ACADEMIA ===\n")
    
    # Obtener la academia actual
    academy = Academy.query.first()
    
    if academy:
        print(f"Datos actuales:")
        print(f"  Nombre: {academy.name}")
        print(f"  Teléfono: {academy.phone}")
        
        # Actualizar datos
        academy.name = "BJJ Santo Domingo"
        academy.slug = "bjj-santo-domingo"
        academy.phone = "+50670036654"
        academy.whatsapp_phone = "+50670036654"
        
        # Actualizar contexto de IA
        academy.ai_context = """
        Somos BJJ Santo Domingo, la mejor academia de Brazilian Jiu-Jitsu en Costa Rica.
        Ofrecemos clases para todos los niveles: principiantes, intermedios y avanzados.
        También tenemos clases para niños desde los 4 años.
        Nuestros horarios son:
        - Lunes a Viernes: 6am-9am, 12pm-1pm, 5pm-9pm
        - Sábados: 9am-12pm
        Primera clase es GRATIS.
        Mensualidad: $120 adultos, $80 niños
        Ubicación: Santo Domingo de Heredia, Costa Rica
        Teléfono/WhatsApp: +50670036654
        """
        
        # También actualizar la descripción
        academy.description = "Academia líder de Brazilian Jiu-Jitsu en Santo Domingo, Costa Rica"
        academy.address_city = "Santo Domingo"
        academy.address_state = "Heredia"
        academy.address_country = "Costa Rica"
        academy.timezone = "America/Santo_Domingo"
        
        db.session.commit()
        
        print(f"\n✅ Datos actualizados:")
        print(f"  Nombre: {academy.name}")
        print(f"  Teléfono: {academy.phone}")
        print(f"  Ciudad: {academy.address_city}")
        print(f"  País: {academy.address_country}")
        
    else:
        print("❌ No se encontró ninguna academia")
