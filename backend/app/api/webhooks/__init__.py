from flask import Blueprint
from .whatsapp_webhook import whatsapp_bp

# Crear blueprint principal para webhooks
webhook_bp = Blueprint("webhooks", __name__)

# Registrar sub-blueprints
webhook_bp.register_blueprint(whatsapp_bp, url_prefix="/whatsapp")

@webhook_bp.route("/test")
def test():
    return {"status": "webhooks working"}