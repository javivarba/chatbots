"""
Appointment Scheduler Simplificado para BJJ Mingo
Versión actualizada con horarios reales y sistema de semana de prueba
Incluye notificaciones automáticas al staff
"""

import sqlite3
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class AppointmentScheduler:
    def __init__(self):
        self.db_path = 'bjj_academy.db'

        # Inicializar servicio de notificaciones
        try:
            from app.services.notification_service import NotificationService
            self.notifier = NotificationService()
            logger.info("✅ NotificationService integrado en AppointmentScheduler")
        except Exception as e:
            logger.warning(f"⚠️ NotificationService no disponible: {e}")
            self.notifier = None
        
        # Horarios REALES de BJJ Mingo
        self.horarios = {
            'adultos_jiujitsu': {
                'dias': [1, 2, 3, 4, 5],  # Lunes a Viernes (1=Lunes)
                'hora': '18:00',  # 6:00 PM
                'nombre': 'Jiu-Jitsu Adultos',
                'descripcion': 'Jiu-Jitsu para adultos'
            },
            'adultos_striking': {
                'dias': [2, 4],  # Martes y Jueves
                'hora': '19:30',  # 7:30 PM
                'nombre': 'Striking Adultos',
                'descripcion': 'Striking para adultos'
            },
            'kids': {
                'dias': [2, 4],  # Martes y Jueves
                'hora': '17:00',  # 5:00 PM
                'nombre': 'Jiu-Jitsu Kids',
                'edad': '4 a 10 años',
                'descripcion': 'Jiu-Jitsu para niños de 4 a 10 años'
            },
            'juniors': {
                'dias': [1, 3],  # Lunes y Miércoles
                'hora': '17:00',  # 5:00 PM
                'nombre': 'Jiu-Jitsu Juniors',
                'edad': '11 a 16 años',
                'descripcion': 'Jiu-Jitsu para adolescentes de 11 a 16 años'
            }
        }
        
        # Mapeo de días en español
        self.dias_nombres = {
            1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
            4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'
        }
    
    def get_available_slots(self, clase_tipo=None, days_ahead=14):
        """
        Obtiene slots disponibles para los próximos días
        clase_tipo: 'adultos_jiujitsu', 'adultos_striking', 'kids', 'juniors', o None para todos
        """
        available = []
        today = datetime.now()
        
        # Si no especifican tipo, mostrar todos
        tipos_a_mostrar = [clase_tipo] if clase_tipo else list(self.horarios.keys())
        
        for i in range(1, days_ahead + 1):
            date = today + timedelta(days=i)
            day_of_week = date.weekday() + 1  # Python: 0=Lun, convertir a 1=Lun
            
            for tipo_key in tipos_a_mostrar:
                horario = self.horarios[tipo_key]
                
                # Verificar si hay clase ese día
                if day_of_week in horario['dias']:
                    datetime_str = f"{date.strftime('%Y-%m-%d')} {horario['hora']}:00"
                    
                    available.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'day': self.dias_nombres[day_of_week],
                        'time': horario['hora'],
                        'datetime': datetime_str,
                        'clase_nombre': horario['nombre'],
                        'clase_tipo': tipo_key,
                        'display': f"{self.dias_nombres[day_of_week]} {date.strftime('%d/%m')} - {horario['nombre']} a las {horario['hora']}"
                    })
        
        return available
    
    def parse_appointment_request(self, message, lead_id=None):
        """Interpretar mensaje para extraer tipo de clase, día y hora"""
        message_lower = message.lower()
        
        # Detectar tipo de clase
        clase_tipo = None
        if 'striking' in message_lower:
            clase_tipo = 'adultos_striking'
        elif any(word in message_lower for word in ['kid', 'niño', 'niña', 'hijo', 'hija', 'chiquito']):
            clase_tipo = 'kids'
        elif any(word in message_lower for word in ['junior', 'adolescente', 'teenager', 'chamaco']):
            clase_tipo = 'juniors'
        elif any(word in message_lower for word in ['adulto', 'jiu', 'jiujitsu', 'bjj']):
            clase_tipo = 'adultos_jiujitsu'
        else:
            # Por defecto, adultos jiu-jitsu
            clase_tipo = 'adultos_jiujitsu'
        
        # Buscar día
        target_date = None
        days_map = {
            'lunes': 1, 'martes': 2, 'miércoles': 3, 'miercoles': 3,
            'jueves': 4, 'viernes': 5, 'sábado': 6, 'sabado': 6,
            'mañana': -1, 'hoy': 0
        }
        
        for key, value in days_map.items():
            if key in message_lower:
                if value < 0:  # mañana
                    target_date = datetime.now() + timedelta(days=abs(value))
                elif value == 0:  # hoy
                    target_date = datetime.now()
                else:  # día de la semana
                    # Calcular próximo día de la semana
                    today = datetime.now()
                    days_ahead = (value - today.weekday() - 1) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    target_date = today + timedelta(days=days_ahead)
                break
        
        # Si no se especificó día, usar el próximo día disponible para esa clase
        if not target_date and clase_tipo:
            target_date = self._get_next_available_day(clase_tipo)
        
        # Si se detectó clase y día, construir datetime
        if clase_tipo and target_date:
            horario = self.horarios[clase_tipo]
            datetime_str = f"{target_date.strftime('%Y-%m-%d')} {horario['hora']}:00"
            
            return {
                'parsed': True,
                'clase_tipo': clase_tipo,
                'date': target_date.strftime('%Y-%m-%d'),
                'time': horario['hora'],
                'datetime': datetime_str,
                'clase_nombre': horario['nombre']
            }
        
        return {'parsed': False}
    
    def _get_next_available_day(self, clase_tipo):
        """Obtiene el próximo día disponible para una clase"""
        horario = self.horarios[clase_tipo]
        today = datetime.now()
        
        for i in range(1, 14):  # Buscar en los próximos 14 días
            date = today + timedelta(days=i)
            day_of_week = date.weekday() + 1
            
            if day_of_week in horario['dias']:
                return date
        
        return None
    
    def book_trial_week(self, lead_id, clase_tipo, notes=None):
        """
        Registra una semana de prueba para un prospecto
        NUEVO: Envía notificación al staff en lugar de link de calendario al cliente
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verificar si ya tiene una semana de prueba activa
        cursor.execute("""
            SELECT COUNT(*) FROM trial_weeks
            WHERE lead_id = ? AND status = 'active'
        """, (lead_id,))

        if cursor.fetchone()[0] > 0:
            conn.close()
            return {
                'success': False,
                'message': 'Ya tenés una semana de prueba activa.'
            }

        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)

        try:
            # Registrar la semana de prueba
            cursor.execute("""
                INSERT INTO trial_weeks
                (lead_id, clase_tipo, start_date, end_date, status, notes)
                VALUES (?, ?, ?, ?, 'active', ?)
            """, (lead_id, clase_tipo, start_date.strftime('%Y-%m-%d'),
                  end_date.strftime('%Y-%m-%d'), notes))

            trial_id = cursor.lastrowid

            # Actualizar status del lead
            cursor.execute("""
                UPDATE leads
                SET status = 'trial_scheduled', lead_score = 9
                WHERE id = ?
            """, (lead_id,))

            conn.commit()

            # Obtener información del lead para la notificación
            cursor.execute("""
                SELECT phone, name FROM leads WHERE id = ?
            """, (lead_id,))
            lead_data = cursor.fetchone()
            conn.close()

            # Preparar información para notificación
            horario = self.horarios[clase_tipo]
            dias_texto = self._get_dias_texto(horario['dias'])
            next_class_date = self._get_next_class_date(clase_tipo)

            # NUEVO: Enviar notificación al staff de la academia
            if self.notifier:
                lead_info = {
                    'name': lead_data[1] if lead_data else 'No proporcionado',
                    'phone': lead_data[0] if lead_data else 'No proporcionado',
                    'status': 'trial_scheduled'
                }

                trial_info = {
                    'clase_nombre': horario['nombre'],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'dias_texto': dias_texto,
                    'hora': horario['hora'],
                    'notes': notes or 'Agendado vía WhatsApp'
                }

                # Enviar notificación
                notification_result = self.notifier.notify_new_trial_booking(lead_info, trial_info)

                if notification_result['success']:
                    logger.info(f"✅ Notificación enviada al staff para lead {lead_id}")
                else:
                    logger.warning(f"⚠️ No se pudo enviar notificación: {notification_result['message']}")

            # Mensaje de confirmación para el cliente (SIN link de calendario)
            confirmation = f"""✅ ¡SEMANA DE PRUEBA CONFIRMADA!

📋 Detalles:
- Clase: {horario['nombre']}
- Días: {dias_texto}
- Hora: {horario['hora']}
- Primera clase: {next_class_date.strftime('%A %d/%m/%Y')}
- Válido hasta: {end_date.strftime('%d/%m/%Y')}

📍 Ubicación: Santo Domingo de Heredia
🗺️ Waze: https://waze.com/ul/hd1u0y3qpc

👕 Qué traer:
- Ropa deportiva cómoda (pantaloneta/lycra, camisa deportiva)
- Sin zapatos
- Agua
- Si tenés gi, podés traerlo

🎯 *La academia te contactará pronto para confirmar tu asistencia.*

📞 Cualquier duda: {self._get_phone()}

¡Te esperamos! 🥋"""

            return {
                'success': True,
                'message': confirmation,
                'trial_id': trial_id
            }

        except Exception as e:
            conn.close()
            logger.error(f"Error registrando semana de prueba: {e}")
            return {
                'success': False,
                'message': f'Error al registrar: {str(e)}'
            }
    
    def _get_dias_texto(self, dias_nums):
        """Convierte lista de números de días a texto"""
        return ', '.join([self.dias_nombres[d] for d in dias_nums])
    
    def _get_phone(self):
        """Obtiene el teléfono de la academia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM academies WHERE id = 1")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else '+506-8888-8888'
    
    def format_available_slots_message(self, slots, clase_tipo=None):
        """Formatear mensaje con slots disponibles"""
        if not slots:
            return "Lo siento, no hay horarios disponibles en los próximos días."
        
        if clase_tipo:
            horario = self.horarios[clase_tipo]
            message = f"📅 Horarios disponibles para {horario['nombre']}:\n\n"
        else:
            message = "📅 Horarios disponibles para tu semana de prueba GRATIS:\n\n"
        
        # Agrupar por clase
        por_clase = {}
        for slot in slots[:20]:  # Máximo 20
            tipo = slot['clase_tipo']
            if tipo not in por_clase:
                por_clase[tipo] = []
            por_clase[tipo].append(slot)
        
        for tipo, slots_tipo in por_clase.items():
            horario = self.horarios[tipo]
            message += f"\n**{horario['nombre']}:**\n"
            dias_texto = self._get_dias_texto(horario['dias'])
            message += f"  {dias_texto} a las {horario['hora']}\n"
        
        message += "\n💬 Respondé con el nombre de la clase y cuándo querés empezar.\n"
        message += "Ejemplo: 'Jiu-Jitsu adultos el martes'\n"
        message += "\n🎁 Recordá: ¡Tu primera SEMANA es GRATIS!"
        
        return message
    def _get_next_class_date(self, clase_tipo):
        """Calcula la fecha de la próxima clase disponible"""
        horario = self.horarios[clase_tipo]
        today = datetime.now()

        for i in range(1, 14):  # Buscar en los próximos 14 días
            date = today + timedelta(days=i)
            day_of_week = date.weekday() + 1

            if day_of_week in horario['dias']:
                # Crear datetime con la hora de la clase
                hora_partes = horario['hora'].split(':')
                return date.replace(hour=int(hora_partes[0]), minute=int(hora_partes[1]))

        return today  # Fallback