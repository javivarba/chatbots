// Dashboard JavaScript
let currentSection = 'stats';

function showSection(section) {
    currentSection = section;
    document.getElementById('stats-section').classList.toggle('hidden', section !== 'stats');
    document.getElementById('appointments-section').classList.toggle('hidden', section !== 'appointments');
    
    // Update button styles
    document.getElementById('btn-stats').classList.toggle('bg-blue-100', section === 'stats');
    document.getElementById('btn-appointments').classList.toggle('bg-blue-100', section === 'appointments');
    
    if (section === 'appointments') {
        loadAppointments();
        loadTodayAppointments();
    }
}

async function loadStats() {
    const response = await fetch('/api/stats');
    const data = await response.json();
    
    document.getElementById('stats-container').innerHTML = `
        <div class="bg-white p-6 rounded-lg shadow">
            <div class="text-gray-500 text-sm">Total Leads</div>
            <div class="text-3xl font-bold text-blue-600">${data.total_leads}</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow">
            <div class="text-gray-500 text-sm">Interesados</div>
            <div class="text-3xl font-bold text-green-600">${data.interested}</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow">
            <div class="text-gray-500 text-sm">Agendados</div>
            <div class="text-3xl font-bold text-purple-600">${data.scheduled}</div>
        </div>
        <div class="bg-white p-6 rounded-lg shadow">
            <div class="text-gray-500 text-sm">Conversión</div>
            <div class="text-3xl font-bold text-yellow-600">${data.conversion_rate}%</div>
        </div>
    `;
}

async function loadLeads() {
    const response = await fetch('/api/leads');
    const leads = await response.json();
    
    const tbody = document.getElementById('leads-tbody');
    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center">No hay leads</td></tr>';
        return;
    }
    
    tbody.innerHTML = leads.map(lead => {
        // Formatear última fecha de contacto
        let lastContactDisplay = 'Nunca';
        if (lead.last_contact) {
            const lastDate = new Date(lead.last_contact);
            const now = new Date();
            const diffHours = Math.floor((now - lastDate) / (1000 * 60 * 60));
            
            if (diffHours < 1) {
                lastContactDisplay = 'Hace minutos';
            } else if (diffHours < 24) {
                lastContactDisplay = `Hace ${diffHours}h`;
            } else {
                const diffDays = Math.floor(diffHours / 24);
                if (diffDays === 1) {
                    lastContactDisplay = 'Ayer';
                } else if (diffDays < 7) {
                    lastContactDisplay = `Hace ${diffDays}d`;
                } else {
                    lastContactDisplay = lastDate.toLocaleDateString('es-MX');
                }
            }
        }
        
        // Formatear fuente con icono
        const sourceIcons = {
            'whatsapp': 'WhatsApp',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'web': 'Web'
        };
        const sourceDisplay = sourceIcons[lead.source] || lead.source;
        
        return `
            <tr class="hover:bg-gray-50 border-t">
                <td class="px-6 py-4">${lead.name}</td>
                <td class="px-6 py-4">${lead.phone}</td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 rounded text-xs status-${lead.status}">${lead.status}</span>
                </td>
                <td class="px-6 py-4 text-sm">${sourceDisplay}</td>
                <td class="px-6 py-4 text-sm text-gray-600">${lastContactDisplay}</td>
                <td class="px-6 py-4">${lead.messages}</td>
                <td class="px-6 py-4">
                    <button onclick="viewConversation(${lead.id})" class="text-blue-600">Ver Chat</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function loadAppointments() {
    const response = await fetch('/api/appointments');
    const appointments = await response.json();
    
    const tbody = document.getElementById('appointments-tbody');
    if (appointments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-4 text-center">No hay citas</td></tr>';
        return;
    }
    
    tbody.innerHTML = appointments.map(apt => {
        const dt = new Date(apt.datetime);
        const dateStr = dt.toLocaleDateString('es-MX');
        const timeStr = dt.toLocaleTimeString('es-MX', {hour: '2-digit', minute:'2-digit'});
        
        return `
            <tr class="hover:bg-gray-50 border-t">
                <td class="px-6 py-4">${dateStr} ${timeStr}</td>
                <td class="px-6 py-4">${apt.lead_name}</td>
                <td class="px-6 py-4">${apt.lead_phone}</td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 rounded text-xs status-${apt.status}">${apt.status}</span>
                </td>
                <td class="px-6 py-4">
                    ${apt.status === 'scheduled' ? 
                        `<button onclick="confirmAppointment(${apt.id})" class="text-green-600 mr-2">Confirmar</button>` : ''}
                    <button onclick="cancelAppointment(${apt.id})" class="text-red-600">Cancelar</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function loadTodayAppointments() {
    const response = await fetch('/api/appointments/today');
    const appointments = await response.json();
    
    const container = document.getElementById('today-appointments');
    if (appointments.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No hay citas para hoy</p>';
        return;
    }
    
    container.innerHTML = appointments.map(apt => `
        <div class="border rounded-lg p-4 mb-2 ${apt.confirmed ? 'bg-green-50' : 'bg-yellow-50'}">
            <div class="flex justify-between">
                <div>
                    <p class="font-semibold">${apt.time} - ${apt.lead_name}</p>
                    <p class="text-sm text-gray-600">${apt.lead_phone}</p>
                </div>
                <span class="px-3 py-1 rounded-full text-xs status-${apt.status}">${apt.status}</span>
            </div>
        </div>
    `).join('');
}

async function viewConversation(leadId) {
    const response = await fetch(`/api/leads/${leadId}`);
    const data = await response.json();
    
    const content = document.getElementById('conversation-content');
    content.innerHTML = `
        <div class="mb-4">
            <p class="font-semibold">${data.lead.name}</p>
            <p class="text-sm text-gray-500">${data.lead.phone}</p>
        </div>
        <div class="space-y-4">
            ${data.messages.map(msg => `
                <div class="${msg.sender === 'user' ? 'text-right' : 'text-left'}">
                    <div class="inline-block max-w-xs px-4 py-2 rounded-lg ${
                        msg.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200'
                    }">
                        <p>${msg.content}</p>
                        <p class="text-xs mt-1 opacity-70">${new Date(msg.timestamp).toLocaleString()}</p>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    document.getElementById('conversation-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('conversation-modal').classList.add('hidden');
}

async function confirmAppointment(id) {
    await fetch(`/api/appointments/${id}/confirm`, {method: 'POST'});
    loadAppointments();
    loadTodayAppointments();
}

async function cancelAppointment(id) {
    if (!confirm('¿Cancelar esta cita?')) return;
    await fetch(`/api/appointments/${id}/cancel`, {method: 'POST'});
    loadAppointments();
    loadTodayAppointments();
}

function refreshData() {
    if (currentSection === 'stats') {
        loadStats();
        loadLeads();
    } else {
        loadAppointments();
        loadTodayAppointments();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    refreshData();
    setInterval(refreshData, 10000);
});