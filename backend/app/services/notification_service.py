"""
Notification Service para BJJ Mingo
Envía notificaciones al staff cuando un nuevo prospecto agenda una clase de prueba
Versión actualizada con múltiples contactos de respaldo
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio para enviar notificaciones por WhatsApp y Email usando Twilio
    """

    def __init__(self):
        """Inicializa el servicio de notificaciones"""
        self.twilio_available = False
        self.client = None
        self.whatsapp_number = None

        # Intentar inicializar Twilio
        self._initialize_twilio()

    def _initialize_twilio(self):
        """Inicializa cliente de Twilio"""
        try:
            from twilio.rest import Client

            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

            if not account_sid or not auth_token or not self.whatsapp_number:
                logger.warning("⚠️ Twilio credentials no configuradas completamente")
                return

            self.client = Client(account_sid, auth_token)
            self.twilio_available = True

            logger.info("✅ NotificationService inicializado con Twilio")

        except ImportError:
            logger.warning("⚠️ Twilio library no instalada")
        except Exception as e:
            logger.error(f"❌ Error inicializando Twilio: {e}")

    def notify_new_trial_booking(self, lead_info, trial_info):
        """
        Notifica al staff de la academia sobre un nuevo prospecto que agendó clase de prueba
        Intenta: 1) WhatsApp primario, 2) WhatsApp secundario, 3) Email

        Args:
            lead_info: Dict con información del prospecto (name, phone, etc.)
            trial_info: Dict con información de la clase (clase_tipo, start_date, etc.)

        Returns:
            Dict con status y mensaje
        """
        try:
            # Obtener contactos de notificación
            notification_contacts = self._get_notification_contacts()

            if not notification_contacts:
                logger.error("❌ No se encontraron contactos de notificación configurados")
                return {
                    'success': False,
                    'message': 'Contactos de notificación no configurados'
                }

            # Construir mensaje de notificación
            notification_message = self._build_notification_message(lead_info, trial_info)

            # Intentar enviar por WhatsApp primario
            if self.twilio_available and self.client:
                primary_whatsapp = notification_contacts.get('primary_whatsapp')
                if primary_whatsapp:
                    logger.info(f"📱 Intentando notificación a WhatsApp primario: {primary_whatsapp}")
                    primary_result = self._send_whatsapp_notification(
                        primary_whatsapp,
                        notification_message
                    )
                    
                    if primary_result['success']:
                        logger.info("✅ Notificación enviada exitosamente por WhatsApp primario")
                        return primary_result
                
                # Si falla el primario, intentar con secundario
                secondary_whatsapp = notification_contacts.get('secondary_whatsapp')
                if secondary_whatsapp:
                    logger.warning("⚠️ Falló WhatsApp primario, intentando con secundario")
                    secondary_result = self._send_whatsapp_notification(
                        secondary_whatsapp,
                        notification_message
                    )
                    
                    if secondary_result['success']:
                        logger.info("✅ Notificación enviada por WhatsApp secundario")
                        return secondary_result
                
                # Si ambos WhatsApp fallan, intentar email
                email = notification_contacts.get('email')
                if email:
                    logger.info("📧 Intentando notificación por email como respaldo")
                    return self._send_email_notification(
                        email,
                        lead_info,
                        trial_info
                    )
            else:
                # Si Twilio no está disponible, intentar email directamente
                email = notification_contacts.get('email')
                if email:
                    logger.warning("⚠️ Twilio no disponible. Intentando notificación por email")
                    return self._send_email_notification(
                        email,
                        lead_info,
                        trial_info
                    )
                    
                # Fallback: solo log
                logger.warning("⚠️ No hay métodos de notificación disponibles. Notificación solo en logs:")
                logger.info(f"\n{'='*50}\n{notification_message}\n{'='*50}")
                return {
                    'success': False,
                    'message': 'No hay métodos de notificación disponibles'
                }

        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    def _build_notification_message(self, lead_info, trial_info):
        """Construye el mensaje de notificación para el staff"""

        # Información del prospecto
        lead_name = lead_info.get('name', 'No proporcionado')
        lead_phone = lead_info.get('phone', 'No proporcionado')
        lead_status = lead_info.get('status', 'trial_scheduled')

        # Información de la clase
        clase_nombre = trial_info.get('clase_nombre', 'No especificado')
        start_date = trial_info.get('start_date', 'No especificado')
        dias_texto = trial_info.get('dias_texto', 'No especificado')
        hora = trial_info.get('hora', 'No especificado')
        notes = trial_info.get('notes', '')

        # Formatear fecha
        try:
            if start_date != 'No especificado':
                date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                fecha_formateada = date_obj.strftime('%d/%m/%Y')
            else:
                fecha_formateada = start_date
        except:
            fecha_formateada = start_date

        # Construir mensaje
        message = f"""🔔 *NUEVO PROSPECTO - SEMANA DE PRUEBA*

👤 *Prospecto:*
• Nombre: {lead_name}
• Teléfono: {lead_phone}
• Estado: {lead_status}

🥋 *Clase Agendada:*
• Tipo: {clase_nombre}
• Días: {dias_texto}
• Horario: {hora}
• Inicio: {fecha_formateada}

📝 *Notas:*
{notes if notes else 'Sin notas adicionales'}

⏰ Registrado: {datetime.now().strftime('%d/%m/%Y %H:%M')}

---
*BJJ Mingo - Sistema de Notificaciones*"""

        return message

    def _send_whatsapp_notification(self, to_phone, message):
        """Envía notificación por WhatsApp usando Twilio"""
        try:
            if not to_phone:
                logger.error("❌ Número de teléfono no proporcionado")
                return {
                    'success': False,
                    'message': 'Número de teléfono no proporcionado'
                }
                
            # Formatear números para WhatsApp
            # Twilio requiere formato: whatsapp:+[código_país][número]
            from_whatsapp = f"whatsapp:{self.whatsapp_number}"
            to_whatsapp = f"whatsapp:{to_phone}"

            logger.info(f"📤 Enviando notificación de {from_whatsapp} a {to_whatsapp}")

            # Enviar mensaje
            twilio_message = self.client.messages.create(
                from_=from_whatsapp,
                to=to_whatsapp,
                body=message
            )

            logger.info(f"✅ Notificación enviada. SID: {twilio_message.sid}")

            return {
                'success': True,
                'message': 'Notificación enviada exitosamente',
                'sid': twilio_message.sid
            }

        except Exception as e:
            logger.error(f"❌ Error enviando WhatsApp: {e}")
            return {
                'success': False,
                'message': f'Error enviando WhatsApp: {str(e)}'
            }

    def _send_email_notification(self, email, lead_info, trial_info):
        """Envía notificación por email como respaldo"""
        try:
            # Por ahora solo log, pero aquí podrías integrar SendGrid o SMTP
            logger.info(f"📧 Email notification would be sent to: {email}")
            
            # Construir mensaje en formato texto para email
            message = self._build_notification_message(lead_info, trial_info)
            # Quitar asteriscos del formato WhatsApp para email
            message = message.replace('*', '')
            
            logger.info(f"Mensaje para email:\n{message}")
            
            # TODO: Implementar envío real de email con SendGrid o SMTP
            # Ejemplo con smtplib básico (descomentar y configurar):
            """
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['Subject'] = '🔔 Nuevo Prospecto - BJJ Mingo'
            msg['From'] = 'sistema@bjjmingo.com'
            msg['To'] = email
            
            body = MIMEText(message, 'plain')
            msg.attach(body)
            
            # Configurar servidor SMTP (ejemplo con Gmail)
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login('tu_email@gmail.com', 'tu_contraseña')
            
            server.send_message(msg)
            server.quit()
            
            return {
                'success': True,
                'message': 'Email enviado exitosamente'
            }
            """
            
            return {
                'success': False,  # Cambiar a True cuando se implemente
                'message': 'Email notification logged but not sent (not implemented)'
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando email: {e}")
            return {
                'success': False,
                'message': f'Error enviando email: {str(e)}'
            }

    def _get_notification_contacts(self):
        """Obtiene los contactos para notificaciones"""
        try:
            from app.config.academy_info import ACADEMY_INFO
            return ACADEMY_INFO.get('notification_contacts', {})
        except ImportError:
            logger.error("No se pudo importar academy_info")
            return {}

    def test_notification(self):
        """Envía una notificación de prueba"""
        test_lead = {
            'name': 'Juan Pérez (PRUEBA)',
            'phone': '+506-1234-5678',
            'status': 'trial_scheduled'
        }

        test_trial = {
            'clase_nombre': 'Jiu-Jitsu Adultos',
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'dias_texto': 'Lunes a Viernes',
            'hora': '18:00',
            'notes': 'Mensaje de prueba del sistema de notificaciones'
        }

        return self.notify_new_trial_booking(test_lead, test_trial)