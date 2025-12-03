"""
Message Processor - Orquestador del Procesamiento de Mensajes
Responsabilidad única: Coordinar el flujo de procesamiento de mensajes
Refactored with Repository Pattern: 25/11/2025
"""

import logging
from typing import Optional
from app.models import MessageDirection
from app.services.lead_manager import LeadManager
from app.services.conversation_manager import ConversationManager
from app.services.intent_detector import IntentDetector
from app.services.ai_service import AIService
from app.repositories.lead_repository import LeadRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.academy_repository import AcademyRepository

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Orquestador del procesamiento de mensajes

    Responsabilidad:
    - Coordinar el flujo de procesamiento
    - Delegar tareas a servicios especializados
    - NO tiene lógica de negocio compleja
    - Solo orquesta llamadas a otros servicios
    """

    def __init__(self):
        """Inicializar servicios y repositorios"""
        self.lead_manager = LeadManager()
        self.conversation_manager = ConversationManager()
        self.intent_detector = IntentDetector()
        self.ai_service = AIService()

        # Inicializar repositorios
        self.lead_repo = LeadRepository()
        self.conversation_repo = ConversationRepository()
        self.academy_repo = AcademyRepository()

        # Inicializar scheduler si está disponible
        try:
            from app.services.appointment_scheduler import AppointmentScheduler
            self.scheduler = AppointmentScheduler()
            logger.info("✅ AppointmentScheduler inicializado")
        except Exception as e:
            logger.warning(f"⚠️ AppointmentScheduler no disponible: {e}")
            self.scheduler = None

        logger.info("✅ MessageProcessor inicializado con todos los servicios")

    def process_message(
        self,
        phone_number: str,
        message: str,
        name: Optional[str] = None
    ) -> str:
        """
        Procesar mensaje completo

        Este método orquesta todo el flujo de procesamiento:
        1. Gestionar lead
        2. Gestionar conversación
        3. Guardar mensaje entrante
        4. Detectar nombre en mensaje
        5. Generar respuesta con OpenAI
        6. Detectar intención de agendamiento
        7. Guardar respuesta
        8. Actualizar status del lead

        Args:
            phone_number: Número de teléfono del usuario
            message: Mensaje del usuario
            name: Nombre del perfil de WhatsApp (opcional)

        Returns:
            Respuesta generada por OpenAI
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"[PROCESS] Nuevo mensaje de {phone_number}")
        logger.info(f"[PROCESS] Contenido: {message}")
        logger.info(f"[PROCESS] Nombre del perfil: {name}")
        logger.info(f"{'='*60}")

        try:
            # 1. Gestionar lead
            lead_id = self.lead_manager.get_or_create(phone_number, name)

            # 2. Detectar si el usuario proporcionó su nombre en el mensaje
            detected_name = self.intent_detector.detect_name(message)
            if detected_name:
                logger.info(f"[NAME_DETECTION] Nombre detectado en mensaje: {detected_name}")
                self.lead_manager.update_name(lead_id, detected_name)

            # 3. Gestionar conversación
            conversation_id = self.conversation_manager.get_or_create(lead_id)

            # 4. Guardar mensaje del usuario
            self.conversation_manager.save_message(
                conversation_id,
                MessageDirection.INBOUND,
                message
            )

            # 5. Generar respuesta con OpenAI
            response = self._generate_ai_response(message, lead_id, conversation_id)

            # 6. Guardar respuesta del bot
            self.conversation_manager.save_message(
                conversation_id,
                MessageDirection.OUTBOUND,
                response
            )

            # 7. Actualizar status del lead
            self.lead_manager.update_status(lead_id, message)

            logger.info(f"[PROCESS] Respuesta generada: {response[:100]}...")
            logger.info(f"{'='*60}\n")

            return response

        except Exception as e:
            logger.error(f"[ERROR] Error procesando mensaje: {e}", exc_info=True)
            return self._get_emergency_response()

    def _generate_ai_response(
        self,
        message: str,
        lead_id: int,
        conversation_id: int
    ) -> str:
        """
        Generar respuesta usando OpenAI + detección de agendamiento

        Args:
            message: Mensaje del usuario
            lead_id: ID del lead
            conversation_id: ID de la conversación

        Returns:
            Respuesta de OpenAI (posiblemente con info de agendamiento)
        """
        # Obtener objetos de base de datos usando repositorios
        lead = self.lead_repo.get_by_id(lead_id)
        conversation = self.conversation_repo.get_by_id(conversation_id)
        academy = self.academy_repo.get_first_academy()

        # Obtener historial para detección de intenciones
        history = self.conversation_manager.get_history(conversation_id, limit=5)

        # NUEVO: Detectar consulta de reserva ANTES de generar respuesta del AI
        if self.scheduler and self.intent_detector.detect_booking_query(message):
            logger.info("[BOOKING_QUERY] Detectada consulta de reserva")

            booking_info = self.scheduler.get_lead_booking(lead_id)

            if booking_info['has_booking']:
                logger.info("[BOOKING_QUERY] Lead tiene reserva, mostrando información")
                return booking_info['message']
            else:
                logger.info("[BOOKING_QUERY] Lead NO tiene reserva")
                # Continuar con generación normal del AI para responder apropiadamente
                # El AI puede ofrecer agendar una clase

        # Generar respuesta con OpenAI
        try:
            logger.info("[AI] Generando respuesta con OpenAI")
            ai_response = self.ai_service.generate_response(
                message,
                lead,
                conversation,
                academy,
                use_history=True
            )

            # Detectar intención de agendamiento
            booking_detected = self.intent_detector.detect_booking_intent(
                message,
                ai_response,
                history
            )

            if booking_detected and self.scheduler:
                logger.info("[BOOKING] Intención de agendamiento detectada")

                # NUEVO: Verificar que el AI no haya rechazado la solicitud
                ai_rejected = self._detect_ai_rejection(ai_response)

                if ai_rejected:
                    logger.info("[BOOKING] AI rechazó la solicitud - NO se agenda automáticamente")
                    logger.info(f"[BOOKING] Razón del rechazo detectada en la respuesta del AI")
                    return ai_response  # Retornar solo la respuesta del AI sin intentar agendar

                # NUEVO: Verificar si el AI está pidiendo datos del usuario
                ai_requesting_data = self._detect_ai_requesting_data(ai_response)

                if ai_requesting_data:
                    logger.info("[BOOKING] AI está pidiendo datos - NO se agenda automáticamente todavía")
                    logger.info(f"[BOOKING] Esperando que el usuario proporcione: nombre, teléfono, edad")
                    return ai_response  # Retornar solo la respuesta del AI sin intentar agendar

                # Combinar últimos mensajes del usuario para detectar contexto (ej: "sobrino", "hijo", etc.)
                recent_user_messages = [msg['content'] for msg in history[-5:] if msg.get('sender') == 'user']
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

                # NUEVO: Manejar errores de validación de fecha
                elif 'error_type' in parsed:
                    logger.warning(f"[BOOKING] Validación falló: {parsed['error_type']}")

                    # Construir mensaje de error amigable con fecha sugerida
                    error_msg = parsed['error_message']

                    if parsed.get('suggested_date_formatted'):
                        error_msg += f" ¿Te parece {parsed['suggested_date_formatted']}?"

                    logger.info(f"[BOOKING] Mensaje de validación: {error_msg}")
                    return error_msg

                else:
                    logger.info("[BOOKING] No se pudo parsear fecha/hora")

            return ai_response

        except Exception as e:
            logger.error(f"[ERROR] Error generando respuesta de IA: {e}")
            return self._get_emergency_response()

    def _get_emergency_response(self) -> str:
        """
        Respuesta de emergencia cuando todo falla

        Returns:
            Mensaje de error genérico
        """
        return (
            "Disculpá, estoy teniendo problemas técnicos en este momento. 😅\n\n"
            "Para no hacerte esperar:\n\n"
            "📞 Llamános al: +506-7015-0369\n"
            "💬 O decime tu nombre y número, y te llamamos\n\n"
            "¡Queremos ayudarte a empezar tu SEMANA DE PRUEBA GRATIS! 🥋"
        )

    def _detect_ai_rejection(self, ai_response: str) -> bool:
        """
        Detecta si el AI rechazó la solicitud de agendamiento

        Busca frases clave que indican que el AI está informando al usuario
        que no es posible agendar para la fecha/hora solicitada.

        Args:
            ai_response: Respuesta generada por el AI

        Returns:
            True si el AI rechazó la solicitud, False en caso contrario
        """
        response_lower = ai_response.lower()

        # Frases de rechazo que indican que el AI está diciendo "no"
        rejection_phrases = [
            'lamentablemente',
            'no tenemos',
            'no hay',
            'no es posible',
            'disculpá',
            'ese día no',
            'esa hora no',
            'no podemos',
            'no alcanza',
            'ya no alcanza',
            'no alcanzamos',
            'no está disponible',
            'no disponible',
            'ese horario no',
            'solo tenemos',  # "solo tenemos X días" implica rechazo del día solicitado
            'únicamente',
            'solamente',
        ]

        # Verificar si alguna frase de rechazo está presente
        for phrase in rejection_phrases:
            if phrase in response_lower:
                logger.info(f"[REJECTION] Frase de rechazo detectada: '{phrase}'")
                return True

        return False

    def _detect_ai_requesting_data(self, ai_response: str) -> bool:
        """
        Detectar si el AI esta pidiendo datos del usuario
        (nombre, telefono, edad) para completar la reserva

        Args:
            ai_response: Respuesta generada por el AI

        Returns:
            True si el AI esta pidiendo datos
        """
        ai_lower = ai_response.lower()

        # Frases que indican que el AI esta pidiendo datos
        requesting_phrases = [
            'necesito tu nombre',
            'necesito nombre',
            'para confirmar necesito',
            'para agendar necesito',
            'nombre completo',
            'numero de telefono',
            'tu edad',
            'cuantos anos',
            'que edad',
            'dame tu nombre',
            'decime tu nombre',
            'cual es tu nombre',
            'podrias proporcionar',
            'me podrias dar'
        ]

        is_requesting = any(phrase in ai_lower for phrase in requesting_phrases)

        if is_requesting:
            logger.info(f"[BOOKING] AI esta solicitando datos del usuario - NO agendar todavia")

        return is_requesting

    def get_conversation_stats(self, lead_id: int) -> dict:
        """
        Obtener estadísticas de conversación para un lead

        Args:
            lead_id: ID del lead

        Returns:
            Diccionario con estadísticas
        """
        conversations = self.conversation_manager.get_active_conversations(lead_id)

        total_messages = sum(
            self.conversation_manager.get_message_count(conv.id)
            for conv in conversations
        )

        return {
            'total_conversations': len(conversations),
            'total_messages': total_messages,
            'active_conversations': len([c for c in conversations if c.is_active])
        }

    def close_conversation(self, conversation_id: int) -> bool:
        """
        Cerrar una conversación

        Args:
            conversation_id: ID de la conversación

        Returns:
            True si se cerró exitosamente
        """
        return self.conversation_manager.close_conversation(conversation_id)
