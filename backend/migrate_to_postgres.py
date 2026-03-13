"""
MFL Digital Solutions — Script de Migração SQLite → PostgreSQL
==============================================================
Executa a migração completa dos dados do SQLite local
para o PostgreSQL (Supabase ou Railway).

USO:
    python migrate_to_postgres.py

PRÉ-REQUISITOS:
    1. pip install psycopg2-binary
    2. Configurar DATABASE_URL no .env:
       DATABASE_URL=postgresql://user:pass@host:5432/dbname

O script preserva todos os dados existentes.
"""

import os
import sqlite3
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = Path(__file__).parent.parent / "data" / "mfl_digital.db"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def check_prereqs():
    if not DATABASE_URL:
        print("❌ DATABASE_URL não configurada no .env")
        print("   Adicione: DATABASE_URL=postgresql://user:pass@host:5432/dbname")
        sys.exit(1)

    if not SQLITE_PATH.exists():
        print(f"⚠️  SQLite não encontrado em {SQLITE_PATH}")
        print("   O banco PostgreSQL será inicializado vazio.")
        return False

    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 não instalado. Execute: pip install psycopg2-binary")
        sys.exit(1)

    return True


def get_sqlite_conn():
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_pg_conn():
    import psycopg2
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)


def migrate():
    print("\n🚀 Iniciando migração SQLite → PostgreSQL\n")

    has_sqlite = check_prereqs()

    # 1. Inicializa schema PostgreSQL
    print("📐 Criando schema PostgreSQL...")
    import database  # importa o novo database.py
    database.DATABASE_URL = DATABASE_URL
    database._IS_POSTGRES = True

    pg = get_pg_conn()
    pg.autocommit = False
    pgc = pg.cursor()

    database._init_postgres(type('FakeCursor', (), {'_raw': pgc})())
    pg.commit()
    print("   ✅ Schema criado.\n")

    if not has_sqlite:
        print("✅ Banco PostgreSQL inicializado (sem dados para migrar).")
        pg.close()
        return

    # 2. Migra dados
    sq = get_sqlite_conn()
    sqc = sq.cursor()

    tables = [
        ("clients",              "id, name, niche, phone, email, package, status, whatsapp_number, username, password_hash, created_at"),
        ("agents",               "id, client_id, name, whatsapp, specialty, active"),
        ("leads",                "id, client_id, phone, name, classification, category, urgency, budget, property_type, neighborhood, summary, raw_message, assigned_agent, status, created_at, updated_at"),
        ("conversations",        "id, lead_id, direction, message, created_at"),
        ("health_score_history", "id, client_id, week, health_score, label, velocity, qual_rate, conversion, recency, trend, alerted, email_sent, recorded_at"),
    ]

    for table, cols in tables:
        # Verifica se a tabela existe no SQLite
        sqc.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not sqc.fetchone():
            print(f"   ⏭️  Tabela '{table}' não existe no SQLite — pulando.")
            continue

        sqc.execute(f"SELECT {cols} FROM {table}")
        rows = sqc.fetchall()

        if not rows:
            print(f"   📭 '{table}': vazia — OK.")
            continue

        col_list = [c.strip() for c in cols.split(",")]
        placeholders = ", ".join(["%s"] * len(col_list))
        col_str = ", ".join(col_list)

        # Desabilita constraints temporariamente para migração com IDs existentes
        pgc.execute(f"ALTER TABLE {table} DISABLE TRIGGER ALL") if table != "rate_limit_log" else None

        migrated = 0
        errors = 0
        for row in rows:
            try:
                values = tuple(row[c] for c in col_list)
                pgc.execute(
                    f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING",
                    values
                )
                migrated += 1
            except Exception as e:
                errors += 1
                print(f"     ⚠️  Erro na linha {dict(row).get('id', '?')}: {e}")

        if table != "rate_limit_log":
            pgc.execute(f"ALTER TABLE {table} ENABLE TRIGGER ALL")

        # Reseta a sequence do ID após inserir com IDs explícitos
        pgc.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table}), 1)
            )
        """)

        pg.commit()
        print(f"   ✅ '{table}': {migrated} registros migrados ({errors} erros).")

    sq.close()
    pg.close()

    print("\n🎉 Migração concluída com sucesso!")
    print("   Próximo passo: configure DATABASE_URL no .env e reinicie o servidor.")


if __name__ == "__main__":
    migrate()
