# verify_twilio_setup.py
import os
from pathlib import Path
from twilio.rest import Client

def load_env_smart():
    try:
        from dotenv import load_dotenv, find_dotenv
    except Exception as e:
        print("⚠️  Instala python-dotenv:  python -m pip install python-dotenv")
        raise

    # 1) intenta .env desde CWD y padres
    p = find_dotenv(usecwd=True)
    tried = []
    if p:
        load_dotenv(p); return p

    # 2) intenta .env junto al script
    here = Path(__file__).resolve().parent
    p = here / ".env"
    tried.append(str(p))
    if p.exists():
        load_dotenv(p); return str(p)

    # 3) intenta backend/.env desde CWD
    p = Path.cwd() / "backend" / ".env"
    tried.append(str(p))
    if p.exists():
        load_dotenv(p); return str(p)

    # 4) intenta backend/.env junto al script (si el script está en raíz)
    p = here / "backend" / ".env"
    tried.append(str(p))
    if p.exists():
        load_dotenv(p); return str(p)

    print("❌ No encontré .env en ninguna ruta conocida.")
    print("   Rutas probadas:\n   - " + "\n   - ".join(tried))
    return None

env_path = load_env_smart()

print("\n=== VERIFICACIÓN TWILIO SANDBOX ===\n")

def env(name: str) -> str:
    v = os.getenv(name)
    return v.strip() if v else ""

account_sid = env("TWILIO_ACCOUNT_SID")
auth_token  = env("TWILIO_AUTH_TOKEN")
from_number = env("TWILIO_WHATSAPP_FROM") or "whatsapp:+14155238886"

if not account_sid or not auth_token:
    print("❌ Credenciales no configuradas en .env")
    print("   Configura TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN")
    if env_path:
        print(f"ℹ️  .env cargado desde: {env_path} (revisa el contenido)")
    raise SystemExit(1)

if not account_sid.startswith("AC"):
    print("⚠️  TWILIO_ACCOUNT_SID no parece válido (debe empezar con 'AC').")

print(f"✅ .env cargado desde: {env_path or '(desconocido)'}")
print(f"✅ Account SID: {account_sid[:10]}…")
print(f"✅ Desde (FROM): {from_number}")

try:
    client = Client(account_sid, auth_token)
    me = client.api.accounts(account_sid).fetch()
    print(f"✅ Conexión OK. Cuenta: {getattr(me, 'friendly_name', 'N/A')}")
    print("\n📱 Sandbox:")
    print("1) Agrega +1 415 523 8886 en WhatsApp")
    print("2) Envía el código 'join <tu-código-sandbox>'")
    print("3) Escribe 'Hola' y valida respuesta del bot")
except Exception as e:
    print(f"❌ Error autenticando con Twilio: {e}")
    raise
