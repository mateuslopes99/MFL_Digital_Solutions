# ─────────────────────────────────────────────
# MFL Digital Solutions — Configuração de Produção
# Usando Waitress (compatível com Windows/Linux)
# ─────────────────────────────────────────────
# Uso: waitress-serve --call "app:create_app"
#   ou: python serve.py
# ─────────────────────────────────────────────

import os
from waitress import serve
from app import create_app
from database import init_db

if __name__ == "__main__":
    init_db()
    app = create_app()

    port = int(os.getenv("FLASK_PORT", 5000))
    threads = int(os.getenv("SERVER_THREADS", 4))

    print("=" * 52)
    print("  MFL Digital Solutions — Servidor de Produção")
    print("=" * 52)
    print(f"  Host:    0.0.0.0:{port}")
    print(f"  Threads: {threads}")
    print(f"  Env:     {os.getenv('FLASK_ENV', 'production')}")
    print("=" * 52)

    serve(app, host="0.0.0.0", port=port, threads=threads)
