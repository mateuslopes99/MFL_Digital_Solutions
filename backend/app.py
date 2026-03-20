"""
MFL Digital Solutions — Servidor Principal (v3)
================================================
Correções aplicadas (20/03/2026):
- Logging estruturado com basicConfig
- init_db() e start_scheduler() dentro de app_context (evita workers duplicados)
- Rate limiting com suporte a Redis (fallback para memória)
- 404 de API separado do catch-all da SPA
- CORS restrito por ambiente
- SESSION segura (HttpOnly, SameSite, Secure em produção)
"""

import os
import logging
import secrets
from pathlib import Path
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

# ── Logging estruturado ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Paths (pathlib) ────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
LANDING_DIR = BASE_DIR / ".." / "frontend" / "landing"
LOGO_DIR    = BASE_DIR / ".." / "logo"
REACT_DIR   = BASE_DIR / ".." / "frontend" / "app" / "dist"

# ── Origens permitidas por ambiente ───────────────────────────────────────────
_ENV = os.getenv("FLASK_ENV", "development")
_EXTRA_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS_EXTRA", "").split(",") if o.strip()]

ALLOWED_ORIGINS = (
    ["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:5000"]
    if _ENV == "development"
    else [
        "https://mfldigitalsolutions.com.br",
        "https://app.mfldigitalsolutions.com.br",
        "https://mfl-digital.vercel.app",
        *_EXTRA_ORIGINS,
    ]
)


def create_app():
    """App Factory — cria e configura a instância Flask."""
    app = Flask(__name__)

    # ── Segurança ──────────────────────────────────────────────────────────────
    secret = os.getenv("SECRET_KEY")
    if not secret:
        if _ENV == "production":
            raise RuntimeError("SECRET_KEY não definida! Configure no Railway antes de produção.")
        secret = secrets.token_urlsafe(32)   # apenas em dev
        logger.warning("[CONFIG] SECRET_KEY não definida — usando chave temporária (só em dev).")

    app.config.update(
        SECRET_KEY=secret,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_ENV == "production",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        PROPAGATE_EXCEPTIONS=True,
    )

    # ── CORS restrito ──────────────────────────────────────────────────────────
    CORS(app,
         supports_credentials=True,
         origins=ALLOWED_ORIGINS,
         resources={
             r"/api/*":     {"origins": ALLOWED_ORIGINS},
             r"/webhook/*": {"origins": "*"},   # Webhooks externos não têm Origin fixo
         })

    # ── Rate Limiting (Redis em produção, memória em dev) ──────────────────────
    redis_url     = os.getenv("REDIS_URL", "")
    storage_uri   = redis_url if redis_url else "memory://"
    if not redis_url and _ENV == "production":
        logger.warning("[RATE LIMIT] REDIS_URL não configurado — usando memória (zera em restart).")

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per minute"],
        storage_uri=storage_uri,
    )

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from modules.whatsapp_routes  import whatsapp_bp
    from modules.dashboard_routes import dashboard_bp
    from modules.leads_routes     import leads_bp
    from modules.auth_routes      import auth_bp
    from modules.clients_routes   import clients_bp

    app.register_blueprint(whatsapp_bp,  url_prefix="/webhook")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(leads_bp,     url_prefix="/api/leads")
    app.register_blueprint(auth_bp,      url_prefix="/api/auth")
    app.register_blueprint(clients_bp,   url_prefix="/api/clients")

    # Limites específicos nas rotas críticas
    limiter.limit("10 per minute")(auth_bp)
    limiter.limit("60 per minute")(whatsapp_bp)

    # ── DB e Scheduler dentro do app_context (evita duplicação em multi-worker) ─
    with app.app_context():
        try:
            from database import init_db
            init_db()
            logger.info("[DB] Banco de dados inicializado.")
        except Exception as exc:
            logger.error("[DB] Falha ao inicializar banco: %s", exc)
            if _ENV == "production":
                raise

        try:
            from modules.followup import start_scheduler
            start_scheduler()
            logger.info("[SCHEDULER] Scheduler de follow-ups iniciado.")
        except Exception as exc:
            logger.error("[SCHEDULER] Falha ao iniciar scheduler: %s", exc)

    # ── Arquivos estáticos da landing ──────────────────────────────────────────
    @app.route("/")
    def landing():
        return send_from_directory(LANDING_DIR, "index.html")

    @app.route("/logo/<path:filename>")
    def serve_logo(filename):
        return send_from_directory(LOGO_DIR, filename)

    @app.route("/static/landing/<path:filename>")
    def serve_landing_static(filename):
        return send_from_directory(LANDING_DIR, filename)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        from modules.followup import get_scheduler_status
        return jsonify({
            "status":    "healthy",
            "version":   "3.0",
            "env":       _ENV,
            "scheduler": get_scheduler_status(),
        }), 200

    # ── Catch-all → React SPA ─────────────────────────────────────────────────
    # Rotas /api/* e /webhook/* NUNCA chegam aqui (blueprints têm prioridade).
    # Rota de API retornando 404 cai no errorhandler(404) → JSON correto.
    @app.route("/<path:path>", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        # Assets buildados pelo Vite (js/css)
        if path.startswith("assets/"):
            asset_file = path[len("assets/"):]
            return send_from_directory(REACT_DIR / "assets", asset_file)
        # Arquivos estáticos da raiz do dist
        static_file = REACT_DIR / path
        if path and static_file.is_file():
            return send_from_directory(REACT_DIR, path)
        # Qualquer outra rota → index.html da SPA
        return send_from_directory(REACT_DIR, "index.html")

    # ── Handlers de erro globais ──────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        # Se a rota começa com /api/ ou /webhook/, retorna JSON (erro real de API)
        if request.path.startswith("/api/") or request.path.startswith("/webhook/"):
            return jsonify({"error": "Rota não encontrada"}), 404
        # Caso contrário, deixa o catch-all da SPA tratar
        return serve_react(request.path.lstrip("/"))

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("[500] Erro interno: %s", e)
        return jsonify({"error": "Erro interno do servidor"}), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Muitas requisições. Tente novamente em breve."}), 429

    logger.info("[BOOT] MFL Digital Solutions v3 inicializado — Ambiente: %s", _ENV)
    return app


# ── Inicialização Global para WSGI (Produção) ──────────────────────────────────
app = create_app()

import atexit
from modules.followup import stop_scheduler
atexit.register(stop_scheduler)


# ── Ponto de entrada (Desenvolvimento) ─────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    logger.info("=" * 52)
    logger.info("  MFL Digital Solutions — Servidor v3")
    logger.info("  URL:      http://localhost:%d", port)
    logger.info("  Ambiente: %s", _ENV)
    logger.info("  CORS:     %s", ", ".join(ALLOWED_ORIGINS))
    logger.info("=" * 52)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=_ENV == "development",
    )
