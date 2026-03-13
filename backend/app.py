"""
MFL Digital Solutions — Servidor Principal (v2)
================================================
Arquitetura App Factory com segurança melhorada:
- CORS restrito por ambiente
- Rate limiting nas rotas críticas
- pathlib em vez de os.path
- Catch-all para React SPA
- Configuração por ambiente
"""

import os
import secrets
from pathlib import Path
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

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
        *_EXTRA_ORIGINS,   # URLs do Vercel ou domínios customizados
    ]
)


def create_app():
    """App Factory — cria e configura a instância Flask."""
    app = Flask(__name__)

    # ── Segurança ──────────────────────────────────────────────────────────────
    secret = os.getenv("SECRET_KEY")
    if not secret:
        if _ENV == "production":
            raise RuntimeError("SECRET_KEY não definida! Configure o .env antes de produção.")
        secret = secrets.token_urlsafe(32)   # apenas em dev

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
             r"/webhook/*": {"origins": ALLOWED_ORIGINS},
         })

    # ── Rate Limiting ──────────────────────────────────────────────────────────
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per minute"],
        storage_uri="memory://",
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

    # Aplicar limites específicos às rotas críticas
    limiter.limit("10 per minute")(auth_bp)
    limiter.limit("60 per minute")(whatsapp_bp)

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
            "version":   "2.0",
            "env":       _ENV,
            "scheduler": get_scheduler_status(),
        }), 200

    # ── Catch-all → React SPA ─────────────────────────────────────────────────
    # Serve qualquer rota desconhecida como React SPA (deve ficar por último!)
    @app.route("/<path:path>", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        # Assets buildados pelo Vite (js/css)
        if path.startswith("assets/"):
            asset_file = path[len("assets/"):]
            return send_from_directory(REACT_DIR / "assets", asset_file)
        # Arquivos estáticos da raiz do dist (logo, favicon, etc.)
        static_file = REACT_DIR / path
        if path and static_file.is_file():
            return send_from_directory(REACT_DIR, path)
        # Qualquer outra rota → index.html da SPA
        return send_from_directory(REACT_DIR, "index.html")

    # ── Handlers de erro globais ──────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso não encontrado"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Erro interno do servidor"}), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Muitas requisições. Tente novamente em breve."}), 429

    return app


# ── Ponto de entrada ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    from database import init_db
    init_db()

    application = create_app()

    # ── Iniciar scheduler de follow-ups ───────────────────────────────────
    from modules.followup import start_scheduler, stop_scheduler
    start_scheduler()

    import atexit
    atexit.register(stop_scheduler)

    port = int(os.getenv("FLASK_PORT", 5000))
    print("=" * 52)
    print("  MFL Digital Solutions — Servidor v2")
    print("=" * 52)
    print(f"  URL:       http://localhost:{port}")
    print(f"  Ambiente:  {_ENV}")
    print(f"  CORS:      {', '.join(ALLOWED_ORIGINS)}")
    print("=" * 52)

    application.run(
        host="0.0.0.0",
        port=port,
        debug=_ENV == "development",
    )
