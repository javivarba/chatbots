# app/routes/webhooks.py
from flask import Blueprint, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import logging

webhook_bp = Blueprint('webhooks', __name__)
logger = logging.getLogger(__name__)

@webhook_bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages from Twilio"""
    try:
        # Log incoming request
        logger.info(f"Received webhook: {request.form}")
        
        # Get message details
        from_number = request.form.get('From', '')
        to_number = request.form.get('To', '')
        body = request.form.get('Body', '')
        message_sid = request.form.get('MessageSid', '')
        
        logger.info(f"Message from {from_number}: {body}")
        
        # Create TwiML response
        resp = MessagingResponse()
        
        # Simple echo response for testing
        resp.message(f"Hola! Recibimos tu mensaje: '{body}'")
        
        # Return TwiML response
        return str(resp), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500