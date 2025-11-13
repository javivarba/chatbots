"""
WhatsApp Webhook Handler - Fixed for Twilio
Handles both GET (verification) and POST (messages)
"""

from flask import Blueprint, request, jsonify, Response
from twilio.twiml.messaging_response import MessagingResponse
from app.models import db, Lead, Conversation, Message, Academy
from app.services.message_processor import MessageProcessor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear blueprint
whatsapp_bp = Blueprint('whatsapp', __name__)

# Inicializar servicios
message_processor = MessageProcessor()

@whatsapp_bp.route('/webhook/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    """
    Webhook principal para WhatsApp/Twilio
    GET: Verificación del webhook
    POST: Procesamiento de mensajes
    """
    
    # Manejar verificación GET (Twilio webhook validation)
    if request.method == 'GET':
        logger.info("GET request received - Webhook verification")
        # Twilio puede enviar un challenge parameter para verificación
        challenge = request.args.get('challenge', 'webhook_active')
        return jsonify({
            'status': 'active',
            'message': 'WhatsApp webhook is configured',
            'challenge': challenge
        }), 200
    
    # Manejar mensajes POST
    if request.method == 'POST':
        try:
            # Obtener datos del mensaje
            incoming_msg = request.values.get('Body', '').strip()
            from_number = request.values.get('From', '').replace('whatsapp:', '')
            sender_name = request.values.get('ProfileName', 'Unknown')
            
            logger.info(f"Message received from {from_number}: {incoming_msg[:50]}...")
            
            # Validar que tenemos los datos necesarios
            if not incoming_msg or not from_number:
                logger.warning("Missing required fields in request")
                return str(MessagingResponse()), 400
            
            # Obtener o crear lead
            lead = Lead.query.filter_by(phone_number=from_number).first()
            if not lead:
                # Crear nuevo lead
                academy = Academy.query.first()  # Usar la primera academia
                if not academy:
                    # Crear academia de prueba si no existe
                    academy = Academy(
                        name="BJJ Academy Test",
                        phone="+1234567890",
                        email="info@bjjacademy.com",
                        address="123 Main St"
                    )
                    db.session.add(academy)
                    db.session.commit()
                
                lead = Lead(
                    academy_id=academy.id,
                    phone_number=from_number,
                    name=sender_name,
                    source='whatsapp',
                    status='new'
                )
                db.session.add(lead)
                db.session.commit()
                logger.info(f"New lead created: {from_number}")
            
            # Obtener o crear conversación
            conversation = Conversation.query.filter_by(
                lead_id=lead.id,
                status='active'
            ).first()
            
            if not conversation:
                conversation = Conversation(
                    lead_id=lead.id,
                    academy_id=lead.academy_id,
                    status='active'
                )
                db.session.add(conversation)
                db.session.commit()
            
            # Guardar mensaje del usuario
            user_message = Message(
                conversation_id=conversation.id,
                sender='user',
                content=incoming_msg
            )
            db.session.add(user_message)
            
            # Procesar mensaje y generar respuesta
            context = {
                'lead_name': lead.name,
                'conversation_history': [
                    {'sender': m.sender, 'content': m.content}
                    for m in conversation.messages[-5:]  # Últimos 5 mensajes
                ]
            }
            
            response_data = message_processor.process_message(incoming_msg, context)
            
            # Actualizar información del lead basado en la intención
            if response_data.get('intent'):
                lead.intent_detected = response_data['intent']
                if response_data['intent'] in ['pregunta_precio', 'agendar_clase', 'informacion_horarios']:
                    lead.interest_level = min(lead.interest_level + 2, 10)
                    if response_data['intent'] == 'agendar_clase':
                        lead.status = 'interested'
            
            # Guardar mensaje de respuesta
            bot_message = Message(
                conversation_id=conversation.id,
                sender='bot',
                content=response_data['response'],
                intent_detected=response_data.get('intent')
            )
            db.session.add(bot_message)
            db.session.commit()
            
            # Crear respuesta de Twilio
            twilio_resp = MessagingResponse()
            twilio_resp.message(response_data['response'])
            
            logger.info(f"Response sent to {from_number}")
            
            return str(twilio_resp), 200
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            
            # Respuesta de error amigable
            error_resp = MessagingResponse()
            error_resp.message("Disculpa, tuve un problema procesando tu mensaje. ¿Podrías intentarlo de nuevo?")
            
            return str(error_resp), 500

# Endpoint adicional para testing
@whatsapp_bp.route('/webhook/test', methods=['POST'])
def test_webhook():
    """Endpoint de prueba para simular mensajes sin Twilio"""
    try:
        data = request.get_json()
        
        # Simular estructura de Twilio
        fake_twilio_data = {
            'Body': data.get('message', 'Test message'),
            'From': f"whatsapp:{data.get('phone', '+1234567890')}",
            'ProfileName': data.get('name', 'Test User')
        }
        
        # Reusar lógica del webhook principal
        with app.test_request_context(
            '/webhook/whatsapp',
            method='POST',
            data=fake_twilio_data
        ):
            response = whatsapp_webhook()
            
        return jsonify({
            'status': 'success',
            'response': str(response[0]) if isinstance(response, tuple) else str(response)
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
