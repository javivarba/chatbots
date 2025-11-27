"""
Conversation Manager - Gestión de Conversaciones y Mensajes
Responsabilidad única: CRUD y lógica de conversaciones
Refactored with Repository Pattern: 25/11/2025
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.models import MessageDirection
from app.services.cache_service import cache
from app.repositories.conversation_repository import ConversationRepository, MessageRepository
from app.repositories.lead_repository import LeadRepository
from app.repositories.academy_repository import AcademyRepository

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Gestor de conversaciones y mensajes con caché integrado

    Responsabilidades:
    - Crear y obtener conversaciones
    - Guardar mensajes
    - Obtener historial de conversaciones
    - Gestión de caché de conversaciones
    """

    def __init__(self):
        self.conversation_repo = ConversationRepository()
        self.message_repo = MessageRepository()
        self.lead_repo = LeadRepository()
        self.academy_repo = AcademyRepository()

    def get_or_create(self, lead_id: int) -> int:
        """
        Obtener o crear conversación activa para un lead

        Args:
            lead_id: ID del lead

        Returns:
            ID de la conversación
        """
        logger.info(f"[CONVERSATION] Buscando conversación activa para lead_id: {lead_id}")

        conversation = self.conversation_repo.find_active_conversation(lead_id)

        if not conversation:
            logger.info(f"[CONVERSATION] No encontrada. Creando nueva conversación para lead_id: {lead_id}")

            lead = self.lead_repo.get_by_id(lead_id)
            if not lead:
                raise Exception(f"Lead {lead_id} no encontrado")

            conversation = self.conversation_repo.create(
                lead_id=lead_id,
                academy_id=lead.academy_id,
                platform='whatsapp',
                is_active=True,
                message_count=0,
                inbound_count=0,
                outbound_count=0,
                started_at=datetime.now(),
                last_message_at=datetime.now()
            )

            logger.info(f"[CONVERSATION] Nueva conversación creada - ID: {conversation.id}")
        else:
            logger.info(f"[CONVERSATION] Conversación encontrada - ID: {conversation.id}, Mensajes: {conversation.message_count}")

        return conversation.id

    def save_message(
        self,
        conversation_id: int,
        direction: MessageDirection,
        content: str,
        intent: Optional[str] = None
    ) -> int:
        """
        Guardar mensaje en la conversación

        Args:
            conversation_id: ID de la conversación
            direction: Dirección del mensaje (INBOUND/OUTBOUND)
            content: Contenido del mensaje
            intent: Intención detectada (opcional)

        Returns:
            ID del mensaje guardado
        """
        message = self.message_repo.create_message(
            conversation_id=conversation_id,
            direction=direction,
            content=content
        )

        # Actualizar conversation
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if conversation:
            update_data = {
                'message_count': conversation.message_count + 1,
                'last_message_at': datetime.now()
            }

            if direction == MessageDirection.INBOUND:
                update_data['inbound_count'] = conversation.inbound_count + 1
                logger.debug(f"[MESSAGE] Guardando mensaje INBOUND en conversación {conversation_id}")
            else:
                update_data['outbound_count'] = conversation.outbound_count + 1
                logger.debug(f"[MESSAGE] Guardando mensaje OUTBOUND en conversación {conversation_id}")

            self.conversation_repo.update(conversation, **update_data)

        # CACHE: Invalidar caché del historial de conversación (ha cambiado)
        cache.invalidate_conversation(conversation_id)
        logger.debug(f"[CACHE INVALIDATE] Historial de conversación {conversation_id}")

        return message.id

    def get_history(self, conversation_id: int, limit: int = 5) -> List[Dict]:
        """
        Obtener historial de conversación (con caché)

        Args:
            conversation_id: ID de la conversación
            limit: Número máximo de mensajes a obtener

        Returns:
            Lista de mensajes en orden cronológico
        """
        logger.info(f"[HISTORY] Obteniendo últimos {limit} mensajes de conversación ID: {conversation_id}")

        # CACHE: Intentar obtener del caché primero
        cached_history = cache.get_conversation_history(conversation_id)
        if cached_history:
            logger.info(f"[CACHE HIT] Historial encontrado en caché ({len(cached_history)} mensajes)")
            return cached_history

        # No está en caché, consultar usando repository
        messages = self.message_repo.get_conversation_history(conversation_id, limit)

        logger.info(f"[HISTORY] Encontrados {len(messages)} mensajes en DB")

        history = []
        for msg in messages:
            sender = 'user' if msg.direction == MessageDirection.INBOUND else 'assistant'
            history.append({
                'sender': sender,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat() if msg.created_at else None
            })
            logger.debug(f"[HISTORY] - {sender}: {msg.content[:50]}...")

        # Invertir para orden cronológico
        history.reverse()

        # CACHE: Guardar en caché
        cache.set_conversation_history(conversation_id, history)
        logger.info(f"[CACHE SET] Historial guardado en caché")

        return history

    def get_message_count(self, conversation_id: int) -> int:
        """
        Obtener cantidad de mensajes en una conversación

        Args:
            conversation_id: ID de la conversación

        Returns:
            Cantidad de mensajes
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        return conversation.message_count if conversation else 0

    def close_conversation(self, conversation_id: int) -> bool:
        """
        Cerrar una conversación (marcarla como inactiva)

        Args:
            conversation_id: ID de la conversación

        Returns:
            True si se cerró exitosamente
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)

        if conversation:
            self.conversation_repo.update(
                conversation,
                is_active=False,
                ended_at=datetime.now()
            )

            # Invalidar caché
            cache.invalidate_conversation(conversation_id)

            logger.info(f"[CONVERSATION] Conversación {conversation_id} cerrada")
            return True

        return False

    def get_active_conversations(self, lead_id: int) -> list:
        """
        Obtener todas las conversaciones activas de un lead

        Args:
            lead_id: ID del lead

        Returns:
            Lista de conversaciones activas
        """
        return self.conversation_repo.find_by(
            lead_id=lead_id,
            is_active=True
        )

    def invalidate_cache(self, conversation_id: int) -> bool:
        """
        Invalidar caché de una conversación específica

        Args:
            conversation_id: ID de la conversación

        Returns:
            True si se invalidó exitosamente
        """
        return cache.invalidate_conversation(conversation_id)

    def get_academy_info(self) -> Dict:
        """
        Obtener información de la academia (con caché)

        Returns:
            Diccionario con información de la academia
        """
        # CACHE: Intentar obtener del caché primero
        cached_info = cache.get_academy_info()
        if cached_info:
            logger.debug(f"[CACHE HIT] Academy info")
            return cached_info

        # No está en caché, consultar usando repository
        academy = self.academy_repo.get_first_academy()

        if academy:
            academy_info = {
                'name': academy.name,
                'description': academy.description or 'Academia de Brazilian Jiu-Jitsu',
                'instructor': academy.instructor_name or 'Instructores certificados',
                'phone': academy.phone,
                'location': f"{academy.address_street}, {academy.address_city}" if academy.address_street else 'Santo Domingo de Heredia, Costa Rica'
            }

            # CACHE: Guardar en caché
            cache.set_academy_info(academy_info)
            logger.debug(f"[CACHE SET] Academy info guardado")

            return academy_info

        return {'name': 'BJJ Mingo', 'phone': '+506-8888-8888'}
