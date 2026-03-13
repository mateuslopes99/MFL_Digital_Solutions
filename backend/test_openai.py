"""
MFL Digital Solutions — Teste de Chave OpenAI
Execute: python backend/test_openai.py
"""
import os
import sys
from dotenv import load_dotenv

# Carregar .env da raiz do projeto
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

api_key = os.getenv("OPENAI_API_KEY", "")

if not api_key or api_key.startswith("sk-..."):
    print("❌ ERRO: Chave OpenAI não configurada no .env")
    print("   Edite o arquivo .env e substitua 'sk-...' pela sua chave real.")
    sys.exit(1)

print(f"🔑 Chave encontrada: {api_key[:8]}...{api_key[-4:]}")
print("⏳ Testando conexão com a OpenAI...")

try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Responda apenas: OK"}
        ],
        max_tokens=5
    )

    answer = response.choices[0].message.content.strip()
    print(f"✅ Chave VÁLIDA! Resposta da OpenAI: '{answer}'")
    print(f"   Modelo: gpt-4o-mini")
    print(f"   Tokens usados: {response.usage.total_tokens}")

except Exception as e:
    error_msg = str(e)
    if "Incorrect API key" in error_msg or "invalid_api_key" in error_msg:
        print("❌ Chave INVÁLIDA ou expirada.")
        print("   Gere uma nova em: https://platform.openai.com/api-keys")
    elif "insufficient_quota" in error_msg:
        print("⚠️  Chave válida, mas sem créditos.")
        print("   Adicione créditos em: https://platform.openai.com/settings/billing")
    else:
        print(f"❌ Erro inesperado: {error_msg}")
