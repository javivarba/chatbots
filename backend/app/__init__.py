from flask import Flask, jsonify, request, render_template
from twilio.twiml.messaging_response import MessagingResponse
from app.api.dashboard_routes import dashboard_bp
from app.services.message_handler import MessageHandler
import os

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configuración básica
    app.config['SECRET_KEY'] = 'dev-secret-key'
    
    # Inicializar message handler
    message_handler = MessageHandler()
    
    # Ruta raíz para Twilio
    @app.route('/', methods=['GET', 'POST'])
    def root():
        """Ruta raíz que Twilio busca"""
        if request.method == 'POST':
            # Obtener datos del mensaje
            incoming_msg = request.values.get('Body', '').strip()
            from_number = request.values.get('From', '').replace('whatsapp:', '')
            sender_name = request.values.get('ProfileName', '')
            
            print(f"📱 Mensaje de {from_number}: {incoming_msg}")
            
            # Procesar mensaje y guardar en BD
            response_text = message_handler.process_message(
                from_number, 
                incoming_msg, 
                sender_name
            )
            
            # Crear respuesta de Twilio
            resp = MessagingResponse()
            resp.message(response_text)
            
            return str(resp)
        else:
            return jsonify({'status': 'active', 'webhook': 'ready'})
    
    # Health endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'message': 'Server is running'})
    
    # Webhook alternativo
    @app.route('/webhook/whatsapp', methods=['GET', 'POST'])
    def whatsapp_webhook():
        return root()
    
    # Dashboard route
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
    
    # Registrar blueprint del dashboard
    app.register_blueprint(dashboard_bp)
    
    return app
