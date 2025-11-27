"""
Lead Manager - Gestión de Leads
Responsabilidad única: Lógica de negocio de leads
Refactored with Repository Pattern: 25/11/2025
"""

import re
import logging
from datetime import datetime
from app.models import LeadStatus
from app.services.cache_service import cache
from app.repositories.lead_repository import LeadRepository
from app.repositories.academy_repository import AcademyRepository

logger = logging.getLogger(__name__)


class LeadManager:
    """
    Gestor de leads con caché integrado y Repository Pattern

    Responsabilidades:
    - Lógica de negocio de leads
    - Actualizar status basado en mensajes
    - Calcular lead scores
    - Gestión de caché de leads

    Nota: Acceso a datos delegado a LeadRepository
    """

    def __init__(self):
        self.lead_repo = LeadRepository()
        self.academy_repo = AcademyRepository()

    def get_or_create(self, phone_number: str, name: str = None) -> int:
        """
        Obtener o crear lead usando Repository Pattern

        Args:
            phone_number: Número de teléfono (normalizado)
            name: Nombre del lead (opcional)

        Returns:
            ID del lead
        """
        # Normalizar teléfono (por si acaso)
        normalized_phone = re.sub(r'[^\d+]', '', phone_number)

        logger.info(f"[LEAD] Buscando lead con teléfono: {normalized_phone}")
        lead = self.lead_repo.find_by_phone(normalized_phone)

        if not lead:
            logger.info(f"[LEAD] No encontrado. Creando nuevo lead con nombre: {name}")

            # Obtener primera academy usando repository
            academy = self.academy_repo.get_first_academy()
            if not academy:
                raise Exception("No hay academy configurada en la base de datos")

            # Crear lead usando repository
            lead = self.lead_repo.create_lead(
                phone=normalized_phone,
                name=name or 'WhatsApp User',
                source='whatsapp',
                academy_id=academy.id
            )

            logger.info(f"[LEAD] Nuevo lead creado - ID: {lead.id}, Nombre: {lead.name}")
        else:
            logger.info(f"[LEAD] Lead encontrado - ID: {lead.id}, Nombre actual: {lead.name}")

            # Si el lead existe pero tiene nombre genérico y ahora tenemos un nombre real, actualizarlo
            if name and name != '' and lead.name in ['WhatsApp User', 'Usuario', None]:
                logger.info(f"[LEAD] Actualizando nombre genérico '{lead.name}' a '{name}'")
                lead = self.lead_repo.update(lead, name=name)

                # Invalidar caché
                cache.invalidate_lead(lead.id)

        return lead.id

    def get_info(self, lead_id: int) -> dict:
        """
        Obtener información del lead (con caché) usando repository

        Args:
            lead_id: ID del lead

        Returns:
            Diccionario con información del lead
        """
        # CACHE: Intentar obtener del caché primero
        cached_info = cache.get_lead_info(lead_id)
        if cached_info:
            logger.debug(f"[CACHE HIT] Lead info para lead_id: {lead_id}")
            return cached_info

        # No está en caché, consultar usando repository
        lead = self.lead_repo.get_by_id(lead_id)

        if lead:
            lead_info = {
                'id': lead.id,
                'phone': lead.phone,
                'name': lead.name,
                'status': lead.status,
                'interest_level': lead.lead_score or 0,
                'source': lead.source or 'whatsapp'
            }

            # CACHE: Guardar en caché
            cache.set_lead_info(lead_id, lead_info)
            logger.debug(f"[CACHE SET] Lead info guardado para lead_id: {lead_id}")

            return lead_info

        return {}

    def update_name(self, lead_id: int, new_name: str) -> bool:
        """
        Actualizar el nombre del lead si es diferente

        Args:
            lead_id: ID del lead
            new_name: Nuevo nombre

        Returns:
            True si se actualizó, False si no
        """
        lead = self.lead_repo.get_by_id(lead_id)

        if not lead or not new_name:
            return False

        old_name = lead.name

        # Solo actualizar si el nombre actual es genérico
        if old_name != new_name and old_name in ['WhatsApp User', 'Usuario', None, '']:
            logger.info(f"[UPDATE] Cambiando nombre de '{old_name}' a '{new_name}' para lead_id: {lead_id}")
            lead = self.lead_repo.update(lead, name=new_name)

            # CACHE: Invalidar caché del lead (ha cambiado)
            cache.invalidate_lead(lead_id)
            logger.debug(f"[CACHE INVALIDATE] Lead {lead_id} actualizado")

            return True
        elif old_name != new_name:
            logger.info(f"[UPDATE] Lead ya tiene nombre '{old_name}', detectado '{new_name}' - no se actualiza")

        return False

    def update_status(self, lead_id: int, message: str) -> bool:
        """
        Actualizar estado del lead basado en el mensaje

        Args:
            lead_id: ID del lead
            message: Mensaje del usuario para detectar intención

        Returns:
            True si se actualizó el status
        """
        msg_lower = message.lower()
        lead = self.lead_repo.get_by_id(lead_id)

        if not lead:
            return False

        status_changed = False

        # Si muestra interés en clase
        if any(word in msg_lower for word in ['agendar', 'clase', 'prueba', 'probar', 'semana']):
            if lead.status != LeadStatus.SCHEDULED:
                lead = self.lead_repo.update(
                    lead,
                    status=LeadStatus.INTERESTED,
                    lead_score=8,
                    last_contact_date=datetime.now()
                )
                status_changed = True
                logger.info(f"[LEAD] Status actualizado a INTERESTED para lead_id: {lead_id}")

        # Si es primera interacción
        elif lead.status == LeadStatus.NEW:
            lead = self.lead_repo.update(
                lead,
                status='contacted',
                last_contact_date=datetime.now()
            )
            status_changed = True
            logger.info(f"[LEAD] Status actualizado a CONTACTED para lead_id: {lead_id}")

        if status_changed:
            # CACHE: Invalidar caché del lead (ha cambiado)
            cache.invalidate_lead(lead_id)
            logger.debug(f"[CACHE INVALIDATE] Lead {lead_id} status actualizado")

        return status_changed

    def calculate_score(self, lead_id: int, message: str) -> int:
        """
        Calcular lead score basado en interacciones

        Args:
            lead_id: ID del lead
            message: Mensaje del usuario

        Returns:
            Score calculado (0-10)
        """
        score = 0
        msg_lower = message.lower()

        # Palabras clave de alto interés
        if 'agendar' in msg_lower or 'reservar' in msg_lower:
            score += 10
        elif 'precio' in msg_lower or 'costo' in msg_lower:
            score += 5
        elif 'horario' in msg_lower:
            score += 5
        elif 'ubicación' in msg_lower or 'donde' in msg_lower:
            score += 3

        return min(score, 10)  # Máximo 10

    def get_by_status(self, status: str) -> list:
        """
        Obtener leads por status

        Args:
            status: Status a filtrar

        Returns:
            Lista de leads
        """
        return self.lead_repo.find_by_status(status)

    def invalidate_cache(self, lead_id: int) -> bool:
        """
        Invalidar caché de un lead específico

        Args:
            lead_id: ID del lead

        Returns:
            True si se invalidó exitosamente
        """
        return cache.invalidate_lead(lead_id)
