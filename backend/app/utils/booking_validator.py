"""
Booking Validator - Validación de reglas de negocio para agendamiento
Centraliza todas las validaciones de fechas y horarios
Creado: 27/11/2025
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BookingValidator:
    """
    Validador de reglas de negocio para agendamiento de clases

    Responsabilidades:
    - Validar anticipación mínima
    - Validar hora de corte para "hoy"
    - Validar que la fecha sea válida para el tipo de clase
    - Validar que la fecha no sea pasada
    - Sugerir fechas alternativas cuando sea necesario
    """

    # Reglas de agendamiento centralizadas
    RULES = {
        'min_advance_hours': 2,         # Mínimo 2 horas de anticipación
        'max_advance_days': 14,          # Máximo 14 días adelante
    }

    # Horarios de clases (sincronizado con AppointmentScheduler)
    HORARIOS = {
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

    DIAS_NOMBRES = {
        1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
        4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'
    }

    def __init__(self):
        """Inicializa el validador"""
        pass

    def validate_booking_date(
        self,
        target_date: datetime,
        clase_tipo: str,
        class_time: str = None
    ) -> Dict:
        """
        Valida si una fecha es válida para agendar una clase

        Args:
            target_date: Fecha objetivo para la clase (datetime)
            clase_tipo: Tipo de clase ('adultos_jiujitsu', 'kids', etc.)
            class_time: Hora de la clase en formato 'HH:MM' (opcional, se obtiene de HORARIOS si no se provee)

        Returns:
            Dict con:
                - valid: bool
                - error_type: str (si valid=False)
                - message: str con mensaje descriptivo
                - suggested_date: datetime (si aplica)
        """
        now = datetime.now()

        # Validar que el tipo de clase exista
        if clase_tipo not in self.HORARIOS:
            return {
                'valid': False,
                'error_type': 'invalid_class_type',
                'message': f'Tipo de clase no válido: {clase_tipo}'
            }

        horario = self.HORARIOS[clase_tipo]

        # Obtener hora de la clase
        if not class_time:
            class_time = horario['hora']

        # Construir datetime completo de la clase
        hora_partes = class_time.split(':')
        class_datetime = target_date.replace(
            hour=int(hora_partes[0]),
            minute=int(hora_partes[1]),
            second=0,
            microsecond=0
        )

        # VALIDACIÓN 1: Fecha no puede ser en el pasado
        if class_datetime < now:
            suggested = self._get_next_available_date(clase_tipo, horario)
            return {
                'valid': False,
                'error_type': 'past_date',
                'message': 'No podés agendar para una fecha pasada.',
                'suggested_date': suggested
            }

        # VALIDACIÓN 2: Anticipación mínima (2 horas)
        hours_until_class = (class_datetime - now).total_seconds() / 3600

        if hours_until_class < self.RULES['min_advance_hours']:
            suggested = self._get_next_available_date(clase_tipo, horario)
            hours_needed = self.RULES['min_advance_hours']

            return {
                'valid': False,
                'error_type': 'insufficient_advance',
                'message': f'Necesitamos al menos {hours_needed} horas de anticipación.',
                'suggested_date': suggested
            }

        # VALIDACIÓN 3: Fecha no puede estar muy lejos en el futuro
        days_until_class = (class_datetime - now).days

        if days_until_class > self.RULES['max_advance_days']:
            return {
                'valid': False,
                'error_type': 'too_far_ahead',
                'message': f'Solo agendamos hasta {self.RULES["max_advance_days"]} días adelante.'
            }

        # VALIDACIÓN 4: Verificar que sea un día válido para esta clase
        day_of_week = target_date.weekday() + 1  # 1=Lunes, 7=Domingo

        if day_of_week not in horario['dias']:
            suggested = self._get_next_available_date(clase_tipo, horario)
            dias_texto = self._get_dias_texto(horario['dias'])

            return {
                'valid': False,
                'error_type': 'invalid_day_for_class',
                'message': f'{horario["nombre"]} es solo {dias_texto}.',
                'suggested_date': suggested
            }

        # ✅ Todas las validaciones pasaron
        logger.info(f"[VALIDATOR] ✅ Fecha válida: {class_datetime.strftime('%Y-%m-%d %H:%M')} para {clase_tipo}")

        return {
            'valid': True,
            'message': f'Fecha válida para {horario["nombre"]}',
            'class_datetime': class_datetime
        }

    def _get_next_available_date(
        self,
        clase_tipo: str,
        horario: Dict = None
    ) -> datetime:
        """
        Obtiene la próxima fecha disponible para una clase

        Args:
            clase_tipo: Tipo de clase
            horario: Dict con info de horario (opcional)

        Returns:
            datetime de la próxima clase disponible
        """
        if not horario:
            horario = self.HORARIOS.get(clase_tipo, {})

        now = datetime.now()

        # Buscar el próximo día disponible
        for i in range(1, self.RULES['max_advance_days'] + 1):
            candidate_date = now + timedelta(days=i)
            day_of_week = candidate_date.weekday() + 1

            if day_of_week in horario['dias']:
                # Construir datetime completo
                hora_partes = horario['hora'].split(':')
                class_datetime = candidate_date.replace(
                    hour=int(hora_partes[0]),
                    minute=int(hora_partes[1]),
                    second=0,
                    microsecond=0
                )

                # Verificar que tenga al menos 2 horas de anticipación
                hours_until_class = (class_datetime - now).total_seconds() / 3600

                if hours_until_class >= self.RULES['min_advance_hours']:
                    return class_datetime

        # Fallback: retornar fecha 7 días adelante
        return now + timedelta(days=7)

    def _get_dias_texto(self, dias_nums: list) -> str:
        """
        Convierte lista de números de días a texto

        Args:
            dias_nums: Lista de números (1=Lunes, 7=Domingo)

        Returns:
            String con días separados por comas
        """
        return ', '.join([self.DIAS_NOMBRES[d] for d in dias_nums])

    def format_suggested_date(self, suggested_date: datetime) -> str:
        """
        Formatea una fecha sugerida para mostrar al usuario

        Args:
            suggested_date: datetime a formatear

        Returns:
            String formateado (ej: "Martes 28/11 a las 5:00 PM")
        """
        day_of_week = suggested_date.weekday() + 1
        day_name = self.DIAS_NOMBRES[day_of_week]
        date_str = suggested_date.strftime('%d/%m')
        time_str = suggested_date.strftime('%I:%M %p').lower().replace('am', 'AM').replace('pm', 'PM')

        return f"{day_name} {date_str} a las {time_str}"

    def get_booking_rules_summary(self) -> str:
        """
        Retorna un resumen de las reglas de agendamiento

        Returns:
            String con las reglas principales
        """
        return f"""📋 REGLAS DE AGENDAMIENTO:

✅ Anticipación mínima: {self.RULES['min_advance_hours']} horas
✅ Máximo adelante: {self.RULES['max_advance_days']} días

Nota: Podés agendar el MISMO día si hay al menos {self.RULES['min_advance_hours']} horas de anticipación.
"""
