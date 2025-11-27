"""
API Routes para el Dashboard - PostgreSQL with SQLAlchemy
Protected with JWT authentication and rate limiting
Refactored with Repository Pattern: 25/11/2025
Pydantic Validation: 25/11/2025
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import limiter
from app.models import MessageDirection, LeadStatus
from app.services.cache_service import cache
from app.repositories.lead_repository import LeadRepository
from app.repositories.conversation_repository import ConversationRepository, MessageRepository
from app.schemas import UpdateLeadStatusRequest, AddLeadNoteRequest, CacheInvalidatePatternRequest, CacheInvalidateKeysRequest
from app.utils.validation import validate_json

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

# Initialize repositories
lead_repo = LeadRepository()
conversation_repo = ConversationRepository()
message_repo = MessageRepository()

@dashboard_bp.route('/stats')
@jwt_required()
def get_stats():
    """Obtener estadísticas generales usando repositories"""

    # Total de leads
    total_leads = lead_repo.count()

    # Leads por status usando repository
    status_counts = lead_repo.count_by_status()

    # Leads agendados
    scheduled = lead_repo.count(status=LeadStatus.SCHEDULED)

    # Leads que necesitan seguimiento usando repository
    needs_followup_leads = lead_repo.find_needs_followup(days=3)
    needs_followup = len(needs_followup_leads)

    # Tasa de conversión
    conversion_rate = round((scheduled / total_leads * 100) if total_leads > 0 else 0, 1)

    return jsonify({
        'total_leads': total_leads,
        'scheduled': scheduled,
        'needs_followup': needs_followup,
        'new': status_counts.get('new', 0),
        'contacted': status_counts.get('contacted', 0),
        'interested': status_counts.get('interested', 0),
        'conversion_rate': conversion_rate
    })

@dashboard_bp.route('/leads')
@jwt_required()
def get_leads():
    """Obtener lista de leads con información accionable usando repositories"""
    status_filter = request.args.get('status')

    # Obtener leads usando repository
    if status_filter:
        leads = lead_repo.find_by_status(status_filter)
    else:
        leads = lead_repo.get_recent_leads(limit=1000)  # Ajustar límite según necesidad

    leads_data = []
    now = datetime.now()

    for lead in leads:
        # Obtener conversaciones usando repository
        conversations = conversation_repo.find_by_lead(lead.id)

        # Contar mensajes
        total_messages = sum(
            message_repo.count_messages_in_conversation(conv.id)
            for conv in conversations
        )

        # Última conversación activa usando repository
        last_conv = conversation_repo.find_active_conversation(lead.id)
        last_contact = last_conv.last_message_at if last_conv else None

        # Último mensaje usando repository
        last_message = None
        last_sender = None
        if last_conv:
            last_message = message_repo.get_last_message(last_conv.id)

            if last_message:
                last_sender = 'user' if last_message.direction == MessageDirection.INBOUND else 'bot'

        # Días sin contacto
        days_since_contact = None
        if last_contact:
            days_since_contact = (now - last_contact).days

        # Determinar próxima acción
        next_action = determine_next_action(
            lead.status,
            lead.lead_score or 0,
            days_since_contact,
            last_sender,
            lead.trial_class_date
        )

        leads_data.append({
            'id': lead.id,
            'phone': lead.phone,
            'name': lead.name or 'Sin nombre',
            'status': lead.status,
            'interest_level': lead.lead_score or 0,
            'source': lead.source or 'whatsapp',
            'created_at': lead.created_at.isoformat() if lead.created_at else None,
            'last_contact': last_contact.isoformat() if last_contact else None,
            'days_since_contact': days_since_contact,
            'total_messages': total_messages,
            'last_sender': last_sender,
            'next_appointment': lead.trial_class_date.isoformat() if lead.trial_class_date else None,
            'next_action': next_action
        })

    return jsonify(leads_data)

def determine_next_action(status, interest_level, days_since_contact, last_sender, next_appointment):
    """Determinar la próxima acción sugerida para un lead"""

    # Si ya tiene cita, solo confirmar
    if next_appointment:
        return {
            'action': 'confirm_appointment',
            'label': 'Confirmar cita',
            'priority': 'high',
            'icon': '📅'
        }

    # Si el último mensaje fue del usuario y no respondimos
    if last_sender == 'user':
        return {
            'action': 'respond',
            'label': 'Responder mensaje',
            'priority': 'urgent',
            'icon': '💬'
        }

    # Si lleva más de 3 días sin contacto
    if days_since_contact and days_since_contact > 3:
        if interest_level >= 7:
            return {
                'action': 'followup_hot',
                'label': 'Seguimiento (Lead caliente)',
                'priority': 'high',
                'icon': '🔥'
            }
        else:
            return {
                'action': 'followup',
                'label': 'Hacer seguimiento',
                'priority': 'medium',
                'icon': '📞'
            }

    # Si está interesado pero no ha agendado
    if status == LeadStatus.INTERESTED and interest_level >= 7:
        return {
            'action': 'schedule',
            'label': 'Agendar clase',
            'priority': 'high',
            'icon': '📆'
        }

    # Lead nuevo sin mucha interacción
    if status == LeadStatus.NEW:
        return {
            'action': 'initial_contact',
            'label': 'Contactar',
            'priority': 'medium',
            'icon': '👋'
        }

    # Por defecto
    return {
        'action': 'monitor',
        'label': 'Monitorear',
        'priority': 'low',
        'icon': '👁️'
    }

@dashboard_bp.route('/leads/<int:lead_id>')
@jwt_required()
def get_lead_detail(lead_id):
    """Obtener detalle de un lead específico usando repositories"""
    lead = lead_repo.get_by_id(lead_id)

    if not lead:
        return jsonify({'error': 'Lead no encontrado'}), 404

    # Obtener conversaciones y mensajes usando repositories
    conversations = conversation_repo.find_by_lead(lead_id)

    all_messages = []
    for conv in conversations:
        messages = message_repo.find_by_conversation(conv.id)
        for msg in messages:
            all_messages.append({
                'id': msg.id,
                'sender': 'user' if msg.direction == MessageDirection.INBOUND else 'bot',
                'content': msg.content,
                'timestamp': msg.created_at.isoformat() if msg.created_at else None,
                'intent': None  # Podemos agregar esto después si es necesario
            })

    return jsonify({
        'lead': {
            'id': lead.id,
            'phone': lead.phone,
            'name': lead.name,
            'status': lead.status,
            'interest_level': lead.lead_score or 0,
            'source': lead.source,
            'created_at': lead.created_at.isoformat() if lead.created_at else None
        },
        'messages': all_messages,
        'appointments': []  # Podemos agregar modelo de appointments después
    })

@dashboard_bp.route('/leads/<int:lead_id>/update-status', methods=['POST'])
@limiter.limit("30 per minute")  # Limitar actualizaciones de status
@jwt_required()
@validate_json(UpdateLeadStatusRequest)  # ✅ Validación automática con Pydantic
def update_lead_status(validated_data: UpdateLeadStatusRequest, lead_id):
    """
    Actualizar el status de un lead usando repository

    Request Body (validado con Pydantic):
        {
            "status": "interested"  # new|contacted|interested|scheduled|converted|lost
        }
    """
    # Datos ya validados por Pydantic
    new_status = validated_data.status  # Ya validado contra enum

    lead = lead_repo.get_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead no encontrado'}), 404

    # Actualizar status usando repository
    lead = lead_repo.update_status(lead, new_status)

    return jsonify({'success': True, 'status': new_status})

@dashboard_bp.route('/leads/<int:lead_id>/add-note', methods=['POST'])
@limiter.limit("20 per minute")  # Limitar creación de notas
@jwt_required()
@validate_json(AddLeadNoteRequest)  # ✅ Validación automática con Pydantic
def add_lead_note(validated_data: AddLeadNoteRequest, lead_id):
    """
    Agregar nota a un lead usando repositories

    Request Body (validado con Pydantic):
        {
            "note": "Cliente muy interesado"  # 1-1000 chars, sanitizado para XSS
        }
    """
    # Datos ya validados y sanitizados por Pydantic
    note = validated_data.note  # Ya sanitizado (HTML escapado)

    lead = lead_repo.get_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead no encontrado'}), 404

    # Buscar conversación activa usando repository
    conversation = conversation_repo.find_active_conversation(lead_id)

    if conversation:
        # Crear mensaje de nota usando repository
        message_repo.create_message(
            conversation_id=conversation.id,
            content=f"[NOTA ADMIN] {note}",
            direction=MessageDirection.OUTBOUND
        )

    return jsonify({'success': True})

@dashboard_bp.route('/appointments')
@jwt_required()
def get_appointments():
    """Obtener todas las citas (leads con trial_class_date) usando repositories"""
    leads_with_appointments = lead_repo.find_scheduled_leads()

    appointments = []
    for lead in leads_with_appointments:
        appointments.append({
            'id': lead.id,
            'datetime': lead.trial_class_date.isoformat() if lead.trial_class_date else None,
            'status': lead.status,
            'confirmed': lead.status == LeadStatus.SCHEDULED,
            'lead_name': lead.name or 'Sin nombre',
            'lead_phone': lead.phone,
            'lead_id': lead.id
        })

    return jsonify(appointments)

@dashboard_bp.route('/cache/stats')
@jwt_required()
def get_cache_stats():
    """Obtener estadísticas del sistema de caché"""
    try:
        stats = cache.get_stats()
        return jsonify({
            'success': True,
            'cache': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/cache/clear', methods=['POST'])
@limiter.limit("10 per hour")  # Operación sensible, limitar fuertemente
@jwt_required()
def clear_cache():
    """
    Limpiar caché - opciones:
    - all: Limpiar todo el caché (PELIGROSO)
    - pattern: Limpiar llaves que coincidan con patrón (ej: "lead:*")
    - keys: Lista de llaves específicas a eliminar
    Rate Limit: 10 por hora (operación sensible)

    Request Body:
        {
            "action": "pattern",  # all|pattern|keys
            "pattern": "lead:*",  # Si action=pattern
            "keys": ["lead:1", "lead:2"]  # Si action=keys
        }
    """
    try:
        # Obtener action sin validación estricta para compatibilidad
        action = request.json.get('action', 'pattern') if request.is_json else 'pattern'

        if action == 'all':
            # PELIGRO: Limpiar todo
            success = cache.clear_all()
            return jsonify({
                'success': success,
                'message': 'Caché completamente limpiado' if success else 'Error limpiando caché'
            })

        elif action == 'pattern':
            pattern = request.json.get('pattern') if request.is_json else None
            if not pattern:
                return jsonify({'success': False, 'error': 'Patrón requerido'}), 400

            # Validación básica del patrón (sin Pydantic por compatibilidad)
            import re
            if not re.match(r'^[a-zA-Z0-9:_*\-]+$', pattern):
                return jsonify({'success': False, 'error': 'Patrón contiene caracteres no permitidos'}), 400

            count = cache.delete_pattern(pattern)
            return jsonify({
                'success': True,
                'message': f'{count} llaves eliminadas',
                'count': count
            })

        elif action == 'keys':
            keys = request.json.get('keys', []) if request.is_json else []
            if not keys:
                return jsonify({'success': False, 'error': 'Lista de llaves requerida'}), 400

            count = 0
            for key in keys:
                if cache.delete(key):
                    count += 1

            return jsonify({
                'success': True,
                'message': f'{count} llaves eliminadas',
                'count': count
            })

        else:
            return jsonify({'success': False, 'error': 'Acción inválida'}), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/cache/invalidate/lead/<int:lead_id>', methods=['POST'])
@limiter.limit("60 per minute")  # Limitar invalidaciones de caché
@jwt_required()
def invalidate_lead_cache(lead_id):
    """Invalidar caché de un lead específico"""
    try:
        success = cache.invalidate_lead(lead_id)
        return jsonify({
            'success': success,
            'message': f'Caché del lead {lead_id} invalidado' if success else 'Error invalidando caché'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/cache/invalidate/conversation/<int:conv_id>', methods=['POST'])
@limiter.limit("60 per minute")  # Limitar invalidaciones de caché
@jwt_required()
def invalidate_conversation_cache(conv_id):
    """Invalidar caché de una conversación específica"""
    try:
        success = cache.invalidate_conversation(conv_id)
        return jsonify({
            'success': success,
            'message': f'Caché de la conversación {conv_id} invalidado' if success else 'Error invalidando caché'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
