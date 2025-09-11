import requests

base_url = 'http://localhost:5000'

print('🔍 Verificando endpoints...\n')

# Endpoint principal
r = requests.get(f'{base_url}/')
print(f'GET /: {r.status_code}')
if r.status_code == 200:
    print(f'Response: {r.json()}\n')

# Health check
r = requests.get(f'{base_url}/health')
print(f'GET /health: {r.status_code}')
if r.status_code == 200:
    print(f'Response: {r.json()}\n')

# Webhook test
r = requests.get(f'{base_url}/webhooks/whatsapp/test')
print(f'GET /webhooks/whatsapp/test: {r.status_code}')
if r.status_code == 200:
    print(f'Response: {r.json()}\n')
