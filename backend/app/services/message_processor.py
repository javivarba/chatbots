"""
Message Processor Service con integración de OpenAI
Actualizado para BJJ Mingo con voseo costarricense
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
    Actualizado para BJJ Mingo
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
        
        # Si muestra interés en semana de prueba
        if any(word in msg_lower for word in ["prueba", "probar", "agendar", "semana", "gratis"]):
            if lead.status in ["engaged", "interested"]:
                lead.status = "interested"
        
        # Actualizar score
        if hasattr(lead, "calculate_lead_score"):
            lead.calculate_lead_score()
    
    def _generate_static_response(self, message, lead, academy):
        """Genera respuesta estática cuando AI no está disponible"""
        msg_lower = message.lower().strip()
        
        # Detectar intención básica
        if any(word in msg_lower for word in ["hola", "hi", "buenos", "buenas"]):
            return self._greeting_response(academy, lead)
        elif any(word in msg_lower for word in ["precio", "costo", "cuanto", "cuánto"]):
            return self._pricing_response(academy)
        elif any(word in msg_lower for word in ["horario", "hora", "cuando", "cuándo"]):
            return self._schedule_response(academy)
        elif any(word in msg_lower for word in ["donde", "dónde", "direccion", "dirección", "ubicacion", "ubicación"]):
            return self._location_response(academy)
        elif any(word in msg_lower for word in ["prueba", "gratis", "probar", "semana"]):
            return self._trial_response(academy)
        else:
            return self._default_response(academy)
    
    def _greeting_response(self, academy, lead):
        """Respuesta de saludo con voseo"""
        name = lead.name if lead.name and lead.name != "WhatsApp User" else ""
        greeting = f"¡Hola {name}!" if name else "¡Hola!"
        return (
            f"{greeting} Bienvenido a {academy.name} 🥋\n\n"
            f"Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?\n\n"
            f"• 📅 Horarios de clases\n"
            f"• 💰 Precios y planes\n"
            f"• 🎁 Semana de prueba GRATIS\n"
            f"• 📍 Ubicación\n"
            f"• 🥋 Info para principiantes"
        )
    
    def _pricing_response(self, academy):
        """Respuesta de precios actualizada"""
        try:
            from app.config.academy_info import get_precios_texto
            return get_precios_texto() + "\n\n¿Te gustaría agendar tu SEMANA de prueba GRATIS?"
        except ImportError:
            return (
                f"💰 **PRECIOS - {academy.name}**\n\n"
                f"ADULTOS:\n"
                f"• Jiu-Jitsu: ₡33,000/mes\n"
                f"• Striking: ₡25,000/mes\n"
                f"• Paquete combinado: ₡43,000/mes\n\n"
                f"NIÑOS:\n"
                f"• Kids o Juniors: ₡30,000/mes\n\n"
                f"🎁 ¡SEMANA DE PRUEBA GRATIS!\n\n"
                f"¿Te gustaría agendar?"
            )
    
    def _schedule_response(self, academy):
        """Respuesta de horarios actualizada"""
        try:
            from app.config.academy_info import get_horarios_texto
            return get_horarios_texto() + "\n\n¿Querés probar una SEMANA GRATIS?"
        except ImportError:
            return (
                f"📅 **HORARIOS - {academy.name}**\n\n"
                f"ADULTOS:\n"
                f"• Jiu-Jitsu: Lunes a Viernes, 6:00 p.m.\n"
                f"• Striking: Martes y Jueves, 7:30 p.m.\n\n"
                f"NIÑOS Y ADOLESCENTES:\n"
                f"• Kids (4-10 años): Martes y Jueves, 5:00 p.m.\n"
                f"• Juniors (11-16 años): Lunes y Miércoles, 5:00 p.m.\n\n"
                f"¿Cuál horario te conviene?"
            )
    
    def _location_response(self, academy):
        """Respuesta de ubicación con voseo"""
        return (
            f"📍 **UBICACIÓN**\n\n"
            f"Santo Domingo de Heredia, Costa Rica\n"
            f"🗺️ Waze: https://waze.com/ul/hd1u0y3qpc\n\n"
            f"📞 {academy.phone}\n\n"
            f"¿Necesitás ayuda para llegar?"
        )
    
    def _trial_response(self, academy):
        """Respuesta de semana de prueba con voseo"""
        return (
            f"🎉 ¡Excelente decisión!\n\n"
            f"Tu primera SEMANA es completamente GRATIS en {academy.name}.\n\n"
            f"Por favor compartíme:\n"
            f"1. Tu nombre completo\n"
            f"2. ¿Qué clase te interesa? (Jiu-Jitsu o Striking)\n"
            f"3. ¿Sos adulto o es para niños/adolescentes?\n\n"
            f"¡Te esperamos! 🥋"
        )
    
    def _default_response(self, academy):
        """Respuesta por defecto con voseo"""
        return (
            f"Gracias por contactar a {academy.name}! 🥋\n\n"
            f"¿Cómo puedo ayudarte?\n\n"
            f"• Escribí 'horarios' para ver las clases\n"
            f"• Escribí 'precios' para ver costos\n"
            f"• Escribí 'prueba' para SEMANA gratis\n"
            f"• Escribí 'ubicación' para la dirección"
        )
    
    def _get_error_response(self, academy):
        """Respuesta de error con voseo"""
        return (
            f"Disculpá, tuve un problema procesando tu mensaje.\n\n"
            f"Por favor llamános al {academy.phone} o intentá de nuevo.\n\n"
            f"También podés escribir:\n"
            f"• 'horarios'\n"
            f"• 'precios'\n"
            f"• 'semana de prueba'"
        )