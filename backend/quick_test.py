#!/usr/bin/env python3
"""
Test rápido para verificar que todo funciona
"""

import requests
import sqlite3
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

def test_flask_server():
    """Probar que Flask está corriendo"""
    print("\n1️⃣ PROBANDO SERVIDOR FLASK...")
    
    try:
        response = requests.get('http://localhost:5000/health', timeout=2)
        if response.status_code == 200:
            print(f"{Fore.GREEN}✅ Servidor Flask funcionando{Style.RESET_ALL}")
            print(f"   Respuesta: {response.json()}")
            return True
        else:
            print(f"{Fore.RED}❌ Servidor responde pero con error: {response.status_code}{Style.RESET_ALL}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Servidor Flask NO está corriendo{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   Ejecuta: cd backend && python run.py{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        return False

def test_database():
    """Probar que la base de datos existe y tiene datos"""
    print("\n2️⃣ PROBANDO BASE DE DATOS...")
    
    db_path = Path('backend/bjj_academy.db')
    
    if not db_path.exists():
        print(f"{Fore.RED}❌ Base de datos no encontrada en: {db_path}{Style.RESET_ALL}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar tablas
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"{Fore.GREEN}✅ Base de datos conectada - {table_count} tablas{Style.RESET_ALL}")
        
        # Contar leads
        cursor.execute("SELECT COUNT(*) FROM lead")
        lead_count = cursor.fetchone()[0]
        print(f"   Leads: {lead_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Error en BD: {e}{Style.RESET_ALL}")
        return False

def test_webhook():
    """Probar el webhook"""
    print("\n3️⃣ PROBANDO WEBHOOK...")
    
    try:
        # Test GET
        response = requests.get('http://localhost:5000/webhook/whatsapp', timeout=2)
        if response.status_code == 200:
            print(f"{Fore.GREEN}✅ Webhook GET funcionando{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️ Webhook GET status: {response.status_code}{Style.RESET_ALL}")
        
        # Test POST
        test_data = {'Body': 'Test', 'From': 'whatsapp:+123'}
        response = requests.post('http://localhost:5000/webhook/whatsapp', data=test_data, timeout=2)
        if response.status_code == 200:
            print(f"{Fore.GREEN}✅ Webhook POST funcionando{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️ Webhook POST status: {response.status_code}{Style.RESET_ALL}")
        
        return True
        
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ Webhook no disponible: {e}{Style.RESET_ALL}")
        return False

def main():
    print("=" * 50)
    print("TEST RÁPIDO DEL SISTEMA")
    print("=" * 50)
    
    results = {
        'flask': test_flask_server(),
        'database': test_database(),
        'webhook': test_webhook()
    }
    
    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN:")
    print("=" * 50)
    
    if all(results.values()):
        print(f"\n{Fore.GREEN}🎉 TODO FUNCIONANDO! Puedes continuar con el Dashboard{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}⚠️ Algunos componentes necesitan atención:{Style.RESET_ALL}")
        
        if not results['flask']:
            print("   1. Inicia el servidor: cd backend && python run.py")
        if not results['database']:
            print("   2. Revisa la base de datos")
        if not results['webhook']:
            print("   3. El webhook no es crítico para continuar")
    
    print(f"\n{Fore.CYAN}SIGUIENTE PASO: Crear el Dashboard{Style.RESET_ALL}")
    print("¿Listo para continuar? (El simulador funciona sin Twilio)")

if __name__ == "__main__":
    main()