"""
Servicio de Recordatorios para BJJ Mingo
Envía recordatorios automáticos 24 horas antes de cada clase
Incluye integración con Celery para tareas programadas
MIGRADO A POSTGRESQL + SQLALCHEMY CON CLASSREMINDER MODEL
"""

import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app import db
from app.models import Lead, ClassReminder, ReminderStatus, Academy

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class ReminderService:
    """
    Servicio que gestiona recordatorios de clases
    - Crea recordatorios cuando se agenda una clase
    - Envía notificaciones 24 horas antes
    - Trackea estado de recordatorios enviados
    """

    def __init__(self):
        # Inicializar servicio de notificaciones Twilio
        try:
            from app.services.notification_service import NotificationService
            self.notifier = NotificationService()
            logger.info("NotificationService integrado en ReminderService")
        except Exception as e:
            logger.warning(f"NotificationService no disponible: {e}")
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

        Args:
            lead_id: ID del prospecto
            trial_week_id: ID de la semana de prueba (puede ser None)
            clase_tipo: Tipo de clase (adultos_jiujitsu, kids, etc.)
            start_date: Fecha de inicio (formato YYYY-MM-DD)

        Returns:
            Dict con success y lista de recordatorios creados
        """
        try:
            # Validar que el lead existe
            lead = Lead.query.get(lead_id)
            if not lead:
                logger.error(f"Lead {lead_id} no encontrado")
                return {'success': False, 'message': 'Lead no encontrado'}

            # Obtener academy_id del lead
            academy_id = lead.academy_id

            # Validar tipo de clase
            horario = self.horarios.get(clase_tipo)
            if not horario:
                logger.error(f"Tipo de clase no válido: {clase_tipo}")
                return {'success': False, 'message': 'Tipo de clase no válido'}

            # Convertir start_date a datetime
            if isinstance(start_date, str):
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_datetime = start_date

            end_datetime = start_datetime + timedelta(days=7)

            reminders_created = []

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
                        second=0,
                        microsecond=0
                    )

                    # Calcular cuándo enviar el recordatorio (24 horas antes)
                    send_at = class_datetime - timedelta(hours=24)

                    # Crear recordatorio en BD
                    reminder = ClassReminder(
                        lead_id=lead_id,
                        academy_id=academy_id,
                        class_type=clase_tipo,
                        class_datetime=class_datetime,
                        send_at=send_at,
                        status=ReminderStatus.PENDING,
                        notes=f'Trial week reminder for {horario["nombre"]}'
                    )

                    db.session.add(reminder)
                    reminders_created.append({
                        'class_datetime': class_datetime.strftime('%Y-%m-%d %H:%M'),
                        'send_at': send_at.strftime('%Y-%m-%d %H:%M'),
                        'day': self.dias_nombres[day_of_week],
                        'type': clase_tipo
                    })

                    logger.info(f"Recordatorio creado: {clase_tipo} el {class_datetime.strftime('%Y-%m-%d %H:%M')}")

                current_date += timedelta(days=1)

            # Commit all reminders
            db.session.commit()

            logger.info(f"OK: {len(reminders_created)} recordatorios creados para lead {lead_id}")

            return {
                'success': True,
                'message': f'{len(reminders_created)} recordatorios creados',
                'reminders': reminders_created,
                'count': len(reminders_created)
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creando recordatorios: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}

    def send_reminder(self, reminder_id):
        """
        Envía un recordatorio específico

        Args:
            reminder_id: ID del recordatorio a enviar

        Returns:
            Dict con success y mensaje
        """
        try:
            reminder = ClassReminder.query.get(reminder_id)

            if not reminder:
                return {'success': False, 'message': 'Recordatorio no encontrado'}

            if reminder.status != ReminderStatus.PENDING:
                return {
                    'success': False,
                    'message': f'Recordatorio no está pendiente (status: {reminder.status})'
                }

            # Obtener lead
            lead = Lead.query.get(reminder.lead_id)
            if not lead:
                reminder.mark_as_failed('Lead no encontrado')
                return {'success': False, 'message': 'Lead no encontrado'}

            if not self.notifier:
                logger.warning("NotificationService no disponible")
                reminder.mark_as_failed('NotificationService no disponible')
                return {'success': False, 'message': 'Servicio de notificaciones no disponible'}

            # Obtener info de la clase
            horario = self.horarios.get(reminder.class_type, {})
            clase_nombre = horario.get('nombre', 'Clase de Jiu-Jitsu')

            # Formatear fecha/hora para el mensaje
            class_dt = reminder.class_datetime
            day_name = self.dias_nombres.get(class_dt.weekday() + 1, class_dt.strftime('%A'))
            date_formatted = class_dt.strftime('%d/%m/%Y')
            time_formatted = class_dt.strftime('%H:%M')

            # Mensaje de recordatorio
            mensaje = f"""Recordatorio de Clase!

Hola {lead.name}!

Te recordamos que manana tenes tu clase de {clase_nombre}:

{day_name} {date_formatted}
{time_formatted}
Santo Domingo de Heredia
Waze: https://waze.com/ul/hd1u0y3qpc

Que traer:
- Ropa deportiva comoda
- Agua
- Si tenes gi, podes traerlo

Te esperamos!

Si no podes asistir, avisanos por favor."""

            # Enviar notificación
            result = self.notifier.send_whatsapp(
                to=lead.phone,
                message=mensaje
            )

            if result['success']:
                message_sid = result.get('sid')
                reminder.mark_as_sent(message_sid)
                logger.info(f"OK: Recordatorio {reminder_id} enviado a {lead.phone}")
                return {
                    'success': True,
                    'message': 'Recordatorio enviado',
                    'sid': message_sid
                }
            else:
                error_msg = result.get('message', 'Error desconocido')
                reminder.mark_as_failed(error_msg)
                logger.error(f"ERROR: Recordatorio {reminder_id} falló: {error_msg}")
                return result

        except Exception as e:
            logger.error(f"Error enviando recordatorio {reminder_id}: {e}")
            import traceback
            traceback.print_exc()

            try:
                reminder = ClassReminder.query.get(reminder_id)
                if reminder:
                    reminder.mark_as_failed(str(e))
            except:
                pass

            return {'success': False, 'message': str(e)}

    def get_pending_reminders(self, limit=100):
        """
        Obtiene recordatorios pendientes que deben enviarse

        Args:
            limit: Número máximo de recordatorios a retornar

        Returns:
            Lista de ClassReminder objects
        """
        return ClassReminder.get_pending_reminders(limit=limit)

    def mark_reminder_sent(self, reminder_id, message_sid=None):
        """
        Marca un recordatorio como enviado

        Args:
            reminder_id: ID del recordatorio
            message_sid: SID del mensaje de Twilio (opcional)

        Returns:
            Dict con success
        """
        try:
            reminder = ClassReminder.query.get(reminder_id)
            if not reminder:
                return {'success': False, 'message': 'Recordatorio no encontrado'}

            reminder.mark_as_sent(message_sid)
            logger.info(f"Recordatorio {reminder_id} marcado como enviado")
            return {'success': True}

        except Exception as e:
            logger.error(f"Error marcando recordatorio como enviado: {e}")
            return {'success': False, 'message': str(e)}

    def get_lead_reminders(self, lead_id, status=None):
        """
        Obtiene todos los recordatorios de un lead

        Args:
            lead_id: ID del lead
            status: Filtrar por status (opcional)

        Returns:
            Lista de ClassReminder objects
        """
        return ClassReminder.get_reminders_for_lead(lead_id, status=status)

    def cancel_reminder(self, reminder_id):
        """
        Cancela un recordatorio programado

        Args:
            reminder_id: ID del recordatorio

        Returns:
            Dict con success
        """
        try:
            reminder = ClassReminder.query.get(reminder_id)
            if not reminder:
                return {'success': False, 'message': 'Recordatorio no encontrado'}

            reminder.cancel()
            logger.info(f"Recordatorio {reminder_id} cancelado")
            return {'success': True}

        except Exception as e:
            logger.error(f"Error cancelando recordatorio: {e}")
            return {'success': False, 'message': str(e)}

    def cancel_lead_future_reminders(self, lead_id):
        """
        Cancela todos los recordatorios futuros de un lead

        Args:
            lead_id: ID del lead

        Returns:
            Dict con success y número de recordatorios cancelados
        """
        try:
            count = ClassReminder.cancel_future_reminders_for_lead(lead_id)
            logger.info(f"{count} recordatorios futuros cancelados para lead {lead_id}")
            return {'success': True, 'count': count}

        except Exception as e:
            logger.error(f"Error cancelando recordatorios: {e}")
            return {'success': False, 'message': str(e)}
