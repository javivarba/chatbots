-- Tabla para trackear recordatorios enviados
-- Evita duplicados y permite saber qué mensajes se han enviado

CREATE TABLE IF NOT EXISTS class_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    appointment_id INTEGER,
    trial_week_id INTEGER,
    clase_tipo TEXT NOT NULL,
    class_datetime TEXT NOT NULL,
    reminder_sent_at TEXT,
    reminder_status TEXT DEFAULT 'pending',  -- pending, sent, failed
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (trial_week_id) REFERENCES trial_weeks(id)
);

-- Índice para búsquedas rápidas por fecha de clase
CREATE INDEX IF NOT EXISTS idx_class_datetime ON class_reminders(class_datetime, reminder_status);

-- Índice para búsquedas por lead
CREATE INDEX IF NOT EXISTS idx_lead_reminders ON class_reminders(lead_id);
