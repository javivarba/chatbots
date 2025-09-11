from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import logging

db = SQLAlchemy()
migrate = Migrate()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def create_app(config_name="default"):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    from .config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Import models (importante para que SQLAlchemy los reconozca)
    from app import models
    
    # Register webhooks blueprint
    from app.api.webhooks import webhook_bp
    app.register_blueprint(webhook_bp, url_prefix="/webhooks")
    
    # Health and info routes
    @app.route("/")
    def index():
        return jsonify({
            "name": "BJJ Academy Bot API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "webhooks": {
                    "whatsapp": "/webhooks/whatsapp/webhook",
                    "test": "/webhooks/whatsapp/test"
                }
            }
        })
    
    @app.route("/health")
    def health():
        try:
            # Test database connection
            db.session.execute("SELECT 1")
            db_status = "connected"
        except:
            db_status = "disconnected"
            
        return jsonify({
            "status": "healthy",
            "database": db_status
        })
    
    return app