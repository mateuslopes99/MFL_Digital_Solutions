"""
MFL Digital Solutions — Autenticação
======================================
Login para Admin (credenciais no .env) e Clientes (DB).
Usa sessão Flask com cookie HttpOnly.
"""

import os
import hashlib
import sys
from flask import Blueprint, request, jsonify, session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection

auth_bp = Blueprint("auth", __name__)


# ── Utilitário ─────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_admin_credentials(username: str, password: str) -> bool:
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASS", "mfl2026")
    return username == admin_user and password == admin_pass


# ── Endpoints ──────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Autenticar usuário (admin ou cliente).
    Body JSON: { "username": "...", "password": "...", "role": "admin"|"client" }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Dados inválidos"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role     = data.get("role", "admin")

    if not username or not password:
        return jsonify({"success": False, "error": "Preencha usuário e senha"}), 400

    # ── Admin ──────────────────────────────────────────────────────────────────
    if role == "admin":
        if check_admin_credentials(username, password):
            session.permanent = True
            session["user"] = {
                "username":  username,
                "role":      "admin",
                "name":      "Administrador MFL",
                "client_id": None
            }
            return jsonify({"success": True, "role": "admin"})
        return jsonify({"success": False, "error": "Credenciais de administrador inválidas"}), 401

    # ── Cliente ────────────────────────────────────────────────────────────────
    if role == "client":
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, niche, package, username, password_hash FROM clients "
                "WHERE username = ? AND status = 'active' LIMIT 1",
                (username,)
            )
            client = cursor.fetchone()
            conn.close()
        except Exception as e:
            return jsonify({"success": False, "error": f"Erro no banco: {str(e)}"}), 500

        if client and client["password_hash"] == hash_password(password):
            session.permanent = True
            session["user"] = {
                "username":  username,
                "role":      "client",
                "name":      client["name"],
                "niche":     client["niche"],
                "package":   client["package"],
                "client_id": client["id"]
            }
            return jsonify({
                "success": True,
                "role":      "client",
                "client_id": client["id"],
                "name":      client["name"]
            })

        return jsonify({"success": False, "error": "Usuário ou senha incorretos"}), 401

    return jsonify({"success": False, "error": "Papel inválido"}), 400


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/me", methods=["GET"])
def me():
    """Retorna dados do usuário autenticado ou 401."""
    user = session.get("user")
    if not user:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, **user})


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    """Permite ao cliente mudar própria senha."""
    user = session.get("user")
    if not user or user["role"] != "client":
        return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()
    current  = data.get("current_password", "")
    new_pass = data.get("new_password", "")

    if len(new_pass) < 6:
        return jsonify({"error": "Nova senha deve ter pelo menos 6 caracteres"}), 400

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM clients WHERE id = ?",
        (user["client_id"],)
    )
    row = cursor.fetchone()

    if not row or row["password_hash"] != hash_password(current):
        conn.close()
        return jsonify({"error": "Senha atual incorreta"}), 401

    cursor.execute(
        "UPDATE clients SET password_hash = ? WHERE id = ?",
        (hash_password(new_pass), user["client_id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})
