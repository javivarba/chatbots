from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import Lead, Conversation, Message, Academy
from app.services.message_processor import MessageProcessor

whatsapp_bp = Blueprint("whatsapp", __name__)

@whatsapp_bp.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    """Endpoint principal para recibir mensajes de WhatsApp"""
    try:
        # Extraer información del mensaje
        from_number = request.form.get("From", "").replace("whatsapp:", "")
        message_body = request.form.get("Body", "").strip()
        profile_name = request.form.get("ProfileName", "")
        
        print(f"Mensaje de {from_number} ({profile_name}): {message_body}")
        
        # Obtener o crear lead
        lead = get_or_create_lead(from_number, profile_name)
        
        # Obtener academia (primera de la BD)
        academy = Academy.query.first()
        if not academy:
            print("ERROR: No hay academia en la BD")
            return create_xml_response("Lo siento, el sistema no está configurado correctamente.")
        
        # Obtener o crear conversación
        conversation = get_or_create_conversation(academy.id, lead.id)
        
        # Guardar mensaje entrante
        save_message(conversation.id, message_body, "inbound")
        
        # IMPORTANTE: Usar el MessageProcessor para generar respuesta inteligente
        processor = MessageProcessor()
        response_text = processor.process_message(
            message_body, 
            lead, 
            conversation, 
            academy
        )
        
        print(f"Respuesta generada: {response_text[:100]}...")
        
        # Guardar mensaje de respuesta
        save_message(conversation.id, response_text, "outbound")
        
        # Actualizar último contacto del lead
        lead.last_contact_date = datetime.utcnow()
        db.session.commit()
        
        # Devolver respuesta en formato XML
        return create_xml_response(response_text)
        
    except Exception as e:
        print(f"ERROR en webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_xml_response("Lo siento, hubo un error procesando tu mensaje.")

def create_xml_response(text):
    """Crea respuesta XML para Twilio"""
    # Escapar caracteres especiales para XML
    text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{text}</Message>
</Response>"""
    return xml, 200, {"Content-Type": "text/xml"}

def get_or_create_lead(phone, name=None):
    """Obtiene o crea un lead basado en el número de teléfono"""
    # Limpiar número
    phone_clean = phone.replace("+", "").replace(" ", "").replace("-", "")
    
    lead = Lead.query.filter_by(phone=phone_clean).first()
    
    if not lead:
        lead = Lead(
            academy_id=1,  # Usar primera academia
            phone=phone_clean,
            name=name or "WhatsApp User",
            source="whatsapp",
            status="new"
        )
        db.session.add(lead)
        db.session.commit()
        print(f"Nuevo lead creado: {phone_clean}")
    elif name and name != "Test User" and lead.name == "WhatsApp User":
        lead.name = name
        db.session.commit()
        print(f"Nombre actualizado para lead: {name}")
    
    return lead

def get_or_create_conversation(academy_id, lead_id):
    """Obtiene o crea conversación activa"""
    conv = Conversation.query.filter_by(
        academy_id=academy_id,
        lead_id=lead_id,
        platform="whatsapp",
        is_active=True
    ).first()
    
    if not conv:
        conv = Conversation(
            academy_id=academy_id,
            lead_id=lead_id,
            platform="whatsapp",
            is_active=True
        )
        db.session.add(conv)
        db.session.commit()
        print(f"Nueva conversación creada para lead {lead_id}")
    
    return conv

def save_message(conversation_id, content, direction):
    """Guarda un mensaje en la base de datos"""
    msg = Message(
        conversation_id=conversation_id,
        direction=direction,
        content=content
    )
    db.session.add(msg)
    
    # Actualizar contadores de la conversación
    conv = Conversation.query.get(conversation_id)
    if conv:
        conv.message_count += 1
        if direction == "inbound":
            conv.inbound_count += 1
        else:
            conv.outbound_count += 1
        conv.last_message_at = datetime.utcnow()
    
    db.session.commit()
    print(f"Mensaje guardado: {direction} - {content[:50]}...")

@whatsapp_bp.route("/test", methods=["GET"])
def test():
    """Endpoint de prueba para verificar que el webhook funciona"""
    return jsonify({
        "status": "ok",
        "webhook": "whatsapp",
        "message_processor": "enabled",
        "timestamp": datetime.utcnow().isoformat()
    })
