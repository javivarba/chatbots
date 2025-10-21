# simple_openai_test.py
"""
Test directo de OpenAI sin depender de Flask
"""

import os
from dotenv import load_dotenv

# Cargar .env
load_dotenv(override=True)

def test_openai_direct():
    print("🔍 TEST DIRECTO DE OPENAI")
    print("=" * 50)
    
    # Verificar API key
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API Key: {'✅ Configurada' if api_key and api_key.startswith('sk-') else '❌ No válida'}")
    
    if not api_key or not api_key.startswith('sk-'):
        print("❌ API Key no válida")
        return False
    
    # Test de conexión
    try:
        # Intentar con versión nueva primero
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres el asistente de BJJ Mingo, responde sobre horarios de clases de BJJ"
                    },
                    {
                        "role": "user", 
                        "content": "¿Cuáles son los horarios de clases?"
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            print("✅ OpenAI v1.0+ funcionando")
            
        except ImportError:
            # Fallback a versión antigua
            import openai
            openai.api_key = api_key
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres el asistente de BJJ Mingo, responde sobre horarios de clases de BJJ"
                    },
                    {
                        "role": "user", 
                        "content": "¿Cuáles son los horarios de clases?"
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            print("✅ OpenAI legacy funcionando")
        
        print(f"\n📝 RESPUESTA DE PRUEBA:")
        print("-" * 40)
        print(ai_response)
        print("-" * 40)
        
        print(f"\n✅ SUCCESS: OpenAI está funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_system_prompt():
    """Test con el system prompt completo de BJJ Mingo"""
    print(f"\n🎯 TEST CON SYSTEM PROMPT COMPLETO")
    print("=" * 50)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key")
        return
    
    # System prompt de BJJ Mingo
    system_prompt = """Eres el asistente virtual de BJJ Mingo, una academia de Brazilian Jiu-Jitsu en Santo Domingo de Heredia, Costa Rica.

Academia: BJJ Mingo
Dirección: Santo Domingo de Heredia, Costa Rica

HORARIOS DETALLADOS:

LUNES:
- 12:00 PM - With Gi
- 5:00 PM - Junior
- 7:15 PM - With Gi

MARTES:
- 12:00 PM - Without Gi
- 5:00 PM - Kids
- 6:00 PM - Open
- 7:15 PM - Without Gi

MIÉRCOLES:
- 12:00 PM - With Gi
- 5:00 PM - Junior
- 7:15 PM - With Gi

JUEVES:
- 12:00 PM - Without Gi
- 5:00 PM - Kids
- 6:00 PM - Open
- 7:15 PM - Without Gi

VIERNES:
- 12:00 PM - Open
- 6:00 PM - Open
- 7:00 PM - Open

Precios:
- Mensualidad Adultos: $120
- Mensualidad Niños: $80
- Primera clase: GRATIS

Responde de forma amigable y siempre menciona que la primera clase es GRATIS."""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hola, ¿me puedes decir los horarios de clases y precios?"}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        print(f"📝 RESPUESTA CON PROMPT COMPLETO:")
        print("-" * 40)
        print(ai_response)
        print("-" * 40)
        
        # Verificar que contiene info específica
        checks = [
            ("12:00 PM" in ai_response, "Horario específico"),
            ("With Gi" in ai_response or "Without Gi" in ai_response, "Tipos de clase"),
            ("$120" in ai_response, "Precio adultos"),
            ("GRATIS" in ai_response.upper(), "Primera clase gratis")
        ]
        
        print(f"\n🔍 VERIFICACIONES:")
        for check, description in checks:
            print(f"   {'✅' if check else '❌'} {description}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 TEST COMPLETO DE OPENAI")
    print("=" * 60)
    
    # Test básico
    basic_works = test_openai_direct()
    
    if basic_works:
        # Test con system prompt
        test_system_prompt()
        
        print(f"\n🎉 ¡OpenAI está funcionando correctamente!")
        print(f"El problema estaba en la carga del .env, no en OpenAI.")
    else:
        print(f"\n❌ Hay un problema con OpenAI o la API key")

    print("\n" + "="*60)
    print("Para usar en Flask, asegúrate de que el AIService se inicialice correctamente")