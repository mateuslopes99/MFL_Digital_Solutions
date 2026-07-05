# MFL Digital Solutions — Configurações Centralizadas
# Importar aqui em vez de hardcodar em múltiplos arquivos
# ⚠️  Nunca colocar secrets aqui — use variáveis de ambiente

# Preços por plano (MRR em R$)
PLAN_PRICES = {
    "essencial": 197,
    "starter":   690,
    "pro":       1490,
    "enterprise": 2990,
}

# Volume de leads/atendimentos permitidos por plano (por mês)
PLAN_LIMITS = {
    "essencial": 30,    # atendimentos/agendamentos
    "starter":   50,    # leads qualificados
    "pro":       300,   # leads qualificados
    "enterprise": None, # ilimitado
}

# Fallback para plano desconhecido
DEFAULT_PLAN_PRICE = 1490

def get_plan_price(package: str) -> int:
    return PLAN_PRICES.get(package.lower(), DEFAULT_PLAN_PRICE)

def get_plan_limit(package: str) -> int | None:
    return PLAN_LIMITS.get(package.lower(), 50)
