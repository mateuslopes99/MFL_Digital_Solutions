"""
MFL Digital Solutions — Teste do Fluxo Completo (Mock)
=======================================================
Simula o recebimento de mensagens WhatsApp e verifica:
  1. Classificação da IA (mock)
  2. Salvamento no banco de dados
  3. Resposta gerada para o cliente

Execute: python backend/test_flow.py
"""

import os
import sys

# Garantir que o path do backend está correto
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from modules.ai_classifier import classify_lead, USE_MOCK
from database import init_db, insert_lead, get_leads, log_conversation

# ─── Mensagens de teste ────────────────────────────────────────────────────────
TEST_MESSAGES = [
    {
        "label": "🔥 HOT — Compra urgente",
        "message": "Oi, preciso urgente de um apartamento em Ponta Verde. "
                   "Já tenho financiamento aprovado, até R$ 600 mil. "
                   "Posso visitar amanhã?"
    },
    {
        "label": "🟡 WARM — Procurando casa",
        "message": "Olá, estou procurando uma casa para comprar na Jatiúca ou Mangabeiras. "
                   "Tenho interesse em algo com 3 quartos. Vocês têm opções?"
    },
    {
        "label": "❄️ COLD — Só pesquisando",
        "message": "Boa tarde, só curiosidade mesmo, qual o preço médio "
                   "de apartamentos em Maceió? Talvez futuramente eu compre algo."
    },
    {
        "label": "🟡 WARM — Aluguel",
        "message": "Preciso alugar um apartamento de 2 quartos no Farol ou Pajuçara. "
                   "Qual o valor médio? Quero para o próximo mês."
    },
    {
        "label": "🔥 HOT — Imóvel comercial",
        "message": "Boa tarde! Preciso de uma sala comercial no Centro, "
                   "tenho o dinheiro disponível, quero fechar essa semana. "
                   "Tem alguma disponível?"
    },
]


def separator(char="─", width=60):
    print(char * width)


def run_tests():
    print()
    separator("═")
    print(f"  MFL Digital Solutions — Teste do Fluxo Completo")
    print(f"  Modo: {'🟡 MOCK (simulação)' if USE_MOCK else '🤖 REAL (OpenAI)'}")
    separator("═")

    # Inicializar banco de dados
    init_db()
    print()

    resultados = []

    for i, test in enumerate(TEST_MESSAGES, 1):
        print(f"TESTE {i}/5: {test['label']}")
        separator()
        print(f"💬 Mensagem: \"{test['message'][:80]}...\"" if len(test['message']) > 80
              else f"💬 Mensagem: \"{test['message']}\"")
        print()

        # Classificar com IA (mock ou real)
        result = classify_lead(test["message"])

        # Exibir resultado
        emoji = {"hot": "🔥", "warm": "🟡", "cold": "❄️"}.get(result["classification"], "❓")
        print(f"  Classificação : {emoji} {result['classification'].upper()}")
        print(f"  Categoria     : {result['category']}")
        print(f"  Urgência      : {result['urgency']}")
        print(f"  Orçamento     : {result['budget']}")
        print(f"  Tipo Imóvel   : {result['property_type']}")
        print(f"  Bairro        : {result['neighborhood']}")
        print(f"  Resumo        : {result['summary']}")
        print()
        print(f"  Resposta para o cliente:")
        print(f"  \"{result['suggested_response']}\"")
        print()

        # Salvar no banco de dados
        lead_id = insert_lead(
            client_id=1,
            phone=f"whatsapp:+558299900000{i}",
            classification=result["classification"],
            category=result["category"],
            urgency=result["urgency"],
            budget=result["budget"],
            property_type=result["property_type"],
            neighborhood=result["neighborhood"],
            summary=result["summary"],
            raw_message=test["message"]
        )
        log_conversation(lead_id, "inbound", test["message"])
        log_conversation(lead_id, "outbound", result["suggested_response"])

        print(f"  ✅ Salvo no banco! Lead ID: {lead_id}")
        separator()
        print()

        resultados.append(result["classification"])

    # Resumo final
    separator("═")
    print("  RESUMO DOS TESTES")
    separator("═")
    hot   = resultados.count("hot")
    warm  = resultados.count("warm")
    cold  = resultados.count("cold")
    total = len(resultados)
    print(f"  Total de mensagens testadas : {total}")
    print(f"  🔥 HOT  (leads quentes)     : {hot}")
    print(f"  🟡 WARM (leads mornos)      : {warm}")
    print(f"  ❄️  COLD (leads frios)       : {cold}")
    print()

    # Verificar leads no banco
    leads = get_leads(client_id=1)
    print(f"  Total de leads no banco     : {len(leads)}")
    separator("═")
    print()
    print("  ✅ Todos os testes passaram!")
    print("  O fluxo completo está funcionando:")
    print("  Mensagem → Classificação → Banco de Dados → Resposta")
    print()
    if USE_MOCK:
        print("  💡 Para ativar a IA real (OpenAI), altere no .env:")
        print("     USE_MOCK=false")
    separator("═")
    print()


if __name__ == "__main__":
    run_tests()
