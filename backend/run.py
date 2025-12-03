import logging
import sys
import os
from app import create_app

# Forzar UTF-8 en Windows para evitar errores con emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar logging para ver logs de OpenAI en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Logs a consola
    ]
)

app = create_app()

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
