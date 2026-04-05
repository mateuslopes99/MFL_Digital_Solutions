"""
MFL Digital Solutions — Rotas do Dashboard (API)
=================================================
Fornece dados para os dashboards Admin e Cliente.
"""

import os
import sys
from flask import Blueprint, jsonify, request, session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection, _IS_POSTGRES
from modules.health_score import calculate_health_score, bulk_health_scores, save_snapshot, get_history
from modules.alerts import send_whatsapp_alert, send_email_report
from config import get_plan_price

dashboard_bp = Blueprint("dashboard", __name__)


def _date_offset(days: int) -> str:
    """Gera o SQL para offset de dados (suporta SQLite e PostgreSQL)."""
    if _IS_POSTGRES:
        return f"NOW() - INTERVAL '{days} days'"
    return f"DATE('now', '-{days} days')"


@dashboard_bp.route("/admin/overview", methods=["GET"])
def admin_overview():
    """Retorna visão geral para o dashboard admin."""
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Acesso restrito ao administrador"}), 403

    conn = get_connection()
    cursor = conn.cursor()

    # Total de leads
    cursor.execute("SELECT COUNT(*) as total FROM leads")
    total_leads = cursor.fetchone()["total"]

    # Leads por classificação
    cursor.execute("""
        SELECT classification, COUNT(*) as count
        FROM leads GROUP BY classification
    """)
    by_classification = {row["classification"]: row["count"] for row in cursor.fetchall()}

    # Leads hoje
    if _IS_POSTGRES:
        cursor.execute("SELECT COUNT(*) as total FROM leads WHERE DATE(created_at) = CURRENT_DATE")
    else:
        cursor.execute("SELECT COUNT(*) as total FROM leads WHERE DATE(created_at) = DATE('now')")
    leads_today = cursor.fetchone()["total"]

    # Total de clientes ativos
    cursor.execute("SELECT id, name, niche, package, status FROM clients WHERE status = 'active'")
    client_rows = cursor.fetchall()
    active_clients = len(client_rows)

    # ── MRR total ──────────────────────────────────────────────────────────
    total_mrr = sum(get_plan_price(r["package"] or "pro") for r in client_rows)

    conn.close()

    # ── Health scores por cliente ──────────────────────────────────────────
    client_ids = [r["id"] for r in client_rows]
    health_map = bulk_health_scores(client_ids)

    clients_with_health = []
    for r in client_rows:
        hs = health_map.get(r["id"], {})
        clients_with_health.append({
            "id":          r["id"],
            "name":        r["name"],
            "niche":       r["niche"],
            "package":     r["package"],
            "mrr":         get_plan_price(r["package"] or "pro"),
            "health_score":hs.get("health_score", 50),
            "churn_risk":  hs.get("churn_risk",  25),
            "health_label":hs.get("label",       "Atenção"),
            "status":      "active",
            "leads_30d":   0,
        })

    avg_health = round(
        sum(c["health_score"] for c in clients_with_health) / len(clients_with_health)
    ) if clients_with_health else 0

    risk_clients = [c for c in clients_with_health if c["health_score"] < 70]

    return jsonify({
        "total_leads":     total_leads,
        "leads_today":     leads_today,
        "active_clients":  active_clients,
        "total_mrr":       total_mrr,
        "avg_health":      avg_health,
        "risk_count":      len(risk_clients),
        "by_classification": {
            "hot":  by_classification.get("hot",  0),
            "warm": by_classification.get("warm", 0),
            "cold": by_classification.get("cold", 0),
        },
        "clients_with_health": clients_with_health,
    })


@dashboard_bp.route("/client/<int:client_id>/overview", methods=["GET"])
def client_overview(client_id):
    """Retorna métricas enriquecidas para o dashboard do cliente."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Não autenticado"}), 401
    # Clientes só podem ver seus próprios dados; admin pode ver qualquer um
    if user.get("role") == "client" and user.get("client_id") != client_id:
        return jsonify({"error": "Acesso negado"}), 403

    conn = get_connection()
    cursor = conn.cursor()

    # ── Totais básicos ────────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) as total FROM leads WHERE client_id = ?", (client_id,))
    total_leads = cursor.fetchone()["total"]

    # Leads por classificação
    cursor.execute("""
        SELECT classification, COUNT(*) as count
        FROM leads WHERE client_id = ?
        GROUP BY classification
    """, (client_id,))
    by_class = {row["classification"]: row["count"] for row in cursor.fetchall()}

    # Leads esta semana
    cursor.execute(f"""
        SELECT COUNT(*) as total FROM leads
        WHERE client_id = ? AND created_at >= {_date_offset(7)}
    """, (client_id,))
    leads_week = cursor.fetchone()["total"]

    # ── Taxa de conversão (leads com status 'converted') ──────────────────
    cursor.execute("""
        SELECT COUNT(*) as total FROM leads
        WHERE client_id = ? AND status = 'converted'
    """, (client_id,))
    converted = cursor.fetchone()["total"]

    # Leads por status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM leads WHERE client_id = ?
        GROUP BY status
    """, (client_id,))
    by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

    # ── Tendência semanal (últimas 4 semanas) ─────────────────────────────
    weekly_trend = []
    for i in range(3, -1, -1):   # semana mais antiga → mais recente
        start_days = (i + 1) * 7
        end_days   = i * 7

        cursor.execute(f"""
            SELECT COUNT(*) as total FROM leads
            WHERE client_id = ?
              AND created_at >= {_date_offset(start_days)}
              AND created_at <  {_date_offset(end_days)}
        """, (client_id,))
        week_total = cursor.fetchone()["total"]

        cursor.execute(f"""
            SELECT COUNT(*) as total FROM leads
            WHERE client_id = ?
              AND classification IN ('hot', 'warm')
              AND created_at >= {_date_offset(start_days)}
              AND created_at <  {_date_offset(end_days)}
        """, (client_id,))
        week_qualified = cursor.fetchone()["total"]

        cursor.execute(f"""
            SELECT COUNT(*) as total FROM leads
            WHERE client_id = ?
              AND status = 'converted'
              AND created_at >= {_date_offset(start_days)}
              AND created_at <  {_date_offset(end_days)}
        """, (client_id,))
        week_converted = cursor.fetchone()["total"]

        weekly_trend.append({
            "week":       f"Sem {4 - i}",
            "leads":      week_total,
            "qualified":  week_qualified,
            "conversion": round(week_converted / week_total * 100, 1) if week_total > 0 else 0,
        })

    conn.close()

    # ── Cálculos derivados ────────────────────────────────────────────────
    hot  = by_class.get("hot",  0)
    warm = by_class.get("warm", 0)
    cold = by_class.get("cold", 0)

    qualification_rate = round((hot + warm) / total_leads * 100, 1) if total_leads > 0 else 0
    conversion_rate    = round(converted / total_leads * 100, 1)     if total_leads > 0 else 0

    # Variação semanal de leads (Sem 4 vs Sem 3)
    leads_trend_pct = 0
    if len(weekly_trend) >= 2:
        prev = weekly_trend[-2]["leads"]
        curr = weekly_trend[-1]["leads"]
        if prev > 0:
            leads_trend_pct = round((curr - prev) / prev * 100, 1)

    # Variação semanal de qualificação
    qual_trend_pct = 0
    if len(weekly_trend) >= 2:
        prev_q = weekly_trend[-2]["qualified"]
        curr_q = weekly_trend[-1]["qualified"]
        prev_t = weekly_trend[-2]["leads"]
        curr_t = weekly_trend[-1]["leads"]
        prev_rate = round(prev_q / prev_t * 100, 1) if prev_t > 0 else 0
        curr_rate = round(curr_q / curr_t * 100, 1) if curr_t > 0 else 0
        qual_trend_pct = round(curr_rate - prev_rate, 1)

    # ── Alertas dinâmicos baseados nos dados reais ────────────────────────
    alerts = []
    if qualification_rate < 70 and total_leads > 0:
        alerts.append({
            "id":      1,
            "type":    "warning",
            "title":   "Taxa de Qualificação Abaixo da Meta",
            "message": (
                f"Sua taxa de qualificação é {qualification_rate}% (meta: 70%+). "
                "Revise o fluxo de qualificação do bot."
            ),
        })
    if conversion_rate < 10 and total_leads > 0:
        alerts.append({
            "id":      2,
            "type":    "critical",
            "title":   "Taxa de Conversão Crítica",
            "message": (
                f"Apenas {conversion_rate}% dos leads converteram. "
                "Acione o follow-up automático para leads quentes."
            ),
        })
    cold_pct = round(cold / total_leads * 100) if total_leads > 0 else 0
    if cold_pct > 50:
        alerts.append({
            "id":      3,
            "type":    "warning",
            "title":   "Muitos Leads Frios",
            "message": (
                f"{cold_pct}% dos seus leads são classificados como frios. "
                "Revise a fonte de tráfego ou o critério de qualificação."
            ),
        })

    return jsonify({
        # Totais
        "total_leads":        total_leads,
        "leads_week":         leads_week,
        # Classificação
        "hot":                hot,
        "warm":               warm,
        "cold":               cold,
        # Taxas
        "qualification_rate": qualification_rate,
        "conversion_rate":    conversion_rate,
        # Variações semanais (para seta de tendência nos KPIs)
        "leads_trend_pct":    leads_trend_pct,
        "qual_trend_pct":     qual_trend_pct,
        # Status dos leads
        "converted":          converted,
        "by_status": {
            "new":       by_status.get("new",       0),
            "contacted": by_status.get("contacted", 0),
            "converted": by_status.get("converted", 0),
            "lost":      by_status.get("lost",      0),
        },
        # Tendência semanal (4 semanas)
        "weekly_trend": weekly_trend,
        # Alertas dinâmicos
        "alerts": alerts,
    })


# ── Health Check Automático ─────────────────────────────────────────────────────

@dashboard_bp.route("/admin/run-health-check", methods=["POST"])
def run_health_check():
    """
    Verifica a saúde de todos os clientes ativos:
    - Salva snapshot no histórico
    - Envia alerta WhatsApp ao admin para críticos (score < 50)
    - Envia e-mail semanal ao cliente
    """
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Acesso restrito ao admin"}), 403

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, package, phone, whatsapp_number
        FROM clients WHERE status = 'active'
    """)
    clients = [dict(r) for r in cursor.fetchall()]
    conn.close()

    results = []
    wa_alerts = 0
    emails_sent = 0

    for client in clients:
        hs = calculate_health_score(client["id"])
        score = hs.get("health_score", 0)

        # Enviar alerta WhatsApp ao admin se score crítico
        alerted = False
        if score < 50:
            alerted = send_whatsapp_alert(client, hs)
            if alerted:
                wa_alerts += 1

        # Enviar e-mail ao cliente (sempre, com conteúdo personalizado)
        emailed = send_email_report(client, hs)
        if emailed:
            emails_sent += 1

        # Salvar snapshot no histórico
        save_snapshot(client["id"], hs, alerted=alerted, email_sent=emailed)

        results.append({
            "client_id":    client["id"],
            "name":         client["name"],
            "health_score": score,
            "label":        hs.get("label"),
            "alerted":      alerted,
            "email_sent":   emailed,
        })

    return jsonify({
        "checked":    len(results),
        "wa_alerts":  wa_alerts,
        "emails_sent":emails_sent,
        "results":    results,
    })


@dashboard_bp.route("/admin/clients/<int:client_id>/history", methods=["GET"])
def client_health_history(client_id):
    """Retorna o histórico de health score de um cliente (admin only)."""
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Acesso restrito ao admin"}), 403

    weeks = min(int(request.args.get("weeks", 12)), 52)
    history = get_history(client_id, weeks)
    return jsonify({"client_id": client_id, "history": history})


@dashboard_bp.route("/client/me/history", methods=["GET"])
def my_health_history():
    """Retorna o histórico de health score do cliente logado."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Não autenticado"}), 401
    if user.get("role") != "client":
        return jsonify({"error": "Acesso apenas para clientes"}), 403

    client_id = user.get("client_id")
    weeks = min(int(request.args.get("weeks", 12)), 52)
    history = get_history(client_id, weeks)
    return jsonify({"client_id": client_id, "history": history})


# ── Endpoints de Custo de Tokens (Fase 2) ─────────────────────────────────────

@dashboard_bp.route("/admin/clients/<int:client_id>/token-cost", methods=["GET"])
def client_token_cost(client_id):
    """
    Retorna o custo de tokens do mês corrente para um cliente.
    Inclui alerta se estiver acima de 80% do budget.
    """
    user = session.get("user")
    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    # Admin vê qualquer cliente; cliente vê apenas o próprio
    if user["role"] == "client" and user.get("client_id") != client_id:
        return jsonify({"error": "Acesso negado"}), 403

    from database import get_monthly_token_cost, check_token_budget_alert

    budget_brl = float(request.args.get("budget", 100.0))
    custo      = get_monthly_token_cost(client_id)
    alerta     = check_token_budget_alert(client_id, budget_brl=budget_brl)

    return jsonify({**custo, **alerta})


@dashboard_bp.route("/admin/token-costs", methods=["GET"])
def all_token_costs():
    """Retorna custo de tokens de todos os clientes ativos (admin only)."""
    user = session.get("user")
    if not user or user["role"] != "admin":
        return jsonify({"error": "Acesso restrito ao admin"}), 403

    from database import get_connection, get_monthly_token_cost, check_token_budget_alert

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, package FROM clients WHERE status = 'active'")
    clients = cursor.fetchall()
    conn.close()

    results   = []
    total_brl = 0.0

    for c in clients:
        custo  = get_monthly_token_cost(c["id"])
        alerta = check_token_budget_alert(c["id"], budget_brl=100.0)
        item   = {
            "client_id":   c["id"],
            "name":        c["name"],
            "package":     c["package"],
            **custo,
            "alert":       alerta["alerted"],
            "percent_used": alerta["percent_used"],
        }
        results.append(item)
        total_brl += custo["custo_estimado"]

    results.sort(key=lambda x: x["custo_estimado"], reverse=True)

    return jsonify({
        "total_custo_brl": round(total_brl, 2),
        "clients":         results,
        "count":           len(results),
    })


@dashboard_bp.route("/admin/followup/status", methods=["GET"])
def followup_status():
    """Retorna status do scheduler de follow-ups (admin only)."""
    user = session.get("user")
    if not user or user["role"] != "admin":
        return jsonify({"error": "Acesso restrito ao admin"}), 403

    from modules.followup import get_scheduler_status, process_followups

    # Permite forçar execução manual (útil para testes)
    if request.args.get("run_now") == "1":
        process_followups()
        return jsonify({"message": "Follow-ups processados manualmente.", **get_scheduler_status()})

    return jsonify(get_scheduler_status())


@dashboard_bp.route("/admin/followup/leads", methods=["GET"])
def followup_leads_pending():
    """Lista leads com follow-up pendente (admin only)."""
    user = session.get("user")
    if not user or user["role"] != "admin":
        return jsonify({"error": "Acesso restrito ao admin"}), 403

    from database import get_connection
    from datetime import datetime, timezone

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.id, l.client_id, c.name as client_name,
               l.phone, l.classification, l.score, l.status,
               l.summary, l.created_at, l.updated_at
        FROM leads l
        JOIN clients c ON c.id = l.client_id
        WHERE l.status IN ('new', 'contacted')
        ORDER BY l.classification DESC, l.score DESC
        LIMIT 50
    """)
    leads = cursor.fetchall()
    conn.close()

    now = datetime.now(timezone.utc)

    enriched = []
    for lead in leads:
        created = lead.get("created_at", "")
        # Calcular horas desde criação para exibição
        try:
            from modules.followup import _parse_dt
            dt = _parse_dt(created)
            hours_old = round((now - dt).total_seconds() / 3600, 1)
        except Exception:
            hours_old = 0

        enriched.append({
            **dict(lead),
            "hours_old": hours_old,
        })

    return jsonify({
        "total":  len(enriched),
        "leads":  enriched,
    })

