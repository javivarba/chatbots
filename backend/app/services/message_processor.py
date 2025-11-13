"""
Message Processor Service con integración de OpenAI
Versión simplificada para BJJ Mingo
"""

from app.models import Lead, Conversation, Academy
from app.services.ai_service import AIService
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Servicio principal para procesar mensajes con IA
    Versión simplificada - delega toda la generación a AIService
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
                # Fallback simplificado - solo referir al teléfono
                logger.info("OpenAI no disponible, usando respuesta de fallback")
                return self._generate_fallback_response(academy)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return self._generate_fallback_response(academy)
    
    def _update_lead_status(self, message, lead):
        """Actualiza el estado del lead basado en la interacción"""
        msg_lower = message.lower()
        
        # Si es primera interacción
        if lead.status == "new":
            lead.status = "engaged"
            logger.info(f"Lead {lead.id} actualizado a 'engaged'")
        
        # Si muestra interés en semana de prueba
        if any(word in msg_lower for word in ["prueba", "probar", "agendar", "semana", "gratis"]):
            if lead.status in ["engaged", "interested"]:
                lead.status = "interested"
                logger.info(f"Lead {lead.id} actualizado a 'interested'")
        
        # Actualizar score si el método existe
        if hasattr(lead, "calculate_lead_score"):
            lead.calculate_lead_score()
            logger.info(f"Score actualizado para lead {lead.id}")
    
    def _generate_fallback_response(self, academy):
        """Respuesta simplificada cuando AI no está disponible"""
        return (
            f"¡Hola! En este momento no puedo procesar tu mensaje automáticamente.\n\n"
            f"Por favor contactanos directamente:\n"
            f"📞 WhatsApp: {academy.phone}\n"
            f"📍 Santo Domingo de Heredia\n\n"
            f"Horarios:\n"
            f"• Jiu-Jitsu Adultos: Lun-Vie 6:00pm\n"
            f"• Striking: Mar-Jue 7:30pm\n"
            f"• Kids/Juniors: Consultar\n\n"
            f"¡Te esperamos para tu semana de prueba GRATIS! 🥋"
        )