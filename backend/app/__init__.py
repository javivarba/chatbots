# IMPORTANT: Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from twilio.twiml.messaging_response import MessagingResponse
from datetime import timedelta
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize Limiter (using memory instead of Redis to reduce connections)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use in-memory storage instead of Redis
)

def create_app(config_name='default'):
    app = Flask(__name__)

    # Configuración básica
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bjj_academy.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(
        seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(
        seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    )

    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    limiter.init_app(app)

    # Custom rate limit exceeded handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handler personalizado para rate limit exceeded"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': f'Has excedido el límite de requests permitidos. {e.description}',
            'retry_after': getattr(e, 'retry_after', None)
        }), 429

    # Import and register blueprints here to avoid circular imports
    from app.api.dashboard_routes import dashboard_bp
    from app.api.auth_routes import auth_bp
    from app.services.message_processor import MessageProcessor
    from app.schemas import WhatsAppWebhookRequest
    from app.utils.validation import validate_form

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    # Inicializar message processor (nuevo orquestador)
    message_handler = MessageProcessor()
    
    # Ruta raíz para Twilio
    @app.route('/', methods=['GET', 'POST'])
    @validate_form(WhatsAppWebhookRequest)  # ✅ Validación automática con Pydantic
    def root(validated_data: WhatsAppWebhookRequest = None):
        """
        Ruta raíz que Twilio busca

        POST: Recibe webhooks de WhatsApp (validado con Pydantic)
        GET: Health check
        """
        if request.method == 'POST' and validated_data:
            # Datos ya validados y sanitizados por Pydantic
            incoming_msg = validated_data.Body           # Ya sanitizado (HTML escapado)
            from_number = validated_data.From            # Ya normalizado
            sender_name = validated_data.ProfileName     # Ya sanitizado

            print(f"[WEBHOOK] ✅ Datos validados con Pydantic")
            print(f"[WEBHOOK] Número normalizado: {from_number}")
            print(f"[WEBHOOK] Nombre: {sender_name or 'Sin nombre'}")
            print(f"[WEBHOOK] Mensaje: {incoming_msg[:50]}...")

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
            # GET request - health check
            return jsonify({'status': 'active', 'webhook': 'ready', 'validation': 'pydantic'})
    
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

    # Login route
    @app.route('/login')
    def login():
        return render_template('login.html')

    # Registrar blueprints
    app.register_blueprint(auth_bp)  # Authentication routes
    app.register_blueprint(dashboard_bp)  # Dashboard API routes

    return app
