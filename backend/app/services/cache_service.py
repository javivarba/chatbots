"""
Cache Service - Redis-based caching layer
Optimiza rendimiento cacheando:
- Información de la academia
- Historial de conversaciones
- Respuestas frecuentes de OpenAI
- Datos de leads
"""

import os
import json
import redis
import logging
import hashlib
from typing import Optional, Any, Dict, List
from datetime import timedelta
from functools import wraps
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class CacheService:
    """
    Servicio de caché usando Redis
    Implementa patrones de cache-aside y TTL configurable
    """

    # TTL por defecto (en segundos)
    DEFAULT_TTL = 3600  # 1 hora

    # TTL específicos por tipo de dato
    TTL_ACADEMY_INFO = 86400  # 24 horas (raramente cambia)
    TTL_LEAD_INFO = 1800  # 30 minutos
    TTL_CONVERSATION_HISTORY = 300  # 5 minutos
    TTL_AI_RESPONSE = 3600  # 1 hora (para preguntas frecuentes)
    TTL_SYSTEM_PROMPT = 86400  # 24 horas

    def __init__(self):
        """Inicializa conexión con Redis"""
        self.enabled = False
        self.client = None

        try:
            redis_url = os.getenv('REDIS_URL')

            if not redis_url:
                logger.warning("⚠️ REDIS_URL no configurada - caché deshabilitado")
                return

            # Configuración de reintentos para Redis Cloud
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,  # Decodificar strings automáticamente
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )

            # Test de conexión
            self.client.ping()
            self.enabled = True

            logger.info("✅ CacheService inicializado correctamente")
            logger.info(f"   Redis URL: {redis_url[:30]}...")

        except redis.ConnectionError as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Error inicializando CacheService: {e}")
            self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del caché

        Args:
            key: Llave del caché

        Returns:
            Valor deserializado o None si no existe
        """
        if not self.enabled:
            return None

        try:
            value = self.client.get(key)

            if value:
                logger.debug(f"[CACHE HIT] {key}")
                return json.loads(value)

            logger.debug(f"[CACHE MISS] {key}")
            return None

        except redis.ConnectionError:
            logger.warning(f"[CACHE ERROR] Conexión perdida al obtener: {key}")
            return None
        except json.JSONDecodeError:
            logger.error(f"[CACHE ERROR] Error deserializando: {key}")
            return None
        except Exception as e:
            logger.error(f"[CACHE ERROR] Error obteniendo {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Guardar valor en caché

        Args:
            key: Llave del caché
            value: Valor a guardar (será serializado a JSON)
            ttl: Tiempo de vida en segundos (None = DEFAULT_TTL)

        Returns:
            True si se guardó exitosamente
        """
        if not self.enabled:
            return False

        try:
            ttl = ttl or self.DEFAULT_TTL
            serialized = json.dumps(value, default=str)  # default=str para datetime

            self.client.setex(key, ttl, serialized)
            logger.debug(f"[CACHE SET] {key} (TTL: {ttl}s)")
            return True

        except redis.ConnectionError:
            logger.warning(f"[CACHE ERROR] Conexión perdida al guardar: {key}")
            return False
        except TypeError as e:
            logger.error(f"[CACHE ERROR] Error serializando {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"[CACHE ERROR] Error guardando {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Eliminar valor del caché

        Args:
            key: Llave a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        if not self.enabled:
            return False

        try:
            self.client.delete(key)
            logger.debug(f"[CACHE DELETE] {key}")
            return True

        except Exception as e:
            logger.error(f"[CACHE ERROR] Error eliminando {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Eliminar todas las llaves que coincidan con el patrón

        Args:
            pattern: Patrón de búsqueda (ej: "lead:*")

        Returns:
            Número de llaves eliminadas
        """
        if not self.enabled:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                count = self.client.delete(*keys)
                logger.debug(f"[CACHE DELETE PATTERN] {pattern}: {count} llaves")
                return count
            return 0

        except Exception as e:
            logger.error(f"[CACHE ERROR] Error eliminando patrón {pattern}: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        PELIGRO: Eliminar TODO el caché
        Usar solo para testing o mantenimiento

        Returns:
            True si se limpió exitosamente
        """
        if not self.enabled:
            return False

        try:
            self.client.flushdb()
            logger.warning("[CACHE] ⚠️ Base de datos limpiada completamente")
            return True

        except Exception as e:
            logger.error(f"[CACHE ERROR] Error limpiando base de datos: {e}")
            return False

    # ========== MÉTODOS DE ALTO NIVEL ==========

    def get_academy_info(self) -> Optional[Dict]:
        """Obtener información de la academia del caché"""
        return self.get("academy:info")

    def set_academy_info(self, info: Dict) -> bool:
        """Guardar información de la academia en caché"""
        return self.set("academy:info", info, self.TTL_ACADEMY_INFO)

    def get_lead_info(self, lead_id: int) -> Optional[Dict]:
        """Obtener información de un lead del caché"""
        return self.get(f"lead:{lead_id}")

    def set_lead_info(self, lead_id: int, info: Dict) -> bool:
        """Guardar información de un lead en caché"""
        return self.set(f"lead:{lead_id}", info, self.TTL_LEAD_INFO)

    def invalidate_lead(self, lead_id: int) -> bool:
        """Invalidar caché de un lead (cuando se actualiza)"""
        return self.delete(f"lead:{lead_id}")

    def get_conversation_history(self, conv_id: int) -> Optional[List[Dict]]:
        """Obtener historial de conversación del caché"""
        return self.get(f"conversation:{conv_id}:history")

    def set_conversation_history(self, conv_id: int, history: List[Dict]) -> bool:
        """Guardar historial de conversación en caché"""
        return self.set(f"conversation:{conv_id}:history", history, self.TTL_CONVERSATION_HISTORY)

    def invalidate_conversation(self, conv_id: int) -> bool:
        """Invalidar caché de una conversación (cuando hay nuevo mensaje)"""
        return self.delete(f"conversation:{conv_id}:history")

    def get_ai_response(self, query_hash: str) -> Optional[str]:
        """
        Obtener respuesta de IA del caché

        Args:
            query_hash: Hash del mensaje + contexto

        Returns:
            Respuesta cacheada o None
        """
        return self.get(f"ai:response:{query_hash}")

    def set_ai_response(self, query_hash: str, response: str) -> bool:
        """Guardar respuesta de IA en caché"""
        return self.set(f"ai:response:{query_hash}", response, self.TTL_AI_RESPONSE)

    def get_system_prompt(self) -> Optional[str]:
        """Obtener system prompt del caché"""
        return self.get("ai:system_prompt")

    def set_system_prompt(self, prompt: str) -> bool:
        """Guardar system prompt en caché"""
        return self.set("ai:system_prompt", prompt, self.TTL_SYSTEM_PROMPT)

    @staticmethod
    def generate_query_hash(message: str, context: Dict) -> str:
        """
        Generar hash único para una query de IA
        Usado para cachear respuestas similares

        Args:
            message: Mensaje del usuario
            context: Contexto (lead_id, conversation_state, etc)

        Returns:
            Hash MD5 como string
        """
        # Normalizar mensaje (lowercase, sin espacios extra)
        normalized_msg = ' '.join(message.lower().strip().split())

        # Crear string combinado
        combined = f"{normalized_msg}|{json.dumps(context, sort_keys=True)}"

        # Generar hash
        return hashlib.md5(combined.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del caché

        Returns:
            Diccionario con métricas
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self.client.info()

            return {
                "enabled": True,
                "total_keys": self.client.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }

        except Exception as e:
            logger.error(f"[CACHE ERROR] Error obteniendo estadísticas: {e}")
            return {"enabled": True, "error": str(e)}

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> str:
        """Calcular tasa de aciertos del caché"""
        total = hits + misses
        if total == 0:
            return "0%"
        return f"{(hits / total * 100):.2f}%"


# Instancia global del servicio de caché
cache = CacheService()


# ========== DECORADORES ==========

def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorador para cachear resultados de funciones

    Args:
        ttl: Tiempo de vida del caché (None = default)
        key_prefix: Prefijo para la llave del caché

    Ejemplo:
        @cached(ttl=300, key_prefix="academy")
        def get_academy_data():
            return expensive_db_query()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar llave de caché
            func_name = func.__name__
            args_str = str(args) + str(sorted(kwargs.items()))
            cache_key = f"{key_prefix}:{func_name}:{hashlib.md5(args_str.encode()).hexdigest()}"

            # Intentar obtener del caché
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Ejecutar función
            result = func(*args, **kwargs)

            # Guardar en caché
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
