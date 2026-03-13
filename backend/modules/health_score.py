"""
MFL Digital Solutions — Cálculo de Health Score
================================================
Calcula a saúde de cada cliente (0-100) baseado em dados reais do banco.

Componentes:
  - Lead Velocity   (30pts): volume de leads nos últimos 30 dias
  - Qualification   (30pts): taxa HOT+WARM / total leads
  - Conversion      (20pts): taxa de conversão real
  - Recency         (10pts): dias desde o último lead
  - Trend           (10pts): tendência semanal positiva ou negativa
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection

# Limite de leads por plano (referência para lead_velocity)
PLAN_LEAD_CAP = {
    "starter":    50,
    "basico":     200,
    "pro":        600,
    "enterprise": 9999,
}


def calculate_health_score(client_id: int) -> dict:
    """
    Calcula o health score (0-100) de um cliente.
    Retorna um dict com o score e o detalhamento de cada componente.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # ── Busca o plano do cliente ───────────────────────────────────────────
    cursor.execute("SELECT package FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    package  = (row["package"] if row else "pro") or "pro"
    lead_cap = PLAN_LEAD_CAP.get(package, 200)

    # ── Total de leads ─────────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) as n FROM leads WHERE client_id = ?", (client_id,))
    total_leads = cursor.fetchone()["n"]

    # ── Leads por classificação ────────────────────────────────────────────
    cursor.execute("""
        SELECT classification, COUNT(*) as n
        FROM leads WHERE client_id = ?
        GROUP BY classification
    """, (client_id,))
    by_class = {r["classification"]: r["n"] for r in cursor.fetchall()}
    hot  = by_class.get("hot",  0)
    warm = by_class.get("warm", 0)
    cold = by_class.get("cold", 0)

    # ── Leads convertidos ──────────────────────────────────────────────────
    cursor.execute("""
        SELECT COUNT(*) as n FROM leads
        WHERE client_id = ? AND status = 'converted'
    """, (client_id,))
    converted = cursor.fetchone()["n"]

    # ── Leads últimos 30 dias ──────────────────────────────────────────────
    cursor.execute("""
        SELECT COUNT(*) as n FROM leads
        WHERE client_id = ?
          AND DATE(created_at) >= DATE('now', '-30 days')
    """, (client_id,))
    leads_30d = cursor.fetchone()["n"]

    # ── Data do último lead ────────────────────────────────────────────────
    cursor.execute("""
        SELECT created_at FROM leads
        WHERE client_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (client_id,))
    last_lead_row = cursor.fetchone()

    # ── Leads semana atual e semana passada (para tendência) ───────────────
    cursor.execute("""
        SELECT COUNT(*) as n FROM leads
        WHERE client_id = ?
          AND DATE(created_at) >= DATE('now', '-7 days')
    """, (client_id,))
    leads_this_week = cursor.fetchone()["n"]

    cursor.execute("""
        SELECT COUNT(*) as n FROM leads
        WHERE client_id = ?
          AND DATE(created_at) >= DATE('now', '-14 days')
          AND DATE(created_at) <  DATE('now', '-7 days')
    """, (client_id,))
    leads_last_week = cursor.fetchone()["n"]

    conn.close()

    # ── 1. Lead Velocity (30 pts) ──────────────────────────────────────────
    # Quanto do cap mensal o cliente usou nos últimos 30 dias?
    if lead_cap >= 9999:   # enterprise: sem cap → usa 300 como base
        velocity_pct = min(leads_30d / 300, 1.0)
    else:
        velocity_pct = min(leads_30d / lead_cap, 1.0)
    velocity_score = round(velocity_pct * 30)

    # ── 2. Qualification Rate (30 pts) ────────────────────────────────────
    qual_rate = (hot + warm) / total_leads if total_leads > 0 else 0
    qual_score = round(qual_rate * 30)

    # ── 3. Conversion Rate (20 pts) ───────────────────────────────────────
    # Conversão de 10% = score 20 (meta realista para imobiliária)
    conv_rate  = converted / total_leads  if total_leads > 0 else 0
    conv_score = round(min(conv_rate / 0.10, 1.0) * 20)

    # ── 4. Recency (10 pts) ───────────────────────────────────────────────
    if not last_lead_row:
        recency_score = 0
    else:
        from datetime import datetime
        last_lead_dt = datetime.fromisoformat(last_lead_row["created_at"])
        days_ago = (datetime.utcnow() - last_lead_dt).days
        if days_ago <= 3:
            recency_score = 10
        elif days_ago <= 7:
            recency_score = 8
        elif days_ago <= 14:
            recency_score = 5
        elif days_ago <= 30:
            recency_score = 2
        else:
            recency_score = 0

    # ── 5. Trend (10 pts) ─────────────────────────────────────────────────
    if leads_this_week >= leads_last_week and leads_this_week > 0:
        trend_score = 10   # crescendo ou estável com atividade
    elif leads_this_week > 0:
        trend_score = 5    # caiu mas tem atividade
    elif leads_last_week > 0:
        trend_score = 2    # parou de receber leads
    else:
        trend_score = 0    # sem atividade recente

    # ── Score final ───────────────────────────────────────────────────────
    total_score = velocity_score + qual_score + conv_score + recency_score + trend_score
    total_score = max(0, min(100, total_score))   # garante 0-100

    # ── Classificação semântica ────────────────────────────────────────────
    if total_score >= 80:
        label    = "Saudável"
        color    = "#00C853"
        churn_risk = max(0, round((100 - total_score) * 0.3))
    elif total_score >= 60:
        label    = "Atenção"
        color    = "#FFD600"
        churn_risk = round((100 - total_score) * 0.6)
    else:
        label    = "Crítico"
        color    = "#FF5252"
        churn_risk = round((100 - total_score) * 0.9)

    return {
        "health_score": total_score,
        "label":        label,
        "color":        color,
        "churn_risk":   churn_risk,
        "detail": {
            "velocity":    velocity_score,    # 0-30
            "qual_rate":   qual_score,        # 0-30
            "conversion":  conv_score,        # 0-20
            "recency":     recency_score,     # 0-10
            "trend":       trend_score,       # 0-10
        },
        "raw": {
            "total_leads":      total_leads,
            "hot":              hot,
            "warm":             warm,
            "cold":             cold,
            "converted":        converted,
            "leads_30d":        leads_30d,
            "leads_this_week":  leads_this_week,
            "leads_last_week":  leads_last_week,
            "qualification_pct": round(qual_rate * 100, 1),
            "conversion_pct":    round(conv_rate * 100, 1),
        },
    }


def bulk_health_scores(client_ids: list[int]) -> dict[int, dict]:
    """Calcula health scores para múltiplos clientes de uma vez."""
    return {cid: calculate_health_score(cid) for cid in client_ids}


def save_snapshot(client_id: int, hs: dict, alerted: bool = False, email_sent: bool = False) -> bool:
    """
    Salva um snapshot do health score no histórico.
    Usa INSERT OR REPLACE para sobrescrever se já existe na mesma semana.
    Retorna True se inserido/atualizado.
    """
    from datetime import date
    week = date.today().strftime("%Y-W%W")   # ex: "2026-W09"
    det  = hs.get("detail", {})

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO health_score_history
                (client_id, week, health_score, label,
                 velocity, qual_rate, conversion, recency, trend,
                 alerted, email_sent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(client_id, week) DO UPDATE SET
                health_score = excluded.health_score,
                label        = excluded.label,
                velocity     = excluded.velocity,
                qual_rate    = excluded.qual_rate,
                conversion   = excluded.conversion,
                recency      = excluded.recency,
                trend        = excluded.trend,
                alerted      = MAX(alerted, excluded.alerted),
                email_sent   = MAX(email_sent, excluded.email_sent)
        """, (
            client_id, week,
            hs.get("health_score", 0),
            hs.get("label", ""),
            det.get("velocity",   0),
            det.get("qual_rate",  0),
            det.get("conversion", 0),
            det.get("recency",    0),
            det.get("trend",      0),
            int(alerted),
            int(email_sent),
        ))
        conn.commit()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[SNAPSHOT] Erro ao salvar: {e}")
        return False
    finally:
        conn.close()


def get_history(client_id: int, weeks: int = 12) -> list[dict]:
    """
    Retorna o histórico de health scores de um cliente (últimas N semanas).
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT week, health_score, label, velocity, qual_rate,
               conversion, recency, trend, alerted, email_sent, recorded_at
        FROM health_score_history
        WHERE client_id = ?
        ORDER BY week DESC
        LIMIT ?
    """, (client_id, weeks))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))   # mais antigo → mais recente
