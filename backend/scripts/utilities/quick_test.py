# quick_test.py
"""Test simple para verificar OpenAI"""

import os
from dotenv import load_dotenv
load_dotenv()

def test_quick():
    print("🚀 TEST RÁPIDO")
    print("=" * 30)
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        print(f"API Key: {'✅' if api_key and api_key.startswith('sk-') else '❌'}")
        
        if not api_key:
            print("❌ No API key")
            return
            
        client = OpenAI(api_key=api_key)
        
        # Test simple
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres el asistente de BJJ Mingo. HORARIOS: LUNES 12:00 PM, 5:00 PM, 7:15 PM. Responde con horarios exactos."},
                {"role": "user", "content": "¿Horarios de lunes?"}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        result = response.choices[0].message.content
        print(f"\n📝 RESPUESTA:")
        print(result)
        
        if "12:00 PM" in result and "5:00 PM" in result:
            print(f"\n✅ ¡FUNCIONA! OpenAI usa horarios correctos")
        else:
            print(f"\n⚠️ Horarios incorrectos")
            
    except ImportError:
        print("❌ Error: OpenAI no instalado correctamente")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_quick()