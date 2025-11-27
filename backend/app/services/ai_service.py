"""
AI Service - Integración con OpenAI GPT
Genera respuestas inteligentes usando el contexto de la academia y la conversación
VERSIÓN ACTUALIZADA para BJJ Mingo con voseo costarricense
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

# IMPORTANTE: Cargar .env ANTES de importar openai
from dotenv import load_dotenv
load_dotenv(override=True)

# Importar OpenAI (versión 1.0+)
from openai import OpenAI

from app.models import Lead, Conversation, Message, Academy
from app.services.cache_service import cache

logger = logging.getLogger(__name__)


class AIService:
    """
    Servicio para generar respuestas usando OpenAI GPT
    Actualizado para BJJ Mingo
    """
    
    def __init__(self):
        """Inicializa el cliente de OpenAI"""
        
        # FORZAR RECARGA DE VARIABLES DE ENTORNO
        load_dotenv(override=True)
        
        api_key = os.getenv('OPENAI_API_KEY')
        
        # Debug logging
        logger.info(f"Inicializando AIService...")
        logger.info(f"API Key presente: {'Sí' if api_key else 'No'}")
        logger.info(f"API Key válida: {'Sí' if api_key and api_key.startswith('sk-') else 'No'}")
        
        if not api_key or api_key == 'sk-your-openai-api-key-here':
            logger.warning("OpenAI API key no configurada correctamente")
            self.enabled = False
            self.client = None
        else:
            try:
                # Usar OpenAI cliente versión 1.0+
                self.client = OpenAI(api_key=api_key)
                self.enabled = True
                self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
                self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', 600))
                self.temperature = float(os.getenv('OPENAI_TEMPERATURE', 0.2))  # Más bajo para precisión
                
                logger.info(f"OpenAI configurado exitosamente:")
                logger.info(f"  - Modelo: {self.model}")
                logger.info(f"  - Max tokens: {self.max_tokens}")
                logger.info(f"  - Temperatura: {self.temperature}")
                
            except Exception as e:
                logger.error(f"Error inicializando OpenAI: {e}")
                self.enabled = False
                self.client = None
    
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
        """

        if not self.enabled or not self.client:
            logger.warning("OpenAI no disponible, usando respuestas predefinidas")
            return self._get_fallback_response(message, academy)

        try:
            # CACHE: Intentar obtener respuesta cacheada para preguntas frecuentes
            # Solo cachear si NO hay historial (preguntas iniciales)
            if not use_history:
                query_context = {
                    "lead_status": lead.status,
                    "has_history": False
                }
                query_hash = cache.generate_query_hash(message, query_context)
                cached_response = cache.get_ai_response(query_hash)

                if cached_response:
                    logger.info(f"[CACHE HIT] Respuesta de IA encontrada en caché")
                    return cached_response

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

            # Llamar a OpenAI (versión 1.0+)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            ai_response = response.choices[0].message.content

            # OpenAI ahora maneja el CTA de forma natural - no agregamos nada automáticamente

            logger.info(f"Respuesta generada exitosamente: {len(ai_response)} caracteres")

            # CACHE: Guardar respuesta en caché si no tiene historial
            if not use_history:
                query_context = {
                    "lead_status": lead.status,
                    "has_history": False
                }
                query_hash = cache.generate_query_hash(message, query_context)
                cache.set_ai_response(query_hash, ai_response)
                logger.info(f"[CACHE SET] Respuesta de IA guardada en caché")

            # Actualizar métricas (opcional)
            self._update_ai_metrics(conversation, response)

            return ai_response
            
        except Exception as e:
            logger.error(f"Error generando respuesta con OpenAI: {e}")
            return self._get_fallback_response(message, academy)
    
    def _build_system_prompt(self, academy: Academy, lead: Lead) -> str:
        """
        Construye el prompt del sistema con información de BJJ Mingo
        """
        # CACHE: Intentar obtener el system prompt base del caché
        base_prompt = cache.get_system_prompt()

        if not base_prompt:
            try:
                # Intentar importar el prompt base desde academy_info
                from app.config.academy_info import get_system_prompt_base
                base_prompt = get_system_prompt_base()

                # Guardar en caché para próximas llamadas
                cache.set_system_prompt(base_prompt)
                logger.info("[CACHE SET] System prompt guardado en caché")

            except ImportError:
                # Fallback si no se puede importar academy_info
                logger.warning("No se pudo importar academy_info, usando prompt por defecto")
                base_prompt = self._get_default_prompt_base(academy)
        else:
            logger.debug("[CACHE HIT] System prompt obtenido del caché")

        # Agregar información del prospecto (esto NO se cachea porque cambia por lead)
        lead_info = f"""

CONTEXTO DEL PROSPECTO:
- Nombre: {lead.name if lead.name != 'WhatsApp User' else 'No proporcionado'}
- Teléfono: {lead.phone}
- Estado: {lead.status}
- Fuente: {lead.source}
"""

        return base_prompt + lead_info
    
    def _get_default_prompt_base(self, academy: Academy) -> str:
        """Prompt base por defecto si academy_info no está disponible"""

        return f"""Sos "Mingo Asistente", un miembro del equipo de BJJ Mingo.

ACADEMIA: BJJ Mingo
📍 Santo Domingo de Heredia, Costa Rica
🗺️ Waze: https://waze.com/ul/hd1u0y3qpc
👥 Instructores: Juan Carlos, Michael, Joaquín, César
📞 {academy.phone}

HORARIOS:
- Jiu-Jitsu Adultos: Lunes a Viernes, 6:00 p.m.
- Striking Adultos: Martes y Jueves, 7:30 p.m.
- Kids (4-10 años): Martes y Jueves, 5:00 p.m.
- Juniors (11-16 años): Lunes y Miércoles, 5:00 p.m.

PRECIOS:
- Adultos Jiu-Jitsu: ₡33,000/mes
- Adultos Striking: ₡25,000/mes
- Paquete combinado: ₡43,000/mes
- Niños: ₡30,000/mes

🎁 SEMANA DE PRUEBA COMPLETAMENTE GRATIS

INSTRUCCIONES:
1. Usá VOSEO costarricense (vení, querés, tenés, podés)
2. Sé amigable, empático y humano
3. NO hagás bromas, pero sé simpático
4. Respondé como parte del equipo, no como bot
5. Para clases de prueba, recolectá datos paso a paso
6. NO cerrés con "vení cuando gustés" - ofrecé fecha específica
7. Mencioná que la SEMANA de prueba es GRATIS
8. Usá los horarios y precios EXACTOS mostrados arriba
"""
    
    def test_connection(self) -> tuple:
        """Test básico de conexión con OpenAI"""
        if not self.enabled or not self.client:
            return False, "OpenAI no habilitado"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hola"}],
                max_tokens=10
            )
            return True, f"Conexión exitosa: {response.choices[0].message.content}"
                
        except Exception as e:
            return False, f"Error: {str(e)}"

    def _get_conversation_history(
        self,
        conversation: Conversation,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Obtiene el historial de conversación para contexto
        """
        history = []

        try:
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
        except Exception as e:
            logger.warning(f"Error obteniendo historial: {e}")

        return history
    
    def _get_fallback_response(self, message: str, academy: Academy) -> str:
        """
        Respuesta de fallback cuando OpenAI no está disponible
        """
        try:
            from app.config.academy_info import get_horarios_texto, get_precios_texto
            horarios_texto = get_horarios_texto()
            precios_texto = get_precios_texto()
        except ImportError:
            horarios_texto = "Lunes a Viernes 6:00 p.m. (Adultos JJ), Martes y Jueves 7:30 p.m. (Striking)"
            precios_texto = "Adultos: ₡33,000/mes, Niños: ₡30,000/mes"
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hola', 'hi', 'buenos']):
            return (
                f"¡Hola! Bienvenido a BJJ Mingo\n\n"
                f"Estoy aquí para ayudarte con información sobre nuestras clases de Jiu-Jitsu y Striking en Santo Domingo de Heredia.\n"
                f"¿En qué puedo ayudarte hoy?"
            )
        elif any(word in message_lower for word in ['precio', 'costo', 'cuanto']):
            return (
                f"{precios_texto}\n\n"
                f"¿Te gustaría agendar tu SEMANA de prueba GRATIS?"
            )
        elif any(word in message_lower for word in ['horario', 'hora', 'cuando']):
            return (
                f"{horarios_texto}\n\n"
                f"¿Querés probar una SEMANA GRATIS?"
            )
        else:
            return (
                f"Gracias por tu mensaje. En BJJ Mingo tenemos:\n"
                f"• Clases de Jiu-Jitsu y Striking\n"
                f"• Programas para niños, adolescentes y adultos\n"
                f"• SEMANA DE PRUEBA GRATIS\n"
                f"• Ambiente familiar y respetuoso\n\n"
                f"¿Qué información específica necesitás?"
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
        positive_words = ['gracias', 'excelente', 'genial', 'bueno', 'perfecto', 'sí', 'dale', 'pura vida']
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