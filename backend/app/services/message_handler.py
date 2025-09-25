"""
Message Handler con Agendamiento Integrado
"""

import sqlite3
from datetime import datetime, timedelta
import os
from app.services.appointment_scheduler import AppointmentScheduler

class MessageHandler:
    def __init__(self):
        self.db_path = 'bjj_academy.db'
        self.scheduler = AppointmentScheduler()
        self.use_openai = False
        
        # Verificar si hay OpenAI key
        api_key = os.getenv('OPENAI_API_KEY', '')
        if api_key and 'sk-' in api_key and 'AQUI_VA' not in api_key:
            try:
                import openai
                openai.api_key = api_key
                self.use_openai = True
                print("✅ OpenAI habilitado")
            except:
                print("⚠️ OpenAI no disponible, usando respuestas predefinidas")
    
    def get_or_create_lead(self, phone_number, name=None):
        """Obtener o crear un lead"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM lead WHERE phone_number = ?", (phone_number,))
        lead = cursor.fetchone()
        
        if not lead:
            cursor.execute("""
                INSERT INTO lead (academy_id, phone_number, name, source, status, interest_level)
                VALUES (1, ?, ?, 'whatsapp', 'new', 5)
            """, (phone_number, name or 'Usuario WhatsApp'))
            conn.commit()
            lead_id = cursor.lastrowid
        else:
            lead_id = lead[0]
        
        conn.close()
        return lead_id
    
    def get_or_create_conversation(self, lead_id):
        """Obtener o crear conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversation 
            WHERE lead_id = ? AND status = 'active'
        """, (lead_id,))
        conv = cursor.fetchone()
        
        if not conv:
            cursor.execute("""
                INSERT INTO conversation (lead_id, academy_id, status)
                VALUES (?, 1, 'active')
            """, (lead_id,))
            conn.commit()
            conv_id = cursor.lastrowid
        else:
            conv_id = conv[0]
        
        conn.close()
        return conv_id
    
    def save_message(self, conv_id, sender, content, intent=None):
        """Guardar mensaje en BD"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO message (conversation_id, sender, content, intent_detected)
            VALUES (?, ?, ?, ?)
        """, (conv_id, sender, content, intent))
        
        conn.commit()
        conn.close()
    
    def get_conversation_context(self, lead_id):
        """Obtener contexto de la conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si estamos en proceso de agendamiento
        cursor.execute("""
            SELECT m.content, m.sender, m.timestamp
            FROM message m
            JOIN conversation c ON m.conversation_id = c.id
            WHERE c.lead_id = ? 
            ORDER BY m.timestamp DESC
            LIMIT 5
        """, (lead_id,))
        
        recent_messages = cursor.fetchall()
        
        # Verificar si ya tiene una cita
        cursor.execute("""
            SELECT appointment_datetime, status
            FROM appointment
            WHERE lead_id = ? AND status = 'scheduled'
            ORDER BY created_at DESC
            LIMIT 1
        """, (lead_id,))
        
        existing_appointment = cursor.fetchone()
        
        conn.close()
        
        return {
            'recent_messages': recent_messages,
            'has_appointment': existing_appointment is not None,
            'appointment': existing_appointment
        }
    
    def get_response(self, message, lead_id):
        """Generar respuesta con manejo de agendamiento"""
        
        msg_lower = message.lower()
        context = self.get_conversation_context(lead_id)
        
        # Si ya tiene cita agendada
        if context['has_appointment']:
            dt_str = context['appointment'][0]
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            
            if 'cancelar' in msg_lower or 'cambiar' in msg_lower:
                # Cancelar cita existente
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE appointment 
                    SET status = 'cancelled' 
                    WHERE lead_id = ? AND status = 'scheduled'
                """, (lead_id,))
                conn.commit()
                conn.close()
                
                return "✅ Tu cita ha sido cancelada. ¿Te gustaría agendar otra?", 'cancelar_cita'
            else:
                return f"Ya tienes una clase agendada para {dt.strftime('%A %d/%m a las %H:%M')}. \n\nSi necesitas cambiarla, escribe 'cancelar' primero.", 'recordatorio_cita'
        
        # Detectar intención de agendar
        agendar_keywords = ['agendar', 'clase', 'prueba', 'probar', 'reservar', 'apartar', 'horario']
        wants_to_schedule = any(word in msg_lower for word in agendar_keywords)
        
        # Verificar si el mensaje anterior fue sobre horarios disponibles
        showing_slots = False
        if context['recent_messages']:
            for msg in context['recent_messages']:
                if msg[1] == 'bot' and 'Horarios disponibles' in msg[0]:
                    showing_slots = True
                    break
        
        # Si quiere agendar o pregunta por horarios
        if wants_to_schedule and not showing_slots:
            # Mostrar horarios disponibles
            slots = self.scheduler.get_available_slots(days_ahead=5)
            response = self.scheduler.format_available_slots_message(slots)
            return response, 'mostrar_horarios'
        
        # Si ya mostramos horarios, intentar parsear la respuesta
        elif showing_slots:
            # Intentar interpretar el mensaje como fecha/hora
            parsed = self.scheduler.parse_appointment_request(message, lead_id)
            
            if parsed['parsed']:
                # Intentar agendar
                result = self.scheduler.book_appointment(
                    lead_id, 
                    parsed['datetime'],
                    f"Agendado via WhatsApp: {message}"
                )
                
                if result['success']:
                    response = result['message']
                    if result['calendar_link']:
                        response += f"\n\n📱 Agregar a Google Calendar:\n{result['calendar_link']}"
                    response += "\n\n📍 Dirección: BJJ Academy, 123 Main St"
                    response += "\n💡 Recuerda traer ropa cómoda y agua"
                    
                    return response, 'cita_confirmada'
                else:
                    return result['message'], 'error_agendamiento'
            else:
                # No se pudo interpretar
                return "No entendí la fecha/hora. Por favor responde con algo como:\n• 'Mañana a las 6pm'\n• 'Lunes 18:00'\n• 'Sábado 9am'", 'fecha_no_clara'
        
        # Si OpenAI está disponible
        if self.use_openai:
            try:
                import openai
                
                # Agregar contexto de agendamiento al prompt
                prompt = f"""Eres un asistente de BJJ Academy. Responde en español de forma amigable y breve.
                
                Mensaje del usuario: {message}
                
                Información de la academia:
                - Clases de Brazilian Jiu-Jitsu para todos los niveles
                - Precio mensual: $50
                - Primera clase gratis
                - Horarios: Lun-Vie 7am, 12pm, 6pm, 8pm. Sábados 9am, 11am
                
                Si el usuario quiere agendar una clase, responde que puede escribir 'quiero agendar una clase'.
                
                Responde de forma natural y útil."""
                
                response = openai.Completion.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=prompt,
                    max_tokens=150,
                    temperature=0.7
                )
                
                return response.choices[0].text.strip(), 'openai_response'
                
            except Exception as e:
                print(f"Error OpenAI: {e}")
        
        # Respuestas predefinidas estándar
        intent = None
        
        if any(word in msg_lower for word in ['hola', 'hi', 'buenas', 'buen']):
            intent = 'saludo'
            response = "¡Hola! 👋 Bienvenido a BJJ Academy. ¿Te interesa conocer sobre nuestras clases de Jiu-Jitsu?"
        elif any(word in msg_lower for word in ['precio', 'costo', 'cuanto', 'pagar']):
            intent = 'precio'
            response = "💰 Nuestras membresías:\n• Mensual: $50\n• Primera clase GRATIS\n\n¿Te gustaría agendar tu clase de prueba? Escribe 'quiero agendar una clase'"
        elif any(word in msg_lower for word in ['info', 'información', 'informacion', 'saber']):
            intent = 'informacion'
            response = "📋 En BJJ Academy ofrecemos:\n• Clases para todos los niveles\n• Instructores certificados\n• Primera clase gratis\n• Ambiente familiar\n\n¿Quieres agendar una clase de prueba?"
        else:
            intent = 'default'
            response = "Gracias por tu mensaje. ¿En qué puedo ayudarte?\n\n• Escribe 'precios' para información de costos\n• Escribe 'quiero agendar' para reservar tu clase gratis\n• Escribe 'info' para conocer más sobre nosotros"
        
        return response, intent
    
    def process_message(self, phone_number, message, name=None):
        """Procesar mensaje completo con agendamiento"""
        
        # 1. Obtener o crear lead
        lead_id = self.get_or_create_lead(phone_number, name)
        
        # 2. Obtener o crear conversación
        conv_id = self.get_or_create_conversation(lead_id)
        
        # 3. Guardar mensaje del usuario
        self.save_message(conv_id, 'user', message)
        
        # 4. Generar respuesta con lógica de agendamiento
        response, intent = self.get_response(message, lead_id)
        
        # 5. Guardar respuesta del bot
        self.save_message(conv_id, 'bot', response, intent)
        
        # 6. Actualizar lead según la intención
        if intent in ['mostrar_horarios', 'cita_confirmada']:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if intent == 'mostrar_horarios':
                cursor.execute("""
                    UPDATE lead 
                    SET status = 'interested', interest_level = 8 
                    WHERE id = ?
                """, (lead_id,))
            elif intent == 'cita_confirmada':
                cursor.execute("""
                    UPDATE lead 
                    SET status = 'scheduled', interest_level = 10 
                    WHERE id = ?
                """, (lead_id,))
            
            conn.commit()
            conn.close()
        
        return response
