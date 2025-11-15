"""
API Routes para el Dashboard - PostgreSQL con SQLAlchemy
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from app import db
from app.models import Lead, Conversation, Message, MessageDirection, LeadStatus
from sqlalchemy import func, desc

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

@dashboard_bp.route('/stats')
def get_stats():
    """Obtener estadísticas generales"""

    # Total de leads
    total_leads = Lead.query.count()

    # Leads por status
    status_counts = db.session.query(
        Lead.status, func.count(Lead.id)
    ).group_by(Lead.status).all()

    status_dict = {status: count for status, count in status_counts}

    # Leads agendados (con trial_class_date)
    scheduled = Lead.query.filter(Lead.status == LeadStatus.SCHEDULED).count()

    # Leads que necesitan seguimiento (>3 días sin contacto)
    three_days_ago = datetime.now() - timedelta(days=3)
    needs_followup = Lead.query.filter(
        Lead.status.notin_([LeadStatus.SCHEDULED, LeadStatus.CONVERTED]),
        (Lead.last_contact_date == None) | (Lead.last_contact_date < three_days_ago)
    ).count()

    # Tasa de conversión
    conversion_rate = round((scheduled / total_leads * 100) if total_leads > 0 else 0, 1)

    return jsonify({
        'total_leads': total_leads,
        'scheduled': scheduled,
        'needs_followup': needs_followup,
        'new': status_dict.get('new', 0),
        'contacted': status_dict.get('contacted', 0),
        'interested': status_dict.get('interested', 0),
        'conversion_rate': conversion_rate
    })

@dashboard_bp.route('/leads')
def get_leads():
    """Obtener lista de leads con información accionable"""
    status_filter = request.args.get('status')

    # Query base
    query = Lead.query

    if status_filter:
        query = query.filter(Lead.status == status_filter)

    leads_data = []
    now = datetime.now()

    for lead in query.order_by(desc(Lead.created_at)).all():
        # Contar conversaciones y mensajes
        conv_count = Conversation.query.filter_by(lead_id=lead.id).count()

        conversations = Conversation.query.filter_by(lead_id=lead.id).all()
        total_messages = sum(
            Message.query.filter_by(conversation_id=conv.id).count()
            for conv in conversations
        )

        # Última conversación activa
        last_conv = Conversation.query.filter_by(
            lead_id=lead.id,
            is_active=True
        ).order_by(desc(Conversation.last_message_at)).first()

        last_contact = last_conv.last_message_at if last_conv else None

        # Último mensaje
        last_message = None
        last_sender = None
        if last_conv:
            last_message = Message.query.filter_by(
                conversation_id=last_conv.id
            ).order_by(desc(Message.created_at)).first()

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
def get_lead_detail(lead_id):
    """Obtener detalle de un lead específico"""
    lead = Lead.query.get(lead_id)

    if not lead:
        return jsonify({'error': 'Lead no encontrado'}), 404

    # Obtener conversaciones y mensajes
    conversations = Conversation.query.filter_by(lead_id=lead_id).all()

    all_messages = []
    for conv in conversations:
        messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at).all()
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
def update_lead_status(lead_id):
    """Actualizar el status de un lead"""
    new_status = request.json.get('status')
    if not new_status:
        return jsonify({'error': 'Status requerido'}), 400

    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({'error': 'Lead no encontrado'}), 404

    lead.status = new_status
    lead.updated_at = datetime.now()
    db.session.commit()

    return jsonify({'success': True, 'status': new_status})

@dashboard_bp.route('/leads/<int:lead_id>/add-note', methods=['POST'])
def add_lead_note(lead_id):
    """Agregar nota a un lead"""
    note = request.json.get('note')
    if not note:
        return jsonify({'error': 'Nota requerida'}), 400

    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({'error': 'Lead no encontrado'}), 404

    # Buscar conversación activa
    conversation = Conversation.query.filter_by(
        lead_id=lead_id,
        is_active=True
    ).first()

    if conversation:
        # Crear mensaje de nota
        message = Message(
            conversation_id=conversation.id,
            direction=MessageDirection.OUTBOUND,  # Notas admin como outbound
            content=f"[NOTA ADMIN] {note}",
            created_at=datetime.now()
        )
        db.session.add(message)
        db.session.commit()

    return jsonify({'success': True})

@dashboard_bp.route('/appointments')
def get_appointments():
    """Obtener todas las citas (leads con trial_class_date)"""
    leads_with_appointments = Lead.query.filter(
        Lead.trial_class_date != None
    ).order_by(Lead.trial_class_date).all()

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
