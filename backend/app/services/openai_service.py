"""
AI Service - Integración con OpenAI GPT
Genera respuestas inteligentes usando el contexto de la academia y la conversación
"""

import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from datetime import datetime
import logging

from app.models import Lead, Conversation, Message, Academy

logger = logging.getLogger(__name__)


class AIService:
    """
    Servicio para generar respuestas usando OpenAI GPT
    """
    
    def __init__(self):
        """Inicializa el cliente de OpenAI"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'sk-your-openai-api-key-here':
            logger.warning("OpenAI API key no configurada correctamente")
            self.client = None
            self.enabled = False
        else:
            try:
                self.client = OpenAI(api_key=api_key)
                self.enabled = True
                self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
                self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', 500))
                self.temperature = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
                logger.info(f"OpenAI configurado con modelo: {self.model}")
            except Exception as e:
                logger.error(f"Error inicializando OpenAI: {e}")
                self.client = None
                self.enabled = False
    
    def generate_response(
        self, 
        message: str, 
        lead: Lead, 
        conversation: Conversation,
        academy: Academy,
        use_history: bool = True
    ) -> str:
        """
        Genera una respuesta usando GPT con el contexto completo
        
        Args:
            message: Mensaje del usuario
            lead: Objeto Lead con info del prospecto
            conversation: Conversación actual
            academy: Academia con su configuración
            use_history: Si incluir historial de conversación
            
        Returns:
            Respuesta generada por GPT o respuesta fallback
        """
        
        if not self.enabled or not self.client:
            logger.warning("OpenAI no disponible, usando respuestas predefinidas")
            return self._get_fallback_response(message, academy)
        
        try:
            # Construir el prompt del sistema
            system_prompt = self._build_system_prompt(academy, lead)
            
            # Construir el historial de mensajes
            messages = [{"role": "system", "content": system_prompt}]
            
            # Agregar historial si está habilitado
            if use_history:
                history = self._get_conversation_history(conversation)
                messages.extend(history)
            
            # Agregar el mensaje actual
            messages.append({"role": "user", "content": message})
            
            logger.info(f"Enviando a OpenAI: {len(messages)} mensajes")
            
            # Llamar a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extraer la respuesta
            ai_response = response.choices[0].message.content
            
            # Verificar si la respuesta sugiere agendar
            if self._should_add_booking_link(ai_response, message):
                ai_response += self._get_booking_cta(academy)
            
            logger.info(f"Respuesta generada: {ai_response[:100]}...")
            
            # Actualizar métricas (opcional)
            self._update_ai_metrics(conversation, response)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generando respuesta con OpenAI: {e}")
            return self._get_fallback_response(message, academy)
    
    def _build_system_prompt(self, academy: Academy, lead: Lead) -> str:
        """
        Construye el prompt del sistema con toda la información de contexto
        """
        # Información del lead
        lead_info = f"""
        Información del prospecto:
        - Nombre: {lead.name if lead.name != 'WhatsApp User' else 'No proporcionado'}
        - Teléfono: {lead.phone}
        - Estado: {lead.status}
        - Fuente: {lead.source}
        """
        
        # Información de la academia
        academy_info = f"""
        Academia: {academy.name}
        Descripción: {academy.description or 'Academia de Brazilian Jiu-Jitsu'}
        Instructor: {academy.instructor_name} ({academy.instructor_belt})
        Teléfono: {academy.phone}
        Dirección: {academy.address_street}, {academy.address_city}
        
        Horarios:
        - Lunes a Viernes: 6am-9am, 12pm-1pm, 5pm-9pm
        - Sábados: 9am-12pm
        
        Precios:
        - Mensualidad Adultos: $120
        - Mensualidad Niños: $80
        - Clase suelta: $25
        - Primera clase: GRATIS
        
        Programas:
        - Principiantes (sin experiencia requerida)
        - Intermedios
        - Avanzados
        - Niños desde 4 años
        """
        
        # Prompt principal
        system_prompt = f"""Eres el asistente virtual de {academy.name}, una academia de Brazilian Jiu-Jitsu en Costa Rica.

{academy_info}

{lead_info}

Tu objetivo es:
1. Responder preguntas sobre la academia de manera amigable y profesional
2. Motivar al prospecto a tomar una clase de prueba GRATIS
3. Recopilar información relevante (nombre, experiencia, disponibilidad)
4. Usar emojis moderadamente para hacer la conversación más amigable
5. Mantener las respuestas concisas pero informativas
6. Si el prospecto muestra interés, siempre ofrecer agendar la clase de prueba

Reglas importantes:
- Sé entusiasta sobre el BJJ pero no agresivo
- Si no sabes algo específico, ofrece que pueden llamar al {academy.phone}
- Siempre menciona que la primera clase es GRATIS cuando sea relevante
- Usa "tú" no "usted" para mantener un tono amigable
- Las respuestas deben ser naturales, como una conversación real
- Si preguntan por algo no relacionado con BJJ, redirige amablemente a información de la academia

Contexto adicional de la academia:
{academy.ai_context or 'Somos la mejor academia de BJJ en la zona, con instructores certificados y un ambiente familiar.'}
"""
        
        return system_prompt
    
    def _get_conversation_history(
        self, 
        conversation: Conversation, 
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Obtiene el historial de conversación para contexto
        """
        history = []
        
        # Obtener últimos mensajes
        recent_messages = Message.query.filter_by(
            conversation_id=conversation.id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # Invertir para orden cronológico
        recent_messages.reverse()
        
        for msg in recent_messages:
            role = "user" if msg.direction == "inbound" else "assistant"
            history.append({
                "role": role,
                "content": msg.content
            })
        
        return history
    
    def _should_add_booking_link(self, response: str, user_message: str) -> bool:
        """
        Determina si debe agregar un link de booking
        """
        booking_keywords = [
            'agendar', 'clase de prueba', 'probar', 'visitar',
            'conocer', 'inscribir', 'horario disponible'
        ]
        
        response_lower = response.lower()
        message_lower = user_message.lower()
        
        return any(keyword in response_lower or keyword in message_lower 
                  for keyword in booking_keywords)
    
    def _get_booking_cta(self, academy: Academy) -> str:
        """
        Obtiene el Call-to-Action para agendar
        """
        return (
            f"\n\n📲 *Para agendar tu clase de prueba GRATIS:*\n"
            f"• Responde con tu nombre completo y el día que prefieres\n"
            f"• O llámanos al {academy.phone}\n"
            f"• También puedes visitar directamente la academia"
        )
    
    def _get_fallback_response(self, message: str, academy: Academy) -> str:
        """
        Respuesta de fallback cuando OpenAI no está disponible
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hola', 'hi', 'buenos']):
            return (
                f"¡Hola! Bienvenido a {academy.name} 🥋\n\n"
                f"Estoy aquí para ayudarte con información sobre nuestras clases de BJJ.\n"
                f"¿En qué puedo ayudarte hoy?"
            )
        elif any(word in message_lower for word in ['precio', 'costo', 'cuanto']):
            return (
                f"💰 Nuestros precios:\n"
                f"• Adultos: $120/mes\n"
                f"• Niños: $80/mes\n"
                f"• Primera clase: ¡GRATIS!\n\n"
                f"¿Te gustaría agendar tu clase de prueba?"
            )
        else:
            return (
                f"Gracias por tu mensaje. En {academy.name} tenemos:\n"
                f"• Clases para todos los niveles\n"
                f"• Primera clase GRATIS\n"
                f"• Horarios flexibles\n\n"
                f"¿Qué información necesitas?"
            )
    
    def _update_ai_metrics(self, conversation: Conversation, response) -> None:
        """
        Actualiza métricas de uso de IA (opcional)
        """
        try:
            if hasattr(response, 'usage'):
                # Actualizar tokens usados
                if hasattr(conversation, 'total_tokens_used'):
                    conversation.total_tokens_used = (
                        (conversation.total_tokens_used or 0) + 
                        response.usage.total_tokens
                    )
                
                # Estimar costo (GPT-3.5-turbo: ~$0.002 per 1K tokens)
                estimated_cost = (response.usage.total_tokens / 1000) * 0.002
                if hasattr(conversation, 'ai_cost'):
                    conversation.ai_cost = (conversation.ai_cost or 0) + estimated_cost
                
                logger.info(f"Tokens usados: {response.usage.total_tokens}, "
                          f"Costo estimado: ${estimated_cost:.4f}")
        except Exception as e:
            logger.warning(f"No se pudieron actualizar métricas: {e}")
    
    def analyze_sentiment(self, message: str) -> float:
        """
        Analiza el sentimiento del mensaje (opcional)
        Returns: Score entre -1 (negativo) y 1 (positivo)
        """
        # Implementación simple basada en palabras clave
        positive_words = ['gracias', 'excelente', 'genial', 'bueno', 'perfecto', 'sí']
        negative_words = ['no', 'mal', 'caro', 'lejos', 'difícil', 'problema']
        
        message_lower = message.lower()
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return 0.5
        elif negative_count > positive_count:
            return -0.5
        else:
            return 0.0