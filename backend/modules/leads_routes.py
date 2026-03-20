"""
MFL Digital Solutions — Rotas de Leads (API)
=============================================
CRUD de leads para o dashboard.
Todas as rotas exigem autenticação via sessão Flask.
Clientes só veem seus próprios leads (isolamento por client_id).
"""

import os
import sys
from flask import Blueprint, jsonify, request, session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_leads, get_connection, get_followup_log

leads_bp = Blueprint("leads", __name__)


# ── Guard de Autenticação Global ──────────────────────────────────────────────

@leads_bp.before_request
def require_auth():
    """Aplica autenticação em TODAS as rotas deste blueprint."""
    if not session.get("user"):
        return jsonify({"error": "Não autenticado"}), 401


def _assert_lead_access(lead: dict) -> bool:
    """
    Verifica se o usuário logado tem direito de ver/editar este lead.
    Admin → acesso total. Cliente → somente leads do seu client_id.
    """
    user = session.get("user")
    if user["role"] == "admin":
        return True
    return lead.get("client_id") == user.get("client_id")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@leads_bp.route("/", methods=["GET"])
def list_leads():
    """Lista leads com filtros opcionais. Clientes só veem os próprios."""
    user           = session.get("user")
    classification = request.args.get("classification")
    status         = request.args.get("status")
    search         = request.args.get("q", "").strip()
    limit          = min(request.args.get("limit", 50, type=int), 500)

    # Clientes têm client_id fixo pelo próprio (sem opção de sobrescrever via query param)
    if user["role"] == "client":
        client_id = user["client_id"]
    else:
        client_id = request.args.get("client_id", type=int)  # admin pode filtrar por cliente

    leads = get_leads(client_id=client_id, classification=classification, limit=limit)

    if status:
        leads = [l for l in leads if l.get("status") == status]
    if search:
        sl = search.lower()
        leads = [l for l in leads if sl in (l.get("phone") or "").lower()
                 or sl in (l.get("summary") or "").lower()
                 or sl in (l.get("neighborhood") or "").lower()]

    return jsonify({"leads": leads, "total": len(leads)})


@leads_bp.route("/<int:lead_id>", methods=["GET"])
def get_lead(lead_id):
    """Retorna detalhes de um lead específico."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Lead não encontrado"}), 404

    lead = dict(row)
    if not _assert_lead_access(lead):
        return jsonify({"error": "Acesso negado"}), 403

    return jsonify(lead)


@leads_bp.route("/<int:lead_id>", methods=["PATCH"])
def update_lead(lead_id):
    """
    Atualiza campos editáveis de um lead.
    Campos aceitos: status, classification, category, urgency,
                    budget, property_type, neighborhood, summary, score
    """
    # Verificar acesso antes de processar
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT client_id FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Lead não encontrado"}), 404
    if not _assert_lead_access(dict(row)):
        return jsonify({"error": "Acesso negado"}), 403

    data = request.get_json() or {}

    EDITABLE = {
        "status", "classification", "category", "urgency",
        "budget", "property_type", "neighborhood", "summary", "score"
    }
    VALID_STATUSES         = {"new", "contacted", "converted", "lost"}
    VALID_CLASSIFICATIONS  = {"hot", "warm", "cold"}

    updates = {k: v for k, v in data.items() if k in EDITABLE}
    if not updates:
        return jsonify({"error": "Nenhum campo válido para atualizar"}), 400

    if "status" in updates and updates["status"] not in VALID_STATUSES:
        return jsonify({"error": f"Status inválido. Use: {sorted(VALID_STATUSES)}"}), 400
    if "classification" in updates and updates["classification"] not in VALID_CLASSIFICATIONS:
        return jsonify({"error": f"Classification inválida. Use: {sorted(VALID_CLASSIFICATIONS)}"}), 400

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values     = list(updates.values()) + [lead_id]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE leads SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "lead_id": lead_id, "updated": updates})


@leads_bp.route("/<int:lead_id>/conversations", methods=["GET"])
def get_lead_conversations(lead_id):
    """Retorna o histórico de conversas do lead."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT client_id FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Lead não encontrado"}), 404
    if not _assert_lead_access(dict(row)):
        conn.close()
        return jsonify({"error": "Acesso negado"}), 403

    cursor.execute(
        "SELECT * FROM conversations WHERE lead_id = ? ORDER BY created_at ASC",
        (lead_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"conversations": [dict(r) for r in rows]})


@leads_bp.route("/<int:lead_id>/followup-log", methods=["GET"])
def get_lead_followup_log(lead_id):
    """
    Retorna o log completo de tentativas de follow-up de um lead.
    Útil para auditoria: por que este lead não recebeu follow-up?
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT client_id FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Lead não encontrado"}), 404
    if not _assert_lead_access(dict(row)):
        return jsonify({"error": "Acesso negado"}), 403

    limit = request.args.get("limit", 20, type=int)
    logs  = get_followup_log(lead_id=lead_id, limit=limit)
    return jsonify({"lead_id": lead_id, "followup_log": logs, "total": len(logs)})


@leads_bp.route("/<int:lead_id>/status", methods=["PATCH"])
def update_lead_status(lead_id):
    """Atalho para atualizar somente o status de um lead."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT client_id FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Lead não encontrado"}), 404
    if not _assert_lead_access(dict(row)):
        return jsonify({"error": "Acesso negado"}), 403

    data       = request.get_json() or {}
    new_status = data.get("status")

    valid_statuses = ["new", "contacted", "converted", "lost"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Status inválido. Use: {valid_statuses}"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_status, lead_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "lead_id": lead_id, "new_status": new_status})
