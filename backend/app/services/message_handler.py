"""
⚠️ DEPRECATED - USE MessageProcessor INSTEAD ⚠️

Este archivo está DEPRECATED y se mantiene solo por compatibilidad con tests antiguos.

NUEVA IMPLEMENTACIÓN: app/services/message_processor.py

MessageProcessor es el nuevo orquestador que:
- Usa la misma arquitectura (LeadManager, ConversationManager, IntentDetector, AIService)
- Tiene mejor separación de responsabilidades
- Es más fácil de mantener y testear
- Incluye todos los fixes más recientes

MIGRACIÓN COMPLETADA: 24/11/2025
- app/__init__.py ahora usa MessageProcessor
- Todos los nuevos desarrollos deben usar MessageProcessor

Este archivo se mantendrá hasta que todos los tests se migren.
"""

import warnings
warnings.warn(
    "MessageHandler está deprecated. Usar MessageProcessor en su lugar.",
    DeprecationWarning,
    stacklevel=2
)

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from app import db
from app.models import Academy, Lead, Conversation, Message, MessageDirection, LeadStatus
from app.services.cache_service import cache

# Importar clases especializadas
from app.services.lead_manager import LeadManager
from app.services.conversation_manager import ConversationManager
from app.services.intent_detector import IntentDetector

# Cargar variables de entorno
load_dotenv(override=True)

# Importar OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI no instalado")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageHandler:
    """
    Handler unificado que PRIORIZA OpenAI sobre todo
    Actualizado para BJJ Mingo - PostgreSQL + SQLAlchemy
    REFACTORIZADO: Usa clases especializadas para cada responsabilidad
    """

    def __init__(self):
        self.openai_client = None
        self.ai_enabled = False

        # Inicializar clases especializadas (inyección de dependencias)
        self.lead_manager = LeadManager()
        self.conversation_manager = ConversationManager()
        self.intent_detector = IntentDetector()
        logger.info("✅ Managers especializados inicializados (LeadManager, ConversationManager, IntentDetector)")

        # Intentar inicializar OpenAI
        self._initialize_openai()

        # Importar AppointmentScheduler
        try:
            from app.services.appointment_scheduler import AppointmentScheduler
            self.scheduler = AppointmentScheduler()
            logger.info("✅ AppointmentScheduler inicializado")
        except Exception as e:
            logger.warning(f"⚠️ AppointmentScheduler no disponible: {e}")
            self.scheduler = None

    def _initialize_openai(self):
        """Inicializar cliente de OpenAI"""
        api_key = os.getenv('OPENAI_API_KEY')

        logger.info("=" * 50)
        logger.info("INICIALIZANDO MESSAGE HANDLER")
        logger.info("=" * 50)
        logger.info(f"OpenAI disponible: {OPENAI_AVAILABLE}")
        logger.info(f"API Key presente: {'Sí' if api_key else 'No'}")
        logger.info(f"API Key válida: {'Sí' if api_key and api_key.startswith('sk-') else 'No'}")

        if not OPENAI_AVAILABLE:
            logger.error("❌ OpenAI library no instalada")
            self.ai_enabled = False
            return

        if not api_key or not api_key.startswith('sk-'):
            logger.error("❌ OpenAI API Key no configurada correctamente")
            self.ai_enabled = False
            return

        try:
            self.openai_client = OpenAI(api_key=api_key)
            # Modelo: gpt-4o-mini (recomendado) - mejor calidad, más barato, soporte a largo plazo
            # Alternativas: gpt-4o (máxima calidad), gpt-3.5-turbo (legacy, no recomendado)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            # Max tokens incrementado para aprovechar capacidad de gpt-4o-mini (soporta hasta 16,384)
            self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', 1000))
            self.temperature = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
            self.ai_enabled = True

            logger.info("✅ OpenAI configurado exitosamente")
            logger.info(f"   Modelo: {self.model}")
            logger.info(f"   Max tokens: {self.max_tokens}")
            logger.info(f"   Temperature: {self.temperature}")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"❌ Error inicializando OpenAI: {e}")
            self.ai_enabled = False

    def process_message(self, phone_number, message, name=None):
        """
        Procesar mensaje - SIEMPRE intenta IA primero
        REFACTORIZADO: Usa managers especializados
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"[PROCESS] Nuevo mensaje de {phone_number}")
        logger.info(f"[PROCESS] Contenido: {message}")
        logger.info(f"[PROCESS] Nombre del perfil: {name}")
        logger.info(f"{'='*60}")

        # 1. Obtener o crear lead (usando LeadManager)
        lead_id = self.lead_manager.get_or_create(phone_number, name)

        # 2. Detectar si el usuario proporcionó su nombre en el mensaje (usando IntentDetector)
        detected_name = self.intent_detector.detect_name(message)
        if detected_name:
            logger.info(f"[NAME_DETECTION] Nombre detectado en mensaje: {detected_name}")
            self.lead_manager.update_name(lead_id, detected_name)

        # 3. Obtener o crear conversación (usando ConversationManager)
        conv_id = self.conversation_manager.get_or_create(lead_id)

        # 4. Guardar mensaje del usuario (usando ConversationManager)
        self.conversation_manager.save_message(conv_id, MessageDirection.INBOUND, message)

        # 5. INTENTAR GENERAR RESPUESTA CON IA
        response = self._generate_ai_response(message, lead_id, conv_id)

        # 6. Guardar respuesta del bot (usando ConversationManager)
        self.conversation_manager.save_message(conv_id, MessageDirection.OUTBOUND, response)

        # 7. Actualizar lead (usando LeadManager)
        self.lead_manager.update_status(lead_id, message)

        logger.info(f"[PROCESS] Respuesta generada: {response[:100]}...")
        logger.info(f"{'='*60}\n")

        return response

    def _generate_ai_response(self, message, lead_id, conv_id):
        """
        Genera respuesta PRIORIZANDO IA + detección de agendamiento
        REFACTORIZADO: Usa managers especializados
        """

        # PRIORIDAD 1: Intentar con OpenAI
        if self.ai_enabled and self.openai_client:
            try:
                logger.info("[DEBUG] Usando OpenAI para generar respuesta")

                # Obtener información del lead y academia (usando managers)
                lead_info = self.lead_manager.get_info(lead_id)
                academy_info = self.conversation_manager.get_academy_info()
                history = self.conversation_manager.get_history(conv_id, limit=5)

                logger.info(f"[DEBUG] Lead: {lead_info['name']}, Conv ID: {conv_id}")

                # Construir prompt del sistema
                system_prompt = self._build_system_prompt(academy_info, lead_info)

                # Construir mensajes para OpenAI
                messages = [{"role": "system", "content": system_prompt}]

                # Agregar historial
                for msg in history:
                    role = "user" if msg['sender'] == 'user' else "assistant"
                    messages.append({"role": role, "content": msg['content']})

                # Agregar mensaje actual
                messages.append({"role": "user", "content": message})

                # Llamar a OpenAI
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )

                ai_response = response.choices[0].message.content

                logger.info(f"[SUCCESS] Respuesta generada: {len(ai_response)} caracteres")

                # DETECTAR INTENCIÓN DE AGENDAMIENTO (usando IntentDetector)
                booking_detected = self.intent_detector.detect_booking_intent(message, ai_response, history)

                if booking_detected and self.scheduler:
                    logger.info("[BOOKING] Intención de agendamiento detectada")

                    # Combinar últimos mensajes del usuario para detectar contexto (ej: "sobrino", "hijo", etc.)
                    recent_user_messages = [msg['content'] for msg in history[-5:] if msg['sender'] == 'user']
                    combined_context = ' '.join(recent_user_messages) + ' ' + message

                    logger.info(f"[BOOKING] Contexto combinado para parseo: {combined_context[:100]}...")

                    # Intentar parsear la fecha/hora del mensaje con contexto de conversación
                    parsed = self.scheduler.parse_appointment_request(combined_context, lead_id)

                    if parsed['parsed']:
                        # Crear la semana de prueba
                        result = self.scheduler.book_trial_week(
                            lead_id,
                            parsed.get('clase_tipo', 'adultos_jiujitsu'),
                            f"Agendado via WhatsApp: {message}"
                        )

                        if result['success']:
                            logger.info(f"[BOOKING] Semana de prueba registrada")
                            return ai_response + "\n\n" + result['message']
                        else:
                            logger.warning(f"[BOOKING] Error: {result['message']}")
                            # Si ya tiene una reserva activa, informar al usuario
                            if 'Ya tenés una semana de prueba activa' in result['message']:
                                return "Ya tenés una clase de prueba agendada. Si necesitás modificar tu reserva, por favor avisame."
                            else:
                                # Otro tipo de error
                                return f"Disculpá, hubo un problema al agendar: {result['message']}"
                    else:
                        logger.info("[BOOKING] No se pudo parsear fecha/hora")

                # OpenAI ahora maneja el CTA de forma natural - no agregamos nada automáticamente
                return ai_response

            except Exception as e:
                logger.error(f"[ERROR] Fallo OpenAI: {e}")
                # Continuar al fallback

        # FALLBACK: Solo si OpenAI falló o no está disponible
        logger.warning("[FALLBACK] OpenAI no disponible, usando respuesta de emergencia")
        return self._get_emergency_response(message)

    def _build_system_prompt(self, academy_info, lead_info):
        """Construir prompt del sistema usando academy_info.py"""
        try:
            from app.config.academy_info import get_system_prompt_base
            base_prompt = get_system_prompt_base()
        except ImportError:
            logger.warning("No se pudo importar academy_info, usando prompt por defecto")
            base_prompt = self._get_default_system_prompt(academy_info)

        # Agregar información del prospecto
        lead_context = f"""

CONTEXTO DEL PROSPECTO:
- Nombre: {lead_info.get('name', 'No proporcionado')}
- Teléfono: {lead_info.get('phone')}
- Estado actual: {lead_info.get('status')}
- Fuente: {lead_info.get('source', 'WhatsApp')}
"""

        return base_prompt + lead_context

    def _get_default_system_prompt(self, academy_info):
        """Prompt por defecto si no se puede importar academy_info"""
        return f"""Sos "Mingo Asistente", parte del equipo de BJJ Mingo.

📍 {academy_info.get('location', 'Santo Domingo de Heredia, Costa Rica')}
📞 {academy_info.get('phone', '+506-8888-8888')}

HORARIOS:
- Jiu-Jitsu Adultos: Lunes a Viernes, 6:00 p.m.
- Striking Adultos: Martes y Jueves, 7:30 p.m.
- Kids (4-10 años): Martes y Jueves, 5:00 p.m.
- Juniors (11-16 años): Lunes y Miércoles, 5:00 p.m.

PRECIOS:
- Adultos JJ: ₡33,000/mes
- Adultos Striking: ₡25,000/mes
- Combo: ₡43,000/mes
- Niños: ₡30,000/mes

🎁 SEMANA DE PRUEBA GRATIS

INSTRUCCIONES:
1. Usá voseo costarricense (vení, querés, tenés, podés)
2. Sé amigable, empático y humano
3. NO hagás bromas, pero sé simpático
4. Recolectá datos paso a paso
5. Siempre ofrecé fecha específica
6. Mencioná que la semana de prueba es GRATIS
"""

    def _get_emergency_response(self, message):
        """Respuesta de emergencia cuando OpenAI no funciona"""
        return (
            "Disculpá, estoy teniendo problemas técnicos en este momento. 😅\n\n"
            "Para no hacerte esperar:\n\n"
            "📞 Llamános al: +506-8888-8888\n"
            "💬 O decime tu nombre y número, y te llamamos\n\n"
            "¡Queremos ayudarte a empezar tu SEMANA DE PRUEBA GRATIS! 🥋"
        )

    # ========== MÉTODOS ELIMINADOS ==========
    # Los siguientes métodos ahora están implementados en clases especializadas:
    # - _detect_name_in_message() -> IntentDetector.detect_name()
    # - _update_lead_name() -> LeadManager.update_name()
    # - _get_or_create_lead() -> LeadManager.get_or_create()
    # - _get_or_create_conversation() -> ConversationManager.get_or_create()
    # - _save_message() -> ConversationManager.save_message()
    # - _get_lead_info() -> LeadManager.get_info()
    # - _get_academy_info() -> ConversationManager.get_academy_info()
    # - _get_conversation_history() -> ConversationManager.get_history()
    # - _update_lead_status() -> LeadManager.update_status()
    # - _detect_booking_intent() -> IntentDetector.detect_booking_intent()
