import os
from datetime import datetime

print("\n=== CÁLCULO DE COSTOS OPENAI ===\n")

# Estimaciones
mensajes_por_conversacion = 10
conversaciones_por_dia = 50
dias_por_mes = 30

# Costos (GPT-3.5-turbo)
tokens_promedio_por_mensaje = 676  # Basado en tu test
costo_por_1k_tokens = 0.002

# Cálculos
tokens_por_dia = tokens_promedio_por_mensaje * mensajes_por_conversacion * conversaciones_por_dia
tokens_por_mes = tokens_por_dia * dias_por_mes
costo_por_dia = (tokens_por_dia / 1000) * costo_por_1k_tokens
costo_por_mes = costo_por_dia * dias_por_mes

print(f"Proyección de uso:")
print(f"• Conversaciones/día: {conversaciones_por_dia}")
print(f"• Mensajes/conversación: {mensajes_por_conversacion}")
print(f"• Tokens/día: {tokens_por_dia:,}")
print(f"• Tokens/mes: {tokens_por_mes:,}")
print(f"\nCostos estimados:")
print(f"• Por día: ${costo_por_dia:.2f}")
print(f"• Por mes: ${costo_por_mes:.2f}")
print(f"\nPara 1 academia: ${costo_por_mes:.2f}/mes")
print(f"Para 10 academias: ${costo_por_mes * 10:.2f}/mes")
