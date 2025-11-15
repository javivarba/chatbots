"""
Message Handler UNIFICADO con prioridad ABSOLUTA a OpenAI
Actualizado para BJJ Mingo con voseo costarricense
MIGRADO A SQLALCHEMY + POSTGRESQL
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from app import db
from app.models import Academy, Lead, Conversation, Message, MessageDirection, LeadStatus

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
    """

    def __init__(self):
        self.openai_client = None
        self.ai_enabled = False

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
            self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
            self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', 600))
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
        """
        logger.info(f"\n[PHONE] Mensaje de {phone_number}: {message}")

        # 1. Obtener o crear lead
        lead_id = self._get_or_create_lead(phone_number, name)

        # 2. Obtener o crear conversación
        conv_id = self._get_or_create_conversation(lead_id)

        # 3. Guardar mensaje del usuario
        self._save_message(conv_id, MessageDirection.INBOUND, message)

        # 4. INTENTAR GENERAR RESPUESTA CON IA
        response = self._generate_ai_response(message, lead_id, conv_id)

        # 5. Guardar respuesta del bot
        self._save_message(conv_id, MessageDirection.OUTBOUND, response)

        # 6. Actualizar lead
        self._update_lead_status(lead_id, message)

        return response

    def _generate_ai_response(self, message, lead_id, conv_id):
        """
        Genera respuesta PRIORIZANDO IA + detección de agendamiento
        """

        # PRIORIDAD 1: Intentar con OpenAI
        if self.ai_enabled and self.openai_client:
            try:
                logger.info("[DEBUG] Usando OpenAI para generar respuesta")

                # Obtener información del lead y academia
                lead_info = self._get_lead_info(lead_id)
                academy_info = self._get_academy_info()
                history = self._get_conversation_history(conv_id, limit=5)

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

                # DETECTAR INTENCIÓN DE AGENDAMIENTO
                booking_detected = self._detect_booking_intent(message, ai_response, history)

                if booking_detected and self.scheduler:
                    logger.info("[BOOKING] Intención de agendamiento detectada")

                    # Intentar parsear la fecha/hora del mensaje
                    parsed = self.scheduler.parse_appointment_request(message, lead_id)

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

    def _detect_booking_intent(self, user_message, ai_response, history):
        """
        Detecta si el usuario está intentando agendar una clase
        """
        msg_lower = user_message.lower()

        # Palabras clave de agendamiento
        booking_keywords = ['agendar', 'reservar', 'apartar', 'quiero clase', 'mi nombre es',
                           'quiero una clase', 'clase el', 'clase para', 'semana de prueba']
        has_booking_keyword = any(word in msg_lower for word in booking_keywords)

        # Verificar si tiene día de la semana
        days = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes',
                'sábado', 'sabado', 'mañana', 'hoy']
        has_day = any(day in msg_lower for day in days)

        # Verificar si tiene hora
        import re
        has_time = bool(re.search(r'\d{1,2}:?\d{0,2}\s?(am|pm|hrs)?', msg_lower))

        # Verificar si respondió con nombre (formato: "Nombre Apellido")
        name_pattern = bool(re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+', user_message))

        # Verificar en historial si ya se estaba hablando de agendamiento
        discussing_booking = False
        if history:
            for msg in history[-5:]:
                content_lower = msg['content'].lower()
                if any(word in content_lower for word in ['agendar', 'reservar', 'semana de prueba',
                                                           'horario', 'clase para']):
                    discussing_booking = True
                    break

        # Lógica de detección
        if has_booking_keyword and has_day and has_time:
            return True
        elif has_day and has_time and discussing_booking:
            return True
        elif name_pattern and has_day and has_time:
            return True
        elif name_pattern and discussing_booking:
            return True

        return False

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

    # ========== MÉTODOS DE BASE DE DATOS (SQLAlchemy) ==========

    def _get_or_create_lead(self, phone_number, name=None):
        """Obtener o crear lead usando SQLAlchemy"""
        # Normalizar teléfono
        import re
        normalized_phone = re.sub(r'[^\d+]', '', phone_number)

        lead = Lead.query.filter_by(phone=normalized_phone).first()

        if not lead:
            # Obtener primera academy
            academy = Academy.query.first()
            if not academy:
                raise Exception("No hay academy configurada en la base de datos")

            lead = Lead(
                academy_id=academy.id,
                phone=normalized_phone,
                name=name or 'WhatsApp User',
                source='whatsapp',
                status=LeadStatus.NEW,
                lead_score=5,
                created_at=datetime.now()
            )
            db.session.add(lead)
            db.session.commit()

        return lead.id

    def _get_or_create_conversation(self, lead_id):
        """Obtener o crear conversación usando SQLAlchemy"""
        conversation = Conversation.query.filter_by(
            lead_id=lead_id,
            is_active=True
        ).first()

        if not conversation:
            lead = Lead.query.get(lead_id)

            conversation = Conversation(
                lead_id=lead_id,
                academy_id=lead.academy_id,
                platform='whatsapp',
                is_active=True,
                message_count=0,
                inbound_count=0,
                outbound_count=0,
                started_at=datetime.now(),
                last_message_at=datetime.now()
            )
            db.session.add(conversation)
            db.session.commit()

        return conversation.id

    def _save_message(self, conv_id, direction, content, intent=None):
        """Guardar mensaje usando SQLAlchemy"""
        message = Message(
            conversation_id=conv_id,
            direction=direction,
            content=content,
            created_at=datetime.now()
        )
        db.session.add(message)

        # Actualizar conversation
        conversation = Conversation.query.get(conv_id)
        if conversation:
            conversation.message_count += 1
            if direction == MessageDirection.INBOUND:
                conversation.inbound_count += 1
            else:
                conversation.outbound_count += 1
            conversation.last_message_at = datetime.now()

        db.session.commit()

    def _get_lead_info(self, lead_id):
        """Obtener información del lead usando SQLAlchemy"""
        lead = Lead.query.get(lead_id)

        if lead:
            return {
                'id': lead.id,
                'phone': lead.phone,
                'name': lead.name,
                'status': lead.status,
                'interest_level': lead.lead_score or 0,
                'source': lead.source or 'whatsapp'
            }
        return {}

    def _get_academy_info(self):
        """Obtener información de la academia usando SQLAlchemy"""
        academy = Academy.query.first()

        if academy:
            return {
                'name': academy.name,
                'description': academy.description or 'Academia de Brazilian Jiu-Jitsu',
                'instructor': academy.instructor_name or 'Instructores certificados',
                'phone': academy.phone,
                'location': f"{academy.address_street}, {academy.address_city}" if academy.address_street else 'Santo Domingo de Heredia, Costa Rica'
            }
        return {'name': 'BJJ Mingo', 'phone': '+506-8888-8888'}

    def _get_conversation_history(self, conv_id, limit=5):
        """Obtener historial de conversación usando SQLAlchemy"""
        messages = Message.query.filter_by(
            conversation_id=conv_id
        ).order_by(Message.created_at.desc()).limit(limit).all()

        history = []
        for msg in messages:
            history.append({
                'sender': 'user' if msg.direction == MessageDirection.INBOUND else 'assistant',
                'content': msg.content,
                'timestamp': msg.created_at.isoformat() if msg.created_at else None
            })

        # Invertir para orden cronológico
        history.reverse()
        return history

    def _update_lead_status(self, lead_id, message):
        """Actualizar estado del lead usando SQLAlchemy"""
        msg_lower = message.lower()
        lead = Lead.query.get(lead_id)

        if not lead:
            return

        # Si muestra interés en clase
        if any(word in msg_lower for word in ['agendar', 'clase', 'prueba', 'probar', 'semana']):
            if lead.status != LeadStatus.SCHEDULED:
                lead.status = LeadStatus.INTERESTED
                lead.lead_score = 8
                lead.last_contact_date = datetime.now()
                db.session.commit()
        # Si es primera interacción
        elif lead.status == LeadStatus.NEW:
            lead.status = 'contacted'
            lead.last_contact_date = datetime.now()
            db.session.commit()
