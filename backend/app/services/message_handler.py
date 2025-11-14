"""
Message Handler UNIFICADO con prioridad ABSOLUTA a OpenAI
Actualizado para BJJ Mingo con voseo costarricense
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from app.utils.database import get_db_connection, get_db_cursor

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
    Actualizado para BJJ Mingo
    """
    
    def __init__(self):
        self.db_path = 'bjj_academy.db'
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
        self._save_message(conv_id, 'user', message)
        
        # 4. INTENTAR GENERAR RESPUESTA CON IA
        response = self._generate_ai_response(message, lead_id, conv_id)
        
        # 5. Guardar respuesta del bot
        self._save_message(conv_id, 'assistant', response)
        
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
    
    # ========== MÉTODOS DE BASE DE DATOS ==========
    
    def _get_or_create_lead(self, phone_number, name=None):
        """Obtener o crear lead"""
        with get_db_cursor(db_path=self.db_path) as cursor:
            cursor.execute("SELECT id, name FROM lead WHERE phone_number = ?", (phone_number,))
            lead = cursor.fetchone()

            if not lead:
                cursor.execute("""
                    INSERT INTO lead (academy_id, phone_number, name, source, status, interest_level)
                    VALUES (1, ?, ?, 'whatsapp', 'new', 5)
                """, (phone_number, name or 'WhatsApp User'))
                lead_id = cursor.lastrowid
            else:
                lead_id = lead[0]

        return lead_id
    
    def _get_or_create_conversation(self, lead_id):
        """Obtener o crear conversación"""
        with get_db_cursor(db_path=self.db_path) as cursor:
            cursor.execute("""
                SELECT id FROM conversation
                WHERE lead_id = ? AND status = 'active'
            """, (lead_id,))
            conv = cursor.fetchone()

            if not conv:
                cursor.execute("""
                    INSERT INTO conversation (lead_id, academy_id, status)
                    VALUES (?, 1, 'active')
                """, (lead_id,))
                conv_id = cursor.lastrowid
            else:
                conv_id = conv[0]

        return conv_id
    
    def _save_message(self, conv_id, sender, content, intent=None):
        """Guardar mensaje"""
        with get_db_cursor(db_path=self.db_path) as cursor:
            cursor.execute("""
                INSERT INTO message (conversation_id, sender, content, intent_detected)
                VALUES (?, ?, ?, ?)
            """, (conv_id, sender, content, intent))
    
    def _get_lead_info(self, lead_id):
        """Obtener información del lead"""
        with get_db_connection(db_path=self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, phone_number, name, status, interest_level, source
                FROM lead WHERE id = ?
            """, (lead_id,))

            row = cursor.fetchone()

            if row:
                return {
                    'id': row[0],
                    'phone': row[1],
                    'name': row[2],
                    'status': row[3],
                    'interest_level': row[4],
                    'source': row[5]
                }
        return {}
    
    def _get_academy_info(self):
        """Obtener información de la academia"""
        with get_db_connection(db_path=self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT name, description, instructor_name, instructor_belt,
                       phone, address_street, address_city
                FROM academy WHERE id = 1
            """)

            row = cursor.fetchone()

            if row:
                return {
                    'name': row[0],
                    'description': row[1],
                    'instructor': f"{row[2]} ({row[3]})" if row[2] else 'Instructores certificados',
                    'phone': row[4],
                    'location': f"{row[5]}, {row[6]}" if row[5] and row[6] else 'Santo Domingo de Heredia, Costa Rica'
                }
        return {'name': 'BJJ Mingo', 'phone': '+506-8888-8888'}
    
    def _get_conversation_history(self, conv_id, limit=5):
        """Obtener historial de conversación"""
        with get_db_connection(db_path=self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT sender, content, timestamp
                FROM message
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (conv_id, limit))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'sender': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                })

        # Invertir para orden cronológico
        messages.reverse()
        return messages
    
    def _update_lead_status(self, lead_id, message):
        """Actualizar estado del lead"""
        msg_lower = message.lower()

        with get_db_cursor(db_path=self.db_path) as cursor:
            # Si muestra interés en clase
            if any(word in msg_lower for word in ['agendar', 'clase', 'prueba', 'probar', 'semana']):
                cursor.execute("""
                    UPDATE lead
                    SET status = 'interested', interest_level = 8
                    WHERE id = ? AND status != 'scheduled'
                """, (lead_id,))
            # Si es primera interacción
            else:
                cursor.execute("""
                    UPDATE lead
                    SET status = 'contacted'
                    WHERE id = ? AND status = 'new'
                """, (lead_id,))