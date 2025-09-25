"""
Message Processor Service con integración de OpenAI
"""

from app.models import Lead, Conversation, Academy
from backend.app.services.openai_service import AIService
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Servicio principal para procesar mensajes con IA
    """
    
    def __init__(self):
        """Inicializa el procesador con servicio de IA"""
        self.ai_service = AIService()
        logger.info(f"MessageProcessor iniciado. AI habilitada: {self.ai_service.enabled}")
    
    def process_message(self, message, lead, conversation, academy):
        """
        Procesa un mensaje usando IA si está disponible
        """
        try:
            # Si OpenAI está configurado, usarlo
            if self.ai_service.enabled:
                logger.info("Usando OpenAI para generar respuesta")
                response = self.ai_service.generate_response(
                    message=message,
                    lead=lead,
                    conversation=conversation,
                    academy=academy,
                    use_history=True
                )
                
                # Actualizar estado del lead basado en la conversación
                self._update_lead_status(message, lead)
                
                return response
            else:
                # Fallback a respuestas predefinidas
                logger.info("OpenAI no disponible, usando respuestas predefinidas")
                return self._generate_static_response(message, lead, academy)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return self._get_error_response(academy)
    
    def _update_lead_status(self, message, lead):
        """Actualiza el estado del lead basado en la interacción"""
        msg_lower = message.lower()
        
        # Si es primera interacción
        if lead.status == "new":
            lead.status = "engaged"
        
        # Si muestra interés en clase de prueba
        if any(word in msg_lower for word in ["prueba", "probar", "agendar", "clase gratis"]):
            if lead.status in ["engaged", "interested"]:
                lead.status = "interested"
        
        # Actualizar score
        if hasattr(lead, "calculate_lead_score"):
            lead.calculate_lead_score()
    
    def _generate_static_response(self, message, lead, academy):
        """Genera respuesta estática cuando AI no está disponible"""
        msg_lower = message.lower().strip()
        
        # Detectar intención básica
        if any(word in msg_lower for word in ["hola", "hi", "buenos"]):
            return self._greeting_response(academy, lead)
        elif any(word in msg_lower for word in ["precio", "costo", "cuanto"]):
            return self._pricing_response(academy)
        elif any(word in msg_lower for word in ["horario", "hora", "cuando"]):
            return self._schedule_response(academy)
        elif any(word in msg_lower for word in ["donde", "direccion", "ubicacion"]):
            return self._location_response(academy)
        elif any(word in msg_lower for word in ["prueba", "gratis", "probar"]):
            return self._trial_response(academy)
        else:
            return self._default_response(academy)
    
    # Métodos de respuestas estáticas (los mismos de antes)
    def _greeting_response(self, academy, lead):
        name = lead.name if lead.name and lead.name != "WhatsApp User" else ""
        greeting = f"¡Hola {name}!" if name else "¡Hola!"
        return (
            f"{greeting} Bienvenido a {academy.name} 🥋\n\n"
            f"Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?\n\n"
            f"• 📅 Horarios de clases\n"
            f"• 💰 Precios y planes\n"
            f"• 🎯 Clase de prueba GRATIS\n"
            f"• 📍 Ubicación\n"
            f"• 🥋 Info para principiantes"
        )
    
    def _pricing_response(self, academy):
        return (
            f"💰 **PRECIOS - {academy.name}**\n\n"
            f"• Adultos: $120/mes\n"
            f"• Niños: $80/mes\n"
            f"• Clase suelta: $25\n\n"
            f"✨ ¡Primera clase GRATIS!\n\n"
            f"¿Te gustaría agendar tu clase de prueba?"
        )
    
    def _schedule_response(self, academy):
        return (
            f"📅 **HORARIOS**\n\n"
            f"Lun-Vie:\n"
            f"• 6:00am - 9:00am\n"
            f"• 12:00pm - 1:00pm\n"
            f"• 5:00pm - 9:00pm\n\n"
            f"Sábados:\n"
            f"• 9:00am - 12:00pm\n\n"
            f"¿Cuál horario te conviene?"
        )
    
    def _location_response(self, academy):
        return (
            f"📍 **UBICACIÓN**\n\n"
            f"{academy.address_street}\n"
            f"{academy.address_city}, {academy.address_state}\n\n"
            f"📞 {academy.phone}\n\n"
            f"¿Necesitas ayuda para llegar?"
        )
    
    def _trial_response(self, academy):
        return (
            f"🎉 ¡Excelente decisión!\n\n"
            f"Tu primera clase es GRATIS en {academy.name}.\n\n"
            f"Por favor compárteme:\n"
            f"1. Tu nombre completo\n"
            f"2. ¿Qué día prefieres venir?\n\n"
            f"¡Te esperamos! 🥋"
        )
    
    def _default_response(self, academy):
        return (
            f"Gracias por contactar a {academy.name}! 🥋\n\n"
            f"¿Cómo puedo ayudarte?\n\n"
            f"• Escribe 'horarios' para ver las clases\n"
            f"• Escribe 'precios' para ver costos\n"
            f"• Escribe 'prueba' para clase gratis\n"
            f"• Escribe 'ubicación' para la dirección"
        )
    
    def _get_error_response(self, academy):
        return (
            f"Disculpa, tuve un problema procesando tu mensaje.\n\n"
            f"Por favor llámanos al {academy.phone} o intenta de nuevo.\n\n"
            f"También puedes escribir:\n"
            f"• 'horarios'\n"
            f"• 'precios'\n"
            f"• 'clase de prueba'"
        )
