"""
Script para debuggear el problema de OpenAI
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_openai_config():
    """Verificar configuración de OpenAI"""
    print("🔍 VERIFICANDO CONFIGURACIÓN OPENAI")
    print("=" * 50)
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    print(f"API Key en .env: {api_key[:20] + '...' if api_key else 'NO CONFIGURADA'}")
    
    if not api_key:
        print("❌ OPENAI_API_KEY no está en el archivo .env")
        return False
    
    if api_key == 'sk-your-openai-api-key-here':
        print("❌ OPENAI_API_KEY tiene valor por defecto")
        return False
    
    if not api_key.startswith('sk-'):
        print("❌ OPENAI_API_KEY no tiene formato válido")
        return False
    
    print("✅ OPENAI_API_KEY parece válida")
    
    # Test de conexión
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Test simple
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hola"}],
            max_tokens=10
        )
        
        print("✅ Conexión exitosa con OpenAI")
        print(f"Respuesta de prueba: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a OpenAI: {e}")
        return False

def test_ai_service():
    """Probar el AIService directamente"""
    print("\n🤖 PROBANDO AI SERVICE")
    print("=" * 50)
    
    try:
        from app import create_app
        from app.services.ai_service import AIService
        from app.models import Academy, Lead, Conversation
        
        app = create_app('default')
        with app.app_context():
            # Inicializar servicio
            ai_service = AIService()
            
            print(f"AI Service habilitado: {ai_service.enabled}")
            
            if not ai_service.enabled:
                print("❌ AIService no está habilitado")
                return False
            
            # Obtener datos de prueba
            academy = Academy.query.first()
            lead = Lead.query.first()
            conversation = Conversation.query.first()
            
            if not academy:
                print("❌ No hay academias en la BD")
                return False
            
            print(f"✅ Academia encontrada: {academy.name if hasattr(academy, 'name') else 'BJJ Mingo'}")
            
            # Test de respuesta
            test_message = "¿Cuáles son los horarios de clases?"
            
            response = ai_service.generate_response(
                message=test_message,
                lead=lead or type('obj', (object,), {'name': 'Test', 'phone': '+506', 'status': 'new', 'source': 'whatsapp'}),
                conversation=conversation or type('obj', (object,), {'id': 1}),
                academy=academy,
                use_history=False
            )
            
            print(f"✅ Respuesta generada:")
            print(f"'{response[:200]}...'")
            
            # Verificar si contiene horarios correctos
            if "12:00 PM" in response or "With Gi" in response:
                print("✅ La respuesta contiene horarios específicos")
            else:
                print("⚠ La respuesta no contiene horarios detallados")
            
            return True
            
    except Exception as e:
        print(f"❌ Error probando AIService: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DIAGNÓSTICO OPENAI - BJJ MINGO BOT")
    print("=" * 60)
    
    # 1. Verificar configuración
    config_ok = check_openai_config()
    
    if config_ok:
        # 2. Probar AI Service
        service_ok = test_ai_service()
        
        if service_ok:
            print("\n🎉 TODO FUNCIONANDO CORRECTAMENTE")
        else:
            print("\n❌ Problema con AIService")
    else:
        print("\n❌ Problema con configuración de OpenAI")
        print("\n🔧 SOLUCIÓN:")
        print("1. Ve a https://platform.openai.com/api-keys")
        print("2. Crea una nueva API key")
        print("3. Actualiza tu archivo .env:")
        print("   OPENAI_API_KEY=sk-tu-nueva-key-aqui")