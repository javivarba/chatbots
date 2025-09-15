# app/__init__.py o donde inicialices tu Flask app
from flask import Flask
from app.routes.webhooks import webhook_bp

def create_app():
    app = Flask(__name__)
    
    # ... otras configuraciones ...
    
    # Registrar blueprints
    app.register_blueprint(webhook_bp, url_prefix='/api')
    
    return app