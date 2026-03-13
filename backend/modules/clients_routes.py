"""
MFL Digital Solutions — CRUD de Clientes
=========================================
Rotas para criar, listar, atualizar e desativar clientes.
Somente acessíveis pelo Admin.
"""

import os
import sys
import hashlib
from flask import Blueprint, request, jsonify, session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from modules.health_score import calculate_health_score

clients_bp = Blueprint("clients", __name__)


# ── Utilitários ────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def require_admin():
    user = session.get("user")
    return user and user.get("role") == "admin"


PLAN_TO_MRR = {
    "starter":    790,
    "basico":     1490,
    "pro":        2790,
    "enterprise": 5490,
}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@clients_bp.route("/", methods=["GET"])
def list_clients():
    """Lista todos os clientes (admin) ou apenas o próprio (cliente)."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    conn   = get_connection()
    cursor = conn.cursor()

    if user["role"] == "admin":
        cursor.execute("""
            SELECT id, name, niche, phone, email, package, status,
                   whatsapp_number, username, created_at
            FROM clients
            ORDER BY created_at DESC
        """)
    else:
        cursor.execute("""
            SELECT id, name, niche, phone, email, package, status,
                   whatsapp_number, username, created_at
            FROM clients WHERE id = ?
        """, (user["client_id"],))

    rows = [dict(r) for r in cursor.fetchall()]

    # Adiciona MRR e health score calculado
    for r in rows:
        r["mrr"] = PLAN_TO_MRR.get(r.get("package", "pro"), 2790)
        hs = calculate_health_score(r["id"])
        r["health"]     = hs["health_score"]
        r["churn_risk"] = hs["churn_risk"]
        r["health_label"] = hs["label"]

    conn.close()
    return jsonify({"clients": rows, "total": len(rows)})


@clients_bp.route("/", methods=["POST"])
def create_client():
    """Cria um novo cliente. Somente admin."""
    if not require_admin():
        return jsonify({"error": "Acesso restrito ao administrador"}), 403

    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Campo 'name' é obrigatório"}), 400

    name     = data["name"].strip()
    username = data.get("username", name.lower().replace(" ", "_").replace(".", ""))
    password = data.get("password", "mfl2026")  # senha padrão inicial

    conn   = get_connection()
    cursor = conn.cursor()

    # Verifica se username já existe
    cursor.execute("SELECT id FROM clients WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": f"Username '{username}' já está em uso"}), 409

    cursor.execute("""
        INSERT INTO clients
            (name, niche, phone, email, package, status,
             whatsapp_number, username, password_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        data.get("niche", "Imobiliária"),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("package", "pro"),
        data.get("status", "active"),
        data.get("whatsapp_number", ""),
        username,
        hash_password(password)
    ))
    client_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "success":   True,
        "id":        client_id,
        "username":  username,
        "password":  password,  # Retorna para o admin anotar
        "message":   f"Cliente '{name}' criado com sucesso"
    }), 201


@clients_bp.route("/<int:client_id>", methods=["GET"])
def get_client(client_id):
    """Retorna dados de um cliente específico."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    # Cliente só pode ver seus próprios dados
    if user["role"] == "client" and user["client_id"] != client_id:
        return jsonify({"error": "Acesso negado"}), 403

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, niche, phone, email, package, status,
               whatsapp_number, username, created_at
        FROM clients WHERE id = ?
    """, (client_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Cliente não encontrado"}), 404

    result = dict(row)
    result["mrr"] = PLAN_TO_MRR.get(result.get("package", "pro"), 2790)
    hs = calculate_health_score(client_id)
    result["health"]       = hs["health_score"]
    result["churn_risk"]   = hs["churn_risk"]
    result["health_label"] = hs["label"]
    return jsonify(result)


@clients_bp.route("/<int:client_id>/health-score", methods=["GET"])
def get_health_score(client_id):
    """Retorna o health score detalhado de um cliente."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Não autenticado"}), 401
    if user["role"] == "client" and user["client_id"] != client_id:
        return jsonify({"error": "Acesso negado"}), 403

    hs = calculate_health_score(client_id)
    return jsonify(hs)


@clients_bp.route("/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    """Atualiza dados de um cliente."""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Não autenticado"}), 401

    # Clientes só podem atualizar a si mesmos e somente campos específicos
    if user["role"] == "client":
        if user["client_id"] != client_id:
            return jsonify({"error": "Acesso negado"}), 403
        allowed = ["phone", "email"]  # campos que o cliente pode editar
    else:
        allowed = ["name", "niche", "phone", "email", "package",
                   "status", "whatsapp_number", "username"]

    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    updates = []
    params  = []
    for field in allowed:
        if field in data:
            updates.append(f"{field} = ?")
            params.append(data[field])

    if "password" in data and require_admin():
        updates.append("password_hash = ?")
        params.append(hash_password(data["password"]))

    if not updates:
        return jsonify({"error": "Nenhum campo válido para atualizar"}), 400

    params.append(client_id)
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE clients SET {', '.join(updates)} WHERE id = ?",
        params
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Cliente atualizado"})


@clients_bp.route("/<int:client_id>", methods=["DELETE"])
def deactivate_client(client_id):
    """Desativa um cliente (soft delete). Somente admin."""
    if not require_admin():
        return jsonify({"error": "Acesso restrito ao administrador"}), 403

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clients SET status = 'inactive' WHERE id = ?",
        (client_id,)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Cliente desativado"})


@clients_bp.route("/<int:client_id>/reset-password", methods=["POST"])
def reset_password(client_id):
    """Admin redefine a senha de um cliente."""
    if not require_admin():
        return jsonify({"error": "Acesso restrito ao administrador"}), 403

    data     = request.get_json()
    new_pass = data.get("password", "mfl2026")

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clients SET password_hash = ? WHERE id = ?",
        (hash_password(new_pass), client_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Senha redefinida para '{new_pass}'"})
