"""
Servicio de Recordatorios para BJJ Mingo
Envía recordatorios automáticos 24 horas antes de cada clase
Incluye integración con Celery para tareas programadas
"""

import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.utils.database import get_db_connection, get_db_cursor

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
        self.db_path = 'bjj_academy.db'

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
        Crea un recordatorio por cada día de clase durante la semana

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
                        second=0
                    )

                    # Crear recordatorio
                    reminder_id = self._create_reminder(
                        lead_id=lead_id,
                        trial_week_id=trial_week_id,
                        clase_tipo=clase_tipo,
                        class_datetime=class_datetime
                    )

                    if reminder_id:
                        reminders_created.append({
                            'id': reminder_id,
                            'date': class_datetime.strftime('%Y-%m-%d'),
                            'day': self.dias_nombres[day_of_week],
                            'time': horario['hora']
                        })

                current_date += timedelta(days=1)

            logger.info(f"✅ Creados {len(reminders_created)} recordatorios para trial_week {trial_week_id}")

            return {
                'success': True,
                'message': f'{len(reminders_created)} recordatorios programados',
                'reminders': reminders_created
            }

        except Exception as e:
            logger.error(f"Error programando recordatorios: {e}")
            return {'success': False, 'message': str(e)}

    def _create_reminder(self, lead_id, trial_week_id=None, appointment_id=None,
                        clase_tipo='adultos_jiujitsu', class_datetime=None):
        """
        Crea un recordatorio en la base de datos

        Returns:
            ID del recordatorio creado o None si hubo error
        """
        try:
            with get_db_cursor(db_path=self.db_path) as cursor:
                # Verificar si ya existe un recordatorio para esta clase
                cursor.execute("""
                    SELECT id FROM class_reminders
                    WHERE lead_id = ? AND class_datetime = ?
                """, (lead_id, class_datetime.strftime('%Y-%m-%d %H:%M:%S')))

                existing = cursor.fetchone()
                if existing:
                    logger.info(f"Recordatorio ya existe para lead {lead_id} en {class_datetime}")
                    return existing[0]

                # Crear nuevo recordatorio
                cursor.execute("""
                    INSERT INTO class_reminders
                    (lead_id, trial_week_id, appointment_id, clase_tipo, class_datetime, reminder_status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (lead_id, trial_week_id, appointment_id, clase_tipo,
                     class_datetime.strftime('%Y-%m-%d %H:%M:%S')))

                reminder_id = cursor.lastrowid
                logger.info(f"Recordatorio creado: ID {reminder_id} para {class_datetime}")
                return reminder_id

        except Exception as e:
            logger.error(f"Error creando recordatorio: {e}")
            return None

    def check_and_send_reminders(self):
        """
        Verifica qué clases están a 24 horas y envía recordatorios
        Esta función debe ejecutarse periódicamente (cada hora con Celery)

        Returns:
            Dict con estadísticas de recordatorios enviados
        """
        try:
            # Calcular ventana de tiempo (24 horas desde ahora, +/- 1 hora de margen)
            now = datetime.now()
            window_start = now + timedelta(hours=23)
            window_end = now + timedelta(hours=25)

            logger.info(f"🔍 Buscando recordatorios entre {window_start} y {window_end}")

            # Buscar recordatorios pendientes en la ventana de tiempo
            with get_db_connection(db_path=self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        cr.id,
                        cr.lead_id,
                        cr.clase_tipo,
                        cr.class_datetime,
                        l.name,
                        l.phone_number
                    FROM class_reminders cr
                    JOIN lead l ON cr.lead_id = l.id
                    WHERE cr.reminder_status = 'pending'
                    AND cr.class_datetime BETWEEN ? AND ?
                    ORDER BY cr.class_datetime
                """, (window_start.strftime('%Y-%m-%d %H:%M:%S'),
                     window_end.strftime('%Y-%m-%d %H:%M:%S')))

                pending_reminders = cursor.fetchall()

            if not pending_reminders:
                logger.info("No hay recordatorios pendientes en esta ventana")
                return {'success': True, 'sent': 0, 'failed': 0}

            logger.info(f"📬 Encontrados {len(pending_reminders)} recordatorios pendientes")

            sent_count = 0
            failed_count = 0

            # Enviar cada recordatorio
            for reminder in pending_reminders:
                reminder_id, lead_id, clase_tipo, class_datetime_str, lead_name, phone = reminder

                result = self._send_reminder(
                    reminder_id=reminder_id,
                    lead_name=lead_name,
                    phone=phone,
                    clase_tipo=clase_tipo,
                    class_datetime_str=class_datetime_str
                )

                if result['success']:
                    sent_count += 1
                else:
                    failed_count += 1

            logger.info(f"✅ Recordatorios enviados: {sent_count}, Fallidos: {failed_count}")

            return {
                'success': True,
                'sent': sent_count,
                'failed': failed_count,
                'total': len(pending_reminders)
            }

        except Exception as e:
            logger.error(f"Error verificando recordatorios: {e}")
            return {'success': False, 'error': str(e)}

    def _send_reminder(self, reminder_id, lead_name, phone, clase_tipo, class_datetime_str):
        """
        Envía un recordatorio individual por WhatsApp

        Returns:
            Dict con success y mensaje
        """
        try:
            # Parsear fecha/hora
            class_datetime = datetime.strptime(class_datetime_str, '%Y-%m-%d %H:%M:%S')

            # Construir mensaje
            horario = self.horarios[clase_tipo]
            day_name = self.dias_nombres[class_datetime.weekday() + 1]

            message = f"""🔔 *RECORDATORIO DE CLASE*

¡Hola {lead_name}! 👋

Te recordamos que mañana {day_name} {class_datetime.strftime('%d/%m/%Y')} tenés clase de:

🥋 *{horario['nombre']}*
⏰ Hora: {horario['hora']}
📍 Santo Domingo de Heredia

🗺️ Waze: https://waze.com/ul/hd1u0y3qpc

👕 Recordá traer:
- Ropa deportiva cómoda
- Agua
- Toalla

¡Te esperamos! 🥋

Si no podés asistir, avisanos por favor.

---
BJJ Mingo"""

            # Enviar mensaje por WhatsApp
            if self.notifier and self.notifier.twilio_available:
                send_result = self.notifier._send_whatsapp_notification(phone, message)

                if send_result['success']:
                    # Marcar como enviado
                    self._update_reminder_status(
                        reminder_id,
                        status='sent',
                        sent_at=datetime.now()
                    )
                    logger.info(f"✅ Recordatorio {reminder_id} enviado a {phone}")
                    return {'success': True, 'message': 'Recordatorio enviado'}
                else:
                    # Marcar como fallido
                    self._update_reminder_status(
                        reminder_id,
                        status='failed',
                        error_message=send_result['message']
                    )
                    logger.error(f"❌ Error enviando recordatorio {reminder_id}: {send_result['message']}")
                    return {'success': False, 'message': send_result['message']}
            else:
                # NotificationService no disponible
                logger.warning(f"⚠️ NotificationService no disponible, recordatorio {reminder_id} no enviado")
                logger.info(f"Mensaje que se hubiera enviado:\n{message}")

                # Marcar como fallido con explicación
                self._update_reminder_status(
                    reminder_id,
                    status='failed',
                    error_message='NotificationService no disponible'
                )
                return {'success': False, 'message': 'NotificationService no disponible'}

        except Exception as e:
            logger.error(f"Error enviando recordatorio {reminder_id}: {e}")
            self._update_reminder_status(
                reminder_id,
                status='failed',
                error_message=str(e)
            )
            return {'success': False, 'message': str(e)}

    def _update_reminder_status(self, reminder_id, status, sent_at=None, error_message=None):
        """
        Actualiza el estado de un recordatorio
        """
        try:
            with get_db_cursor(db_path=self.db_path) as cursor:
                if sent_at:
                    cursor.execute("""
                        UPDATE class_reminders
                        SET reminder_status = ?, reminder_sent_at = ?
                        WHERE id = ?
                    """, (status, sent_at.strftime('%Y-%m-%d %H:%M:%S'), reminder_id))
                elif error_message:
                    cursor.execute("""
                        UPDATE class_reminders
                        SET reminder_status = ?, error_message = ?
                        WHERE id = ?
                    """, (status, error_message, reminder_id))
                else:
                    cursor.execute("""
                        UPDATE class_reminders
                        SET reminder_status = ?
                        WHERE id = ?
                    """, (status, reminder_id))

                logger.info(f"Recordatorio {reminder_id} actualizado a estado: {status}")

        except Exception as e:
            logger.error(f"Error actualizando recordatorio {reminder_id}: {e}")

    def get_pending_reminders_count(self):
        """
        Obtiene la cantidad de recordatorios pendientes
        Útil para monitoreo
        """
        try:
            with get_db_connection(db_path=self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM class_reminders
                    WHERE reminder_status = 'pending'
                    AND class_datetime > datetime('now')
                """)
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            logger.error(f"Error contando recordatorios: {e}")
            return 0

    def test_reminder(self, lead_id):
        """
        Envía un recordatorio de prueba inmediatamente (sin esperar 24 horas)
        Útil para testing
        """
        try:
            # Obtener información del lead
            with get_db_connection(db_path=self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, phone_number FROM lead WHERE id = ?
                """, (lead_id,))
                lead_data = cursor.fetchone()

            if not lead_data:
                return {'success': False, 'message': f'Lead {lead_id} no encontrado'}

            lead_name, phone = lead_data

            # Crear fecha de prueba (mañana a las 6pm)
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow = tomorrow.replace(hour=18, minute=0, second=0)

            # Enviar recordatorio de prueba
            result = self._send_reminder(
                reminder_id=0,  # ID temporal para prueba
                lead_name=lead_name,
                phone=phone,
                clase_tipo='adultos_jiujitsu',
                class_datetime_str=tomorrow.strftime('%Y-%m-%d %H:%M:%S')
            )

            return result

        except Exception as e:
            logger.error(f"Error en test de recordatorio: {e}")
            return {'success': False, 'message': str(e)}
