"""
API Routes para el Dashboard
"""

from flask import Blueprint, jsonify
import sqlite3
from datetime import datetime

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
    
    # Leads interesados (interest_level >= 7)
    cursor.execute("SELECT COUNT(*) as total FROM lead WHERE interest_level >= 7")
    interested = cursor.fetchone()['total']
    
    # Mensajes totales
    cursor.execute("SELECT COUNT(*) as total FROM message")
    total_messages = cursor.fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'total_leads': total_leads,
        'interested': interested,
        'new': status_counts.get('new', 0),
        'contacted': status_counts.get('contacted', 0),
        'scheduled': status_counts.get('scheduled', 0),
        'total_messages': total_messages,
        'conversion_rate': round((interested / total_leads * 100) if total_leads > 0 else 0, 1)
    })

@dashboard_bp.route('/leads')
def get_leads():
    """Obtener lista de leads"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            l.id,
            l.phone_number,
            l.name,
            l.status,
            l.interest_level,
            l.created_at,
            COUNT(DISTINCT c.id) as conversations,
            COUNT(m.id) as messages
        FROM lead l
        LEFT JOIN conversation c ON l.id = c.lead_id
        LEFT JOIN message m ON c.id = m.conversation_id
        GROUP BY l.id
        ORDER BY l.created_at DESC
    """)
    
    leads = []
    for row in cursor.fetchall():
        leads.append({
            'id': row['id'],
            'phone': row['phone_number'],
            'name': row['name'] or 'Sin nombre',
            'status': row['status'],
            'interest_level': row['interest_level'],
            'created_at': row['created_at'],
            'conversations': row['conversations'],
            'messages': row['messages']
        })
    
    conn.close()
    
    return jsonify(leads)

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
    
    conn.close()
    
    return jsonify({
        'lead': {
            'id': lead['id'],
            'phone': lead['phone_number'],
            'name': lead['name'],
            'status': lead['status'],
            'interest_level': lead['interest_level'],
            'created_at': lead['created_at']
        },
        'messages': messages
    })

@dashboard_bp.route('/leads/<int:lead_id>/update-status', methods=['POST'])
def update_lead_status(lead_id):
    """Actualizar el status de un lead"""
    from flask import request
    
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

@dashboard_bp.route('/appointments/today')
def get_today_appointments():
    """Obtener citas de hoy"""
    from datetime import date
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = date.today().strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT 
            a.*,
            l.name,
            l.phone_number
        FROM appointment a
        JOIN lead l ON a.lead_id = l.id
        WHERE DATE(a.appointment_datetime) = ? 
        AND a.status != 'cancelled'
        ORDER BY a.appointment_time ASC
    """, (today,))
    
    appointments = []
    for row in cursor.fetchall():
        appointments.append({
            'id': row['id'],
            'time': row['appointment_time'],
            'lead_name': row['name'] or 'Sin nombre',
            'lead_phone': row['phone_number'],
            'status': row['status'],
            'confirmed': row['confirmed']
        })
    
    conn.close()
    return jsonify(appointments)

@dashboard_bp.route('/appointments/<int:appointment_id>/confirm', methods=['POST'])
def confirm_appointment(appointment_id):
    """Confirmar una cita"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE appointment 
        SET confirmed = 1, status = 'confirmed' 
        WHERE id = ?
    """, (appointment_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@dashboard_bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancelar una cita"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE appointment 
        SET status = 'cancelled' 
        WHERE id = ?
    """, (appointment_id,))
    
    cursor.execute("""
        UPDATE lead 
        SET status = 'interested' 
        WHERE id = (SELECT lead_id FROM appointment WHERE id = ?)
    """, (appointment_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})
