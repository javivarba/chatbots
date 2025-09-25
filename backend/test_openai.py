# test_openai.py
import os
import sys
from openai import OpenAI

try:
    # 1) Cargar .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception as e:
        print(f"⚠️  No se pudo cargar .env automáticamente: {e}")

    # 2) Leer la API key
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        print("❌ API Key no configurada (OPENAI_API_KEY vacío o ausente en .env)")
        sys.exit(1)

    # 3) Cliente y ping rápido
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # modelo vigente
        messages=[{"role": "user", "content": "Di hola en 5 palabras"}],
        max_tokens=20,
        temperature=0
    )
    print(f"✅ OpenAI funcionando: {resp.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error al invocar OpenAI: {e}")
    raise