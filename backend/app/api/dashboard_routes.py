"""
API Routes para el Dashboard - Versión Mejorada
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect('bjj_academy.db')
    conn.row_factory = sqlite3.Row
    return conn

@dashboard_bp.route('/stats')
def get_stats():
    """Obtener estadísticas generales"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de leads
    cursor.execute("SELECT COUNT(*) as total FROM lead")
    total_leads = cursor.fetchone()['total']
    
    # Leads por status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM lead 
        GROUP BY status
    """)
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
    
    # Leads con cita confirmada
    cursor.execute("""
        SELECT COUNT(DISTINCT lead_id) as total 
        FROM appointment 
        WHERE status = 'scheduled' AND confirmed = 1
    """)
    scheduled = cursor.fetchone()['total']
    
    # Leads que necesitan seguimiento (>3 días sin contacto y no agendados)
    cursor.execute("""
        SELECT COUNT(DISTINCT l.id) as total
        FROM lead l
        LEFT JOIN conversation c ON l.id = c.lead_id
        WHERE l.status NOT IN ('scheduled', 'engaged')
        AND (c.last_message_at IS NULL OR 
             julianday('now') - julianday(c.last_message_at) > 3)
    """)
    needs_followup = cursor.fetchone()['total']
    
    # Tasa de conversión (leads agendados / total leads)
    conversion_rate = round((scheduled / total_leads * 100) if total_leads > 0 else 0, 1)
    
    conn.close()
    
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
def get_leads():
    """Obtener lista de leads con información accionable"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener filtros opcionales
    status_filter = request.args.get('status')
    needs_followup = request.args.get('needs_followup') == 'true'
    
    base_query = """
        SELECT 
            l.id,
            l.phone_number,
            l.name,
            l.status,
            l.interest_level,
            l.source,
            l.created_at,
            COUNT(DISTINCT c.id) as conversations,
            COUNT(m.id) as total_messages,
            MAX(c.last_message_at) as last_contact,
            MAX(m.timestamp) as last_message_time,
            (SELECT sender FROM message m2 
             WHERE m2.conversation_id = c.id 
             ORDER BY timestamp DESC LIMIT 1) as last_sender,
            (SELECT appointment_datetime FROM appointment 
             WHERE lead_id = l.id AND status = 'scheduled' 
             ORDER BY created_at DESC LIMIT 1) as next_appointment
        FROM lead l
        LEFT JOIN conversation c ON l.id = c.lead_id
        LEFT JOIN message m ON c.id = m.conversation_id
        WHERE 1=1
    """
    
    params = []
    
    if status_filter:
        base_query += " AND l.status = ?"
        params.append(status_filter)
    
    base_query += """
        GROUP BY l.id
    """
    
    if needs_followup:
        base_query += """
            HAVING (last_contact IS NULL OR 
                    julianday('now') - julianday(last_contact) > 3)
            AND l.status NOT IN ('scheduled', 'engaged')
        """
    
    base_query += " ORDER BY l.created_at DESC"
    
    cursor.execute(base_query, params)
    
    leads = []
    now = datetime.now()
    
    for row in cursor.fetchall():
        # Calcular días sin contacto
        days_since_contact = None
        if row['last_contact']:
            last_contact_dt = datetime.fromisoformat(row['last_contact'])
            days_since_contact = (now - last_contact_dt).days
        
        # Determinar próxima acción sugerida
        next_action = determine_next_action(
            row['status'], 
            row['interest_level'], 
            days_since_contact,
            row['last_sender'],
            row['next_appointment']
        )
        
        leads.append({
            'id': row['id'],
            'phone': row['phone_number'],
            'name': row['name'] or 'Sin nombre',
            'status': row['status'],
            'interest_level': row['interest_level'] or 0,
            'source': row['source'] or 'whatsapp',
            'created_at': row['created_at'],
            'last_contact': row['last_contact'],
            'days_since_contact': days_since_contact,
            'total_messages': row['total_messages'],
            'last_sender': row['last_sender'],
            'next_appointment': row['next_appointment'],
            'next_action': next_action
        })
    
    conn.close()
    
    return jsonify(leads)

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
        if interest_level and interest_level >= 7:
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
    if status == 'interested' and interest_level and interest_level >= 7:
        return {
            'action': 'schedule',
            'label': 'Agendar clase',
            'priority': 'high',
            'icon': '📆'
        }
    
    # Lead nuevo sin mucha interacción
    if status == 'new':
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Información del lead
    cursor.execute("SELECT * FROM lead WHERE id = ?", (lead_id,))
    lead = cursor.fetchone()
    
    if not lead:
        conn.close()
        return jsonify({'error': 'Lead no encontrado'}), 404
    
    # Mensajes del lead
    cursor.execute("""
        SELECT m.*, c.id as conv_id
        FROM message m
        JOIN conversation c ON m.conversation_id = c.id
        WHERE c.lead_id = ?
        ORDER BY m.timestamp ASC
    """, (lead_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            'id': row['id'],
            'sender': row['sender'],
            'content': row['content'],
            'timestamp': row['timestamp'],
            'intent': row['intent_detected']
        })
    
    # Citas del lead
    cursor.execute("""
        SELECT * FROM appointment 
        WHERE lead_id = ? 
        ORDER BY appointment_datetime DESC
    """, (lead_id,))
    
    appointments = []
    for row in cursor.fetchall():
        appointments.append({
            'id': row['id'],
            'datetime': row['appointment_datetime'],
            'status': row['status'],
            'confirmed': row['confirmed']
        })
    
    conn.close()
    
    return jsonify({
        'lead': {
            'id': lead['id'],
            'phone': lead['phone_number'],
            'name': lead['name'],
            'status': lead['status'],
            'interest_level': lead['interest_level'],
            'source': lead['source'],
            'created_at': lead['created_at']
        },
        'messages': messages,
        'appointments': appointments
    })

@dashboard_bp.route('/leads/<int:lead_id>/update-status', methods=['POST'])
def update_lead_status(lead_id):
    """Actualizar el status de un lead"""
    new_status = request.json.get('status')
    if not new_status:
        return jsonify({'error': 'Status requerido'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE lead 
        SET status = ?, updated_at = ? 
        WHERE id = ?
    """, (new_status, datetime.now().isoformat(), lead_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'status': new_status})

@dashboard_bp.route('/leads/<int:lead_id>/add-note', methods=['POST'])
def add_lead_note(lead_id):
    """Agregar nota a un lead"""
    note = request.json.get('note')
    if not note:
        return jsonify({'error': 'Nota requerida'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buscar conversación activa
    cursor.execute("""
        SELECT id FROM conversation 
        WHERE lead_id = ? AND status = 'active'
        LIMIT 1
    """, (lead_id,))
    
    conv = cursor.fetchone()
    if conv:
        conv_id = conv['id']
        cursor.execute("""
            INSERT INTO message (conversation_id, sender, content, intent_detected)
            VALUES (?, 'admin', ?, 'note')
        """, (conv_id, note))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# Rutas de appointments (mantener las existentes)
@dashboard_bp.route('/appointments')
def get_appointments():
    """Obtener todas las citas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            a.id,
            a.appointment_datetime,
            a.status,
            a.confirmed,
            l.name,
            l.phone_number,
            l.id as lead_id
        FROM appointment a
        JOIN lead l ON a.lead_id = l.id
        WHERE a.status != 'cancelled'
        ORDER BY a.appointment_datetime ASC
    """)
    
    appointments = []
    for row in cursor.fetchall():
        appointments.append({
            'id': row['id'],
            'datetime': row['appointment_datetime'],
            'status': row['status'],
            'confirmed': row['confirmed'],
            'lead_name': row['name'] or 'Sin nombre',
            'lead_phone': row['phone_number'],
            'lead_id': row['lead_id']
        })
    
    conn.close()
    return jsonify(appointments)