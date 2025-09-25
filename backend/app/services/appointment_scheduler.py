"""
Servicio de Agendamiento de Clases
"""

import sqlite3
from datetime import datetime, timedelta
import re

class AppointmentScheduler:
    def __init__(self):
        self.db_path = 'bjj_academy.db'
        self.days_map = {
            'lunes': 1, 'martes': 2, 'miércoles': 3, 'miercoles': 3,
            'jueves': 4, 'viernes': 5, 'sábado': 6, 'sabado': 6,
            'mañana': -1, 'hoy': 0, 'pasado mañana': -2
        }
        self.time_map = {
            '7am': '07:00', '7': '07:00', 'mañana temprano': '07:00',
            '12pm': '12:00', '12': '12:00', 'mediodía': '12:00', 'mediodia': '12:00',
            '6pm': '18:00', '6': '18:00', '18': '18:00', 'tarde': '18:00',
            '8pm': '20:00', '8': '20:00', '20': '20:00', 'noche': '20:00',
            '9am': '09:00', '9': '09:00',
            '11am': '11:00', '11': '11:00'
        }
    
    def get_available_slots(self, days_ahead=7):
        """Obtener slots disponibles para los próximos días"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        available = []
        today = datetime.now()
        
        for i in range(1, days_ahead + 1):
            date = today + timedelta(days=i)
            day_of_week = date.weekday() + 1  # Python: 0=Lun, SQL: 1=Lun
            
            # Solo Lun-Sab (1-6)
            if day_of_week > 6:
                continue
            
            # Obtener horarios para ese día
            cursor.execute("""
                SELECT time_slot, max_capacity 
                FROM schedule_slots 
                WHERE day_of_week = ? AND is_active = 1
                ORDER BY time_slot
            """, (day_of_week,))
            
            slots = cursor.fetchall()
            
            for time_slot, max_capacity in slots:
                # Contar citas existentes
                datetime_str = f"{date.strftime('%Y-%m-%d')} {time_slot}:00"
                cursor.execute("""
                    SELECT COUNT(*) FROM appointment 
                    WHERE appointment_datetime = ? AND status != 'cancelled'
                """, (datetime_str,))
                
                booked = cursor.fetchone()[0]
                available_spots = max_capacity - booked
                
                if available_spots > 0:
                    day_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 
                               'Viernes', 'Sábado', 'Domingo'][day_of_week - 1]
                    
                    available.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'day': day_name,
                        'time': time_slot,
                        'datetime': datetime_str,
                        'available': available_spots,
                        'display': f"{day_name} {date.strftime('%d/%m')} a las {time_slot}"
                    })
        
        conn.close()
        return available
    
    def parse_appointment_request(self, message, lead_id=None):
        """Interpretar mensaje para extraer fecha y hora"""
        message_lower = message.lower()
        
        # Buscar día
        target_date = None
        target_time = None
        
        # Verificar "mañana", "hoy", etc
        for key, value in self.days_map.items():
            if key in message_lower:
                if value < 0:  # mañana, pasado mañana
                    target_date = datetime.now() + timedelta(days=abs(value))
                elif value == 0:  # hoy
                    target_date = datetime.now()
                else:  # día de la semana
                    # Calcular próximo día de la semana
                    today = datetime.now()
                    days_ahead = (value - today.weekday() - 1) % 7
                    if days_ahead == 0:
                        days_ahead = 7  # Si es el mismo día, siguiente semana
                    target_date = today + timedelta(days=days_ahead)
                break
        
        # Buscar hora
        for key, value in self.time_map.items():
            if key in message_lower:
                target_time = value
                break
        
        # Si no encontramos hora específica, buscar patrones
        if not target_time:
            # Buscar patrones como "18:00", "6:00"
            time_pattern = re.search(r'(\d{1,2}):?(\d{2})?\s?(am|pm)?', message_lower)
            if time_pattern:
                hour = int(time_pattern.group(1))
                minutes = time_pattern.group(2) or '00'
                ampm = time_pattern.group(3)
                
                if ampm == 'pm' and hour < 12:
                    hour += 12
                
                target_time = f"{hour:02d}:{minutes}"
        
        if target_date and target_time:
            return {
                'date': target_date.strftime('%Y-%m-%d'),
                'time': target_time,
                'datetime': f"{target_date.strftime('%Y-%m-%d')} {target_time}:00",
                'parsed': True
            }
        
        return {'parsed': False, 'date': None, 'time': None}
    
    def book_appointment(self, lead_id, appointment_datetime, notes=None):
        """Reservar una cita"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si el lead ya tiene una cita
        cursor.execute("""
            SELECT COUNT(*) FROM appointment 
            WHERE lead_id = ? AND status = 'scheduled'
        """, (lead_id,))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return {
                'success': False,
                'message': 'Ya tienes una clase agendada. Por favor cancela la anterior primero.'
            }
        
        # Parsear fecha y hora
        dt = datetime.strptime(appointment_datetime, '%Y-%m-%d %H:%M:%S')
        
        # Verificar que no sea en el pasado
        if dt < datetime.now():
            conn.close()
            return {
                'success': False,
                'message': 'No puedes agendar clases en el pasado.'
            }
        
        # Verificar disponibilidad
        day_of_week = dt.weekday() + 1
        time_slot = dt.strftime('%H:%M')
        
        cursor.execute("""
            SELECT max_capacity FROM schedule_slots 
            WHERE day_of_week = ? AND time_slot = ?
        """, (day_of_week, time_slot))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return {
                'success': False,
                'message': 'Ese horario no está disponible.'
            }
        
        max_capacity = result[0]
        
        # Contar reservas existentes
        cursor.execute("""
            SELECT COUNT(*) FROM appointment 
            WHERE appointment_datetime = ? AND status != 'cancelled'
        """, (appointment_datetime,))
        
        current_bookings = cursor.fetchone()[0]
        
        if current_bookings >= max_capacity:
            conn.close()
            return {
                'success': False,
                'message': 'Lo siento, esa clase está llena. Por favor elige otro horario.'
            }
        
        # Crear la cita
        try:
            cursor.execute("""
                INSERT INTO appointment 
                (lead_id, appointment_date, appointment_time, appointment_datetime, 
                 status, class_type, confirmed, notes)
                VALUES (?, ?, ?, ?, 'scheduled', 'trial', 1, ?)
            """, (lead_id, dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M:%S'), 
                  appointment_datetime, notes))
            
            # Actualizar status del lead
            cursor.execute("""
                UPDATE lead SET status = 'scheduled', interest_level = 9 
                WHERE id = ?
            """, (lead_id,))
            
            conn.commit()
            
            # Generar link de Google Calendar
            calendar_link = self.generate_calendar_link(dt)
            
            conn.close()
            
            return {
                'success': True,
                'message': f"✅ ¡Clase confirmada para {dt.strftime('%A %d/%m a las %H:%M')}!",
                'appointment_id': cursor.lastrowid,
                'calendar_link': calendar_link,
                'datetime': appointment_datetime
            }
            
        except sqlite3.IntegrityError:
            conn.close()
            return {
                'success': False,
                'message': 'Ya tienes una cita agendada para ese horario.'
            }
        except Exception as e:
            conn.close()
            return {
                'success': False,
                'message': f'Error al agendar: {str(e)}'
            }
    
    def generate_calendar_link(self, dt):
        """Generar link para agregar a Google Calendar"""
        # Formato: YYYYMMDDTHHmmss
        start = dt.strftime('%Y%m%dT%H%M%S')
        end = (dt + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')
        
        title = "Clase de Prueba - BJJ Academy"
        details = "Tu primera clase de Brazilian Jiu-Jitsu. ¡No olvides traer ropa cómoda y agua!"
        location = "BJJ Academy, 123 Main St"
        
        # Crear URL de Google Calendar
        base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
        url = f"{base_url}&text={title}&dates={start}/{end}&details={details}&location={location}"
        
        # Reemplazar espacios y caracteres especiales
        url = url.replace(' ', '%20').replace('¡', '%C2%A1').replace('!', '%21')
        
        return url
    
    def format_available_slots_message(self, slots):
        """Formatear mensaje con slots disponibles"""
        if not slots:
            return "Lo siento, no hay horarios disponibles en los próximos días."
        
        message = "📅 Horarios disponibles para tu clase de prueba:\n\n"
        
        current_date = None
        for slot in slots[:10]:  # Máximo 10 opciones
            if slot['date'] != current_date:
                current_date = slot['date']
                message += f"\n**{slot['day']} {datetime.strptime(slot['date'], '%Y-%m-%d').strftime('%d/%m')}:**\n"
            
            message += f"  • {slot['time']} ({slot['available']} lugares)\n"
        
        message += "\n💬 Responde con el día y hora que prefieras."
        message += "\nEjemplo: 'Mañana a las 6pm' o 'Lunes 18:00'"
        
        return message
