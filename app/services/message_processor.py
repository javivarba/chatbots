from app.models import Lead, Conversation, Academy
from datetime import datetime

class MessageProcessor:
    def process_message(self, message, lead, conversation, academy):
        """Procesa mensajes y genera respuestas basadas en palabras clave"""
        
        msg_lower = message.lower()
        
        # Detectar intenci�n b�sica
        if any(word in msg_lower for word in ["hola", "hi", "buenos dias", "buenas"]):
            return self._greeting_response(academy, lead)
        elif any(word in msg_lower for word in ["precio", "costo", "cuanto", "pago"]):
            return self._pricing_response(academy)
        elif any(word in msg_lower for word in ["horario", "hora", "cuando", "dias"]):
            return self._schedule_response(academy)
        elif any(word in msg_lower for word in ["donde", "direccion", "ubicacion"]):
            return self._location_response(academy)
        elif any(word in msg_lower for word in ["prueba", "gratis", "probar"]):
            return self._trial_response(academy)
        else:
            return self._default_response(academy)
    
    def _greeting_response(self, academy, lead):
        name = lead.name if lead.name and lead.name != "WhatsApp User" else ""
        greeting = f"Hola {name}!" if name else "Hola!"
        return f"{greeting} Bienvenido a {academy.name} ??\n\nSoy tu asistente virtual. Puedo ayudarte con:\n� Horarios y precios\n� Clase de prueba GRATIS\n� Ubicaci�n\n\n�En qu� puedo ayudarte?"
    
    def _pricing_response(self, academy):
        return f"?? Nuestros precios en {academy.name}:\n\n� Mensualidad Adultos: $120\n� Mensualidad Ni�os: $80\n� Clase suelta: $25\n\n? Primera clase GRATIS!\n\n�Te gustar�a agendar tu clase de prueba?"
    
    def _schedule_response(self, academy):
        return f"?? Horarios de {academy.name}:\n\n� Lunes a Viernes: 6am-9am, 12pm-1pm, 5pm-9pm\n� S�bados: 9am-12pm\n\nTenemos clases para principiantes, intermedios y avanzados.\n\n�Quieres agendar una clase de prueba?"
    
    def _location_response(self, academy):
        return f"?? Ubicaci�n de {academy.name}:\n\nAvenida Central, San Jos�\n(Frente al parque central)\n\n?? Parqueo disponible\n?? Tel: {academy.phone}\n\n�Te gustar�a visitarnos?"
    
    def _trial_response(self, academy):
        return f"?? �Excelente decisi�n!\n\nEn {academy.name} tu primera clase es GRATIS.\n\nPor favor comp�rteme:\n1. Tu nombre completo\n2. �Has practicado artes marciales antes?\n3. �Qu� d�a prefieres venir?\n\n�Te esperamos! ??"
    
    def _default_response(self, academy):
        return f"Gracias por contactar a {academy.name}! ??\n\n�C�mo puedo ayudarte?\n\n� ?? Horarios\n� ?? Precios\n� ?? Clase de prueba\n� ?? Ubicaci�n\n\nEscribe tu pregunta y con gusto te ayudo."