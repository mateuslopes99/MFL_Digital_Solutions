"""
MFL Digital Solutions — Classificador de Leads com IA
======================================================
Suporta dois modos:
  - MOCK (USE_MOCK=true no .env): Simula classificação sem usar créditos OpenAI.
    Usa regras de palavras-chave para gerar respostas realistas.
  - REAL (USE_MOCK=false): Usa GPT-4o-mini via OpenAI API.

Para alternar, edite o .env: USE_MOCK=true|false
"""

import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

# ─── Configuração de Modo ──────────────────────────────────────────────────────
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

# ─── Cliente OpenAI (lazy, só inicializa quando USE_MOCK=false) ────────────────
_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("sk-..."):
            raise ValueError("[AI] OPENAI_API_KEY não configurada no .env")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


# ─── Prompt do sistema (usado no modo REAL) ────────────────────────────────────
SYSTEM_PROMPT = """Você é um especialista em qualificação de leads para imobiliárias.
Analise a mensagem do cliente e responda APENAS com um JSON válido, sem markdown.

Classifique como:
- "hot": Orçamento definido, urgência alta, pronto para comprar/alugar
- "warm": Interessado mas sem urgência ou orçamento indefinido
- "cold": Curiosidade, pesquisa inicial, sem intenção clara

Para o score (0-100), use estes critérios:
- Urgência declarada (esta semana, amanhã, urgente): +30
- Budget confirmado dentro do perfil: +25
- Região/bairro específico informado: +20
- Engajamento alto (várias informações, perguntas): +15
- Perfil ativo (linguagem de quem já decidiu): +10

Para o sentimento:
- "empolgado": linguagem entusiástica, muitas perguntas, ansião positivo
- "ansioso": urgência, medo de perder oportunidade
- "irritado": frustração, reclamação, experiência ruim anterior
- "neutro": consulta objetiva, sem carga emocional

Responda EXATAMENTE neste formato:
{
  "classification": "hot|warm|cold",
  "category": "compra|aluguel|consulta|reclamacao|outro",
  "urgency": "alta|media|baixa",
  "budget": "valor ou 'não informado'",
  "property_type": "apartamento|casa|comercial|terreno|não informado",
  "neighborhood": "bairro ou 'não informado'",
  "score": 0,
  "sentiment": "empolgado|ansioso|irritado|neutro",
  "summary": "resumo em uma frase",
  "suggested_response": "resposta amigável ao cliente"
}"""


# ─── Modo MOCK — classificador por palavras-chave ─────────────────────────────
_HOT_KEYWORDS = [
    "urgente", "preciso logo", "esta semana", "amanhã", "já", "imediato",
    "aprovado", "financiamento aprovado", "dinheiro", "pronto para",
    "quero fechar", "vamos fechar", "confirmar", "assinar", "comprar hoje",
]

_WARM_KEYWORDS = [
    "interesse", "gostaria", "quero ver", "tem disponível", "visita",
    "quando posso", "me manda", "informações", "queria saber", "estou procurando",
    "você tem", "procurando", "apartamento", "casa", "alugar", "comprar",
]

_COLD_KEYWORDS = [
    "só curiosidade", "pesquisando", "futuramente", "talvez", "não sei",
    "ainda não decidi", "só olhando", "preço médio", "qual o valor",
]

_NEIGHBORHOOD_WORDS = [
    "ponta verde", "jatiúca", "pajuçara", "farol", "mangabeiras", "gruta",
    "petrópolis", "centro", "tabuleiro", "benedito bentes", "antares",
    "serraria", "canaã", "clima bom", "pinheiro",
]

_BUDGET_PATTERN = re.compile(
    r"r?\$?\s*([\d\.]+)\s*(mil|k|reais|milhão|milhões)?", re.IGNORECASE
)

_PROPERTY_KEYWORDS = {
    "apartamento": ["apartamento", "apto", "ap "],
    "casa": ["casa", "sobrado", "chácara"],
    "comercial": ["comercial", "sala", "loja", "escritório", "galpão"],
    "terreno": ["terreno", "lote", "área"],
}


def _mock_classify(message: str) -> dict:
    """
    Classifica um lead usando regras de palavras-chave.
    Simula o comportamento da IA de forma determinística e gratuita.
    """
    msg_lower = message.lower()

    # Classificação
    if any(kw in msg_lower for kw in _HOT_KEYWORDS):
        classification = "hot"
        urgency = "alta"
    elif any(kw in msg_lower for kw in _COLD_KEYWORDS):
        classification = "cold"
        urgency = "baixa"
    else:
        classification = "warm"
        urgency = "media"

    # Categoria
    if any(w in msg_lower for w in ["aluguel", "alugar", "aluga"]):
        category = "aluguel"
    elif any(w in msg_lower for w in ["comprar", "compra", "adquirir"]):
        category = "compra"
    elif any(w in msg_lower for w in ["reclamar", "problema", "erro"]):
        category = "reclamacao"
    else:
        category = "consulta"

    # Tipo de imóvel
    property_type = "não informado"
    for ptype, keywords in _PROPERTY_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            property_type = ptype
            break

    # Bairro
    neighborhood = "não informado"
    for bairro in _NEIGHBORHOOD_WORDS:
        if bairro in msg_lower:
            neighborhood = bairro.title()
            break

    # Orçamento
    budget = "não informado"
    match = _BUDGET_PATTERN.search(message)
    if match:
        valor = match.group(1).replace(".", "")
        sufixo = (match.group(2) or "").lower()
        if sufixo in ("mil", "k"):
            budget = f"R$ {valor}.000"
        elif sufixo in ("milhão", "milhões"):
            budget = f"R$ {valor}.000.000"
        else:
            budget = f"R$ {valor}"

    # Resumo
    summary_map = {
        "hot":  f"Lead quente — {category} de {property_type} com urgência alta",
        "warm": f"Lead morno — interesse em {category} de {property_type}",
        "cold": f"Lead frio — pesquisando {property_type}, sem urgência",
    }
    summary = summary_map[classification]

    # Resposta sugerida
    if classification == "hot":
        response = (
            f"Olá! 🔥 Vi que você tem interesse urgente. "
            f"Um de nossos corretores especializados vai entrar em contato *agora mesmo* "
            f"para te ajudar a encontrar o imóvel ideal! 🏠"
        )
    elif classification == "warm":
        response = (
            f"Olá! 👋 Que bom te ver por aqui! Temos *ótimas opções* de {property_type} "
            f"{'em ' + neighborhood if neighborhood != 'não informado' else 'em Maceió'}. "
            f"Posso te enviar algumas sugestões? Nos conte um pouco mais sobre o que procura! 😊"
        )
    else:
        response = (
            "Olá! 👋 Obrigado pelo contato! Estamos aqui para te ajudar quando estiver "
            "pronto para dar o próximo passo. Quer que eu te envie nossa lista de imóveis? 🏠"
        )

    return {
        "classification": classification,
        "category": category,
        "urgency": urgency,
        "budget": budget,
        "property_type": property_type,
        "neighborhood": neighborhood,
        "score": _calculate_score(classification, urgency, budget, neighborhood, msg_lower),
        "sentiment": _detect_sentiment(msg_lower),
        "summary": summary,
        "suggested_response": response,
        "_mock": True,
    }


# ─── Score Numérico 0–100 ──────────────────────────────────────────────────────

def _calculate_score(classification: str, urgency: str, budget: str,
                     neighborhood: str, msg_lower: str) -> int:
    """Calcula score de 0-100 baseado em 5 critérios do plano estratégico."""
    score = 0
    _HIGH_URGENCY = ["esta semana", "amanhã", "urgente", "imediato", "hoje",
                     "pronto", "já", "logo", "rápido", "agora"]
    if urgency == "alta" or any(k in msg_lower for k in _HIGH_URGENCY):
        score += 30
    elif urgency == "media":
        score += 15
    if budget and budget != "não informado":
        score += 25
    if neighborhood and neighborhood != "não informado":
        score += 20
    word_count = len(msg_lower.split())
    if word_count >= 15:
        score += 15
    elif word_count >= 8:
        score += 8
    if classification == "hot":
        score += 10
    elif classification == "warm":
        score += 5
    return min(score, 100)


def _detect_sentiment(msg_lower: str) -> str:
    """Detecta o tom emocional da mensagem."""
    _IRRITADO  = ["absurdo", "péssimo", "horrivel", "raiva", "revoltado",
                  "decepcionado", "errado"]
    _ANSIOSO   = ["urgente", "preciso logo", "não posso perder", "prazo",
                  "último", "acabando", "antes que"]
    _EMPOLGADO = ["amei", "perfeito", "exatamente", "incrivel", "maravilhoso",
                  "adorei", "top", "show", "excelente"]
    if any(k in msg_lower for k in _IRRITADO):
        return "irritado"
    if any(k in msg_lower for k in _ANSIOSO):
        return "ansioso"
    if any(k in msg_lower for k in _EMPOLGADO):
        return "empolgado"
    return "neutro"


# ─── Função principal ──────────────────────────────────────────────────────────
def classify_lead(message: str, conversation_history: list = None) -> dict:
    """
    Classifica um lead com base na mensagem recebida.

    Usa modo MOCK se USE_MOCK=true no .env (padrão).
    Usa OpenAI se USE_MOCK=false e OPENAI_API_KEY estiver configurada.
    """
    if USE_MOCK:
        print(f"[AI] Modo MOCK ativo — classificando sem API")
        return _mock_classify(message)

    # Modo REAL (OpenAI)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        for entry in conversation_history[-6:]:
            messages.append(entry)
    messages.append({"role": "user", "content": f"Mensagem do cliente: {message}"})

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        result["_mock"] = False
        return result

    except json.JSONDecodeError:
        return _mock_classify(message)  # Fallback para mock
    except Exception as e:
        print(f"[AI] Erro OpenAI: {e} — usando mock como fallback")
        result = _mock_classify(message)
        result["_error"] = str(e)
        return result


def generate_qualification_questions() -> str:
    """Gera perguntas de qualificação para o lead."""
    return (
        "Para te ajudar melhor, preciso de algumas informações rápidas:\n\n"
        "💰 *Qual é o seu orçamento aproximado?*\n"
        "a) Até R$ 300K\nb) R$ 300K - R$ 600K\nc) R$ 600K - R$ 1M\nd) Acima de R$ 1M\n\n"
        "🏠 *Qual tipo de imóvel você procura?*\n"
        "a) Apartamento\nb) Casa\nc) Comercial\nd) Terreno\n\n"
        "⏰ *Qual é a sua urgência?*\n"
        "a) Preciso urgente (esta semana)\nb) Próximo mês\n"
        "c) Nos próximos 3 meses\nd) Só pesquisando"
    )
