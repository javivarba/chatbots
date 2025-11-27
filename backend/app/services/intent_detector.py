"""
Intent Detector - Detección de Intenciones en Mensajes
Responsabilidad única: Detectar patrones e intenciones en mensajes de usuarios
"""

import re
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Detector de intenciones en mensajes

    Responsabilidades:
    - Detectar nombres en mensajes
    - Detectar intención de agendamiento
    - Detectar tipo de pregunta
    - Detectar sentimiento (futuro)
    """

    # Palabras clave por intención
    BOOKING_KEYWORDS = [
        'agendar', 'reservar', 'apartar', 'quiero clase',
        'mi nombre es', 'quiero una clase', 'clase el',
        'clase para', 'semana de prueba'
    ]

    DAYS_OF_WEEK = [
        'lunes', 'martes', 'miércoles', 'miercoles',
        'jueves', 'viernes', 'sábado', 'sabado',
        'domingo', 'mañana', 'hoy'
    ]

    QUESTION_TYPES = {
        'precio': ['precio', 'costo', 'cuanto', 'cuánto', 'vale', 'mensualidad'],
        'horario': ['horario', 'hora', 'cuando', 'cuándo', 'día', 'dias'],
        'ubicacion': ['ubicación', 'ubicacion', 'donde', 'dónde', 'dirección', 'direccion', 'waze'],
        'experiencia': ['experiencia', 'nivel', 'principiante', 'avanzado', 'cinturón'],
        'equipo': ['equipo', 'ropa', 'gi', 'kimono', 'necesito', 'traer'],
        'edad': ['edad', 'años', 'niños', 'niño', 'kids', 'adultos']
    }

    def detect_name(self, message: str) -> Optional[str]:
        """
        Detectar si el usuario proporcionó su nombre en el mensaje

        Patrones detectados:
        - "Mi nombre es Juan"
        - "Me llamo María"
        - "Soy Pedro"
        - "Juan Pérez" (solo nombre)

        Args:
            message: Mensaje del usuario

        Returns:
            Nombre detectado o None
        """
        msg = message.strip()

        # Patrón 1: "Mi nombre es Juan" o "Me llamo Juan" o "Soy Juan"
        patterns = [
            r'(?:mi nombre es|me llamo|soy)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
            r'(?:nombre:?)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Verificar que no sea una palabra común
                if name.lower() not in ['hola', 'si', 'no', 'bueno', 'ok', 'gracias']:
                    logger.info(f"[INTENT] Nombre detectado (patrón): {name}")
                    return name

        # Patrón 2: Solo un nombre (2 palabras capitalizadas, probablemente nombre y apellido)
        if re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+$', msg):
            logger.info(f"[INTENT] Nombre detectado (nombre completo): {msg.strip()}")
            return msg.strip()

        return None

    def detect_booking_intent(
        self,
        message: str,
        ai_response: str = None,
        history: List[Dict] = None
    ) -> bool:
        """
        Detectar si el usuario está intentando agendar una clase

        Args:
            message: Mensaje del usuario
            ai_response: Respuesta generada por IA (opcional)
            history: Historial de conversación (opcional)

        Returns:
            True si se detecta intención de agendamiento
        """
        msg_lower = message.lower()

        # 1. Verificar palabras clave de agendamiento
        has_booking_keyword = any(
            word in msg_lower for word in self.BOOKING_KEYWORDS
        )

        # 2. Verificar si tiene día de la semana
        has_day = any(day in msg_lower for day in self.DAYS_OF_WEEK)

        # 3. Verificar si tiene hora
        has_time = bool(re.search(r'\d{1,2}:?\d{0,2}\s?(am|pm|hrs)?', msg_lower))

        # 4. Verificar si respondió con nombre (formato: "Nombre Apellido")
        name_pattern = bool(re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+', message))

        # 5. Verificar en historial si ya se estaba hablando de agendamiento
        discussing_booking = False
        if history:
            for msg in history[-5:]:  # Últimos 5 mensajes
                content_lower = msg['content'].lower()
                if any(word in content_lower for word in [
                    'agendar', 'reservar', 'semana de prueba',
                    'horario', 'clase para'
                ]):
                    discussing_booking = True
                    break

        # Lógica de detección
        if has_booking_keyword and has_day and has_time:
            logger.info("[INTENT] Intención de agendamiento detectada (keyword + día + hora)")
            return True
        elif has_day and has_time and discussing_booking:
            logger.info("[INTENT] Intención de agendamiento detectada (día + hora + contexto)")
            return True
        elif name_pattern and has_day and has_time:
            logger.info("[INTENT] Intención de agendamiento detectada (nombre + día + hora)")
            return True
        elif name_pattern and discussing_booking:
            logger.info("[INTENT] Intención de agendamiento detectada (nombre + contexto)")
            return True

        return False

    def detect_question_type(self, message: str) -> Optional[str]:
        """
        Detectar el tipo de pregunta del usuario

        Args:
            message: Mensaje del usuario

        Returns:
            Tipo de pregunta ('precio', 'horario', 'ubicacion', etc.) o None
        """
        msg_lower = message.lower()

        for question_type, keywords in self.QUESTION_TYPES.items():
            if any(keyword in msg_lower for keyword in keywords):
                logger.info(f"[INTENT] Tipo de pregunta detectada: {question_type}")
                return question_type

        return None

    def detect_sentiment(self, message: str) -> str:
        """
        Analizar el sentimiento del mensaje

        Args:
            message: Mensaje del usuario

        Returns:
            'positive', 'negative', o 'neutral'
        """
        msg_lower = message.lower()

        positive_words = [
            'gracias', 'excelente', 'genial', 'bueno', 'perfecto',
            'sí', 'dale', 'pura vida', 'interesante', 'me gusta'
        ]

        negative_words = [
            'no', 'mal', 'caro', 'lejos', 'difícil', 'problema',
            'cancelar', 'no puedo', 'no me interesa'
        ]

        positive_count = sum(1 for word in positive_words if word in msg_lower)
        negative_count = sum(1 for word in negative_words if word in msg_lower)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def detect_urgency(self, message: str) -> bool:
        """
        Detectar si el mensaje indica urgencia

        Args:
            message: Mensaje del usuario

        Returns:
            True si el mensaje es urgente
        """
        msg_lower = message.lower()

        urgency_keywords = [
            'urgente', 'rápido', 'ya', 'ahora', 'hoy',
            'cuanto antes', 'lo antes posible', 'inmediato'
        ]

        is_urgent = any(keyword in msg_lower for keyword in urgency_keywords)

        if is_urgent:
            logger.info("[INTENT] Mensaje urgente detectado")

        return is_urgent

    def detect_greeting(self, message: str) -> bool:
        """
        Detectar si el mensaje es un saludo

        Args:
            message: Mensaje del usuario

        Returns:
            True si es un saludo
        """
        msg_lower = message.lower().strip()

        greetings = [
            'hola', 'buenos dias', 'buenas tardes', 'buenas noches',
            'buen día', 'buenas', 'hey', 'holis', 'ola'
        ]

        return any(greeting in msg_lower for greeting in greetings)

    def detect_farewell(self, message: str) -> bool:
        """
        Detectar si el mensaje es una despedida

        Args:
            message: Mensaje del usuario

        Returns:
            True si es una despedida
        """
        msg_lower = message.lower().strip()

        farewells = [
            'gracias', 'chao', 'adiós', 'hasta luego',
            'nos vemos', 'bye', 'pura vida', 'ok'
        ]

        return any(farewell in msg_lower for farewell in farewells)

    def extract_phone_number(self, message: str) -> Optional[str]:
        """
        Extraer número de teléfono del mensaje

        Args:
            message: Mensaje del usuario

        Returns:
            Número de teléfono encontrado o None
        """
        # Patrón para números de Costa Rica
        patterns = [
            r'\+?506\s?[6-8]\d{3}\s?\d{4}',  # +506 8888 8888
            r'[6-8]\d{3}[-\s]?\d{4}',         # 8888-8888 o 8888 8888
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                phone = match.group(0)
                logger.info(f"[INTENT] Número de teléfono detectado: {phone}")
                return phone

        return None

    def extract_age(self, message: str) -> Optional[int]:
        """
        Extraer edad del mensaje

        Args:
            message: Mensaje del usuario

        Returns:
            Edad encontrada o None
        """
        # Patrón: "tengo 25 años", "25 años", "edad: 25"
        patterns = [
            r'(?:tengo|tiene|edad:?)\s+(\d{1,2})\s*(?:años?)?',
            r'(\d{1,2})\s*años?'
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 4 <= age <= 99:  # Rango válido
                    logger.info(f"[INTENT] Edad detectada: {age}")
                    return age

        return None
