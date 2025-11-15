"""
Servicio de Recordatorios para BJJ Mingo
Envía recordatorios automáticos 24 horas antes de cada clase
Incluye integración con Celery para tareas programadas
MIGRADO A SQLALCHEMY + POSTGRESQL (SIMPLIFICADO)
NOTA: Funcionalidad completa de recordatorios requiere modelo ClassReminder
"""

import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app import db
from app.models import Lead

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class ReminderService:
    """
    Servicio que gestiona recordatorios de clases
    - Crea recordatorios cuando se agenda una clase
    - Envía notificaciones 24 horas antes
    - Trackea estado de recordatorios enviados

    NOTA: Versión simplificada sin tabla class_reminders
    """

    def __init__(self):
        # Inicializar servicio de notificaciones Twilio
        try:
            from app.services.notification_service import NotificationService
            self.notifier = NotificationService()
            logger.info("✅ NotificationService integrado en ReminderService")
        except Exception as e:
            logger.warning(f"⚠️ NotificationService no disponible: {e}")
            self.notifier = None

        # Horarios de clases (sincronizado con AppointmentScheduler)
        self.horarios = {
            'adultos_jiujitsu': {
                'dias': [1, 2, 3, 4, 5],  # Lunes a Viernes
                'hora': '18:00',
                'nombre': 'Jiu-Jitsu Adultos'
            },
            'adultos_striking': {
                'dias': [2, 4],  # Martes y Jueves
                'hora': '19:30',
                'nombre': 'Striking Adultos'
            },
            'kids': {
                'dias': [2, 4],  # Martes y Jueves
                'hora': '17:00',
                'nombre': 'Jiu-Jitsu Kids'
            },
            'juniors': {
                'dias': [1, 3],  # Lunes y Miércoles
                'hora': '17:00',
                'nombre': 'Jiu-Jitsu Juniors'
            }
        }

        self.dias_nombres = {
            1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
            4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'
        }

    def schedule_trial_week_reminders(self, lead_id, trial_week_id, clase_tipo, start_date):
        """
        Programa recordatorios para toda la semana de prueba

        NOTA: Versión simplificada - solo registra en logs
        Para implementación completa, crear modelo ClassReminder

        Args:
            lead_id: ID del prospecto
            trial_week_id: ID de la semana de prueba
            clase_tipo: Tipo de clase (adultos_jiujitsu, kids, etc.)
            start_date: Fecha de inicio (formato YYYY-MM-DD)

        Returns:
            Dict con success y lista de recordatorios creados
        """
        try:
            horario = self.horarios.get(clase_tipo)
            if not horario:
                logger.error(f"Tipo de clase no válido: {clase_tipo}")
                return {'success': False, 'message': 'Tipo de clase no válido'}

            # Convertir start_date a datetime
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = start_datetime + timedelta(days=7)

            reminders_planned = []

            # Iterar los próximos 7 días
            current_date = start_datetime
            while current_date <= end_datetime:
                day_of_week = current_date.weekday() + 1  # 1=Lunes

                # Si hay clase ese día
                if day_of_week in horario['dias']:
                    # Construir datetime de la clase
                    hora_partes = horario['hora'].split(':')
                    class_datetime = current_date.replace(
                        hour=int(hora_partes[0]),
                        minute=int(hora_partes[1]),
                        second=0
                    )

                    # Registrar en logs (sin guardar en BD por ahora)
                    reminders_planned.append({
                        'date': class_datetime.strftime('%Y-%m-%d'),
                        'day': self.dias_nombres[day_of_week],
                        'time': horario['hora'],
                        'send_at': (class_datetime - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M')
                    })

                    logger.info(f"📅 Recordatorio planeado para {class_datetime.strftime('%Y-%m-%d %H:%M')}")

                current_date += timedelta(days=1)

            logger.info(f"✅ {len(reminders_planned)} recordatorios planeados para lead {lead_id}")
            logger.warning("⚠️ Recordatorios no se guardan en BD (requiere modelo ClassReminder)")

            return {
                'success': True,
                'message': f'{len(reminders_planned)} recordatorios planeados (sin persistencia)',
                'reminders': reminders_planned
            }

        except Exception as e:
            logger.error(f"Error planeando recordatorios: {e}")
            return {'success': False, 'message': str(e)}

    def send_reminder(self, lead_id, class_datetime, clase_tipo):
        """
        Envía un recordatorio inmediato a un lead

        Args:
            lead_id: ID del lead
            class_datetime: Datetime de la clase
            clase_tipo: Tipo de clase

        Returns:
            Dict con success y mensaje
        """
        try:
            lead = Lead.query.get(lead_id)

            if not lead:
                return {'success': False, 'message': 'Lead no encontrado'}

            if not self.notifier:
                logger.warning("NotificationService no disponible")
                return {'success': False, 'message': 'Servicio de notificaciones no disponible'}

            # Obtener info de la clase
            horario = self.horarios.get(clase_tipo, {})
            clase_nombre = horario.get('nombre', 'Clase de Jiu-Jitsu')

            # Formatear fecha/hora para el mensaje
            day_name = class_datetime.strftime('%A')
            date_formatted = class_datetime.strftime('%d/%m/%Y')
            time_formatted = class_datetime.strftime('%H:%M')

            # Mensaje de recordatorio
            mensaje = f"""🔔 ¡Recordatorio de Clase!

Hola {lead.name}! 👋

Te recordamos que mañana tenés tu clase de {clase_nombre}:

📅 {day_name} {date_formatted}
🕐 {time_formatted}
📍 Santo Domingo de Heredia
🗺️ Waze: https://waze.com/ul/hd1u0y3qpc

👕 Qué traer:
- Ropa deportiva cómoda
- Agua
- Si tenés gi, podés traerlo

¡Te esperamos! 🥋

Si no podés asistir, avisanos por favor."""

            # Enviar notificación
            result = self.notifier.send_whatsapp(
                to=lead.phone,
                message=mensaje
            )

            if result['success']:
                logger.info(f"✅ Recordatorio enviado a {lead.phone}")
                return {
                    'success': True,
                    'message': 'Recordatorio enviado',
                    'sid': result.get('sid')
                }
            else:
                logger.error(f"❌ Error enviando recordatorio: {result['message']}")
                return result

        except Exception as e:
            logger.error(f"Error enviando recordatorio: {e}")
            return {'success': False, 'message': str(e)}

    def get_pending_reminders(self):
        """
        Obtiene recordatorios pendientes que deben enviarse

        NOTA: Versión simplificada - retorna lista vacía
        Para implementación completa, crear modelo ClassReminder

        Returns:
            Lista de recordatorios pendientes
        """
        logger.warning("⚠️ get_pending_reminders: Requiere modelo ClassReminder")
        return []

    def mark_reminder_sent(self, reminder_id):
        """
        Marca un recordatorio como enviado

        NOTA: Versión simplificada - solo registra en logs
        Para implementación completa, crear modelo ClassReminder
        """
        logger.warning(f"⚠️ mark_reminder_sent({reminder_id}): Requiere modelo ClassReminder")
        return {'success': True, 'message': 'Simulado - sin persistencia'}

    def get_lead_reminders(self, lead_id):
        """
        Obtiene todos los recordatorios de un lead

        NOTA: Versión simplificada - retorna lista vacía
        Para implementación completa, crear modelo ClassReminder
        """
        logger.warning(f"⚠️ get_lead_reminders({lead_id}): Requiere modelo ClassReminder")
        return []

    def cancel_reminder(self, reminder_id):
        """
        Cancela un recordatorio programado

        NOTA: Versión simplificada - solo registra en logs
        Para implementación completa, crear modelo ClassReminder
        """
        logger.warning(f"⚠️ cancel_reminder({reminder_id}): Requiere modelo ClassReminder")
        return {'success': True, 'message': 'Simulado - sin persistencia'}
