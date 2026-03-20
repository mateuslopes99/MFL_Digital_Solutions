# MFL Digital Solutions — Configurações Centralizadas
# Importar aqui em vez de hardcodar em múltiplos arquivos

# Preços por plano (MRR em R$)
PLAN_PRICES = {
    "starter":    690,
    "pro":       1490,
    "enterprise": 2990,
}

# Fallback para plano desconhecido
DEFAULT_PLAN_PRICE = 1490

def get_plan_price(package: str) -> int:
    return PLAN_PRICES.get(package, DEFAULT_PLAN_PRICE)
