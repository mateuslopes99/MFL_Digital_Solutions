"""
MFL Digital Solutions — Banco de Dados (v2 — Dual DB)
======================================================
Suporta dois modos automaticamente via variável de ambiente:

  MODO PRODUÇÃO  → DATABASE_URL=postgresql://... no .env
  MODO DEV LOCAL → DATABASE_URL ausente → usa SQLite (data/mfl_digital.db)

Compatibilidade garantida: todas as queries usam ? como placeholder,
que este módulo traduz para %s automaticamente quando em PostgreSQL.
"""

import os
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuração de modo ──────────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
_IS_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

# SQLite fallback (dev local)
_SQLITE_PATH = Path(__file__).parent.parent / "data" / "mfl_digital.db"


# ── Pool de conexão PostgreSQL (lazy singleton) ───────────────────────────────

_pg_pool = None

def _get_pg_pool():
    global _pg_pool
    if _pg_pool is None:
        try:
            from psycopg2 import pool
            # Normaliza postgres:// → postgresql:// (Railway usa postgres://)
            url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            _pg_pool = pool.SimpleConnectionPool(1, 10, url)
            logger.info("[DB] Pool PostgreSQL iniciado.")
        except ImportError:
            raise RuntimeError(
                "[DB] psycopg2 não instalado. Execute: pip install psycopg2-binary"
            )
    return _pg_pool


# ── Wrapper de conexão ────────────────────────────────────────────────────────

class _PgConn:
    """
    Wrapper sobre conexão psycopg2 que imita a interface do sqlite3.Connection,
    incluindo row_factory para retornar dicionários nos fetchall/fetchone.
    """
    def __init__(self, raw):
        self._raw = raw
        self.cursor = lambda: _PgCursor(self._raw.cursor())

    def commit(self):   self._raw.commit()
    def rollback(self): self._raw.rollback()
    def close(self):    _get_pg_pool().putconn(self._raw)


class _PgCursor:
    """
    Wrapper sobre cursor psycopg2 com:
      - Tradução automática de ? → %s nas queries
      - fetchone/fetchall retornam dicts (como sqlite3.Row)
      - Atributo lastrowid via RETURNING
    """
    def __init__(self, raw):
        self._raw = raw
        self.lastrowid = None

    def _translate(self, query: str) -> str:
        """Converte placeholders SQLite (?) para PostgreSQL (%s)."""
        return query.replace("?", "%s")

    def _translate_autoincrement(self, query: str) -> str:
        """Converte sintaxe SQLite → PostgreSQL."""
        q = query
        q = q.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        q = q.replace("DATETIME DEFAULT CURRENT_TIMESTAMP", "TIMESTAMPTZ DEFAULT NOW()")
        q = q.replace("INTEGER DEFAULT 1", "BOOLEAN DEFAULT TRUE")
        return q

    def execute(self, query: str, params=()):
        q = self._translate(query)
        # Para INSERT, adiciona RETURNING id para capturar lastrowid
        if q.strip().upper().startswith("INSERT") and "RETURNING" not in q.upper():
            q = q.rstrip().rstrip(";") + " RETURNING id"
            self._raw.execute(q, params)
            row = self._raw.fetchone()
            self.lastrowid = row[0] if row else None
        else:
            self._raw.execute(q, params)

    def executescript(self, script: str):
        for stmt in script.split(";"):
            stmt = stmt.strip()
            if stmt:
                self._raw.execute(stmt)

    def fetchone(self):
        row = self._raw.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in self._raw.description]
        return dict(zip(cols, row))

    def fetchall(self):
        rows = self._raw.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in self._raw.description]
        return [dict(zip(cols, r)) for r in rows]

    def __getitem__(self, key):
        return self._raw.__getitem__(key)


# ── API pública ───────────────────────────────────────────────────────────────

def get_connection():
    """
    Retorna conexão com o banco ativo (PostgreSQL ou SQLite).
    Em PostgreSQL, retorna wrapper com interface compatível.
    Em SQLite, retorna conexão nativa com row_factory=Row.
    """
    if _IS_POSTGRES:
        raw = _get_pg_pool().getconn()
        raw.autocommit = False
        return _PgConn(raw)
    else:
        Path(_SQLITE_PATH.parent).mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(_SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    Compatível com PostgreSQL e SQLite.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    if _IS_POSTGRES:
        _init_postgres(cursor)
    else:
        _init_sqlite(cursor)

    conn.commit()
    conn.close()
    mode = "PostgreSQL" if _IS_POSTGRES else "SQLite"
    print(f"[DB] Banco de dados inicializado com sucesso. [{mode}]")


def _init_sqlite(cursor):
    """Schema SQLite — para desenvolvimento local."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            niche           TEXT DEFAULT 'Imobiliária',
            phone           TEXT,
            email           TEXT,
            package         TEXT DEFAULT 'pro',
            status          TEXT DEFAULT 'active',
            whatsapp_number TEXT,
            username        TEXT UNIQUE,
            password_hash   TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    for col in [
        "ALTER TABLE clients ADD COLUMN whatsapp_number TEXT",
        "ALTER TABLE clients ADD COLUMN username TEXT",
        "ALTER TABLE clients ADD COLUMN password_hash TEXT",
    ]:
        try:
            cursor.execute(col)
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id   INTEGER NOT NULL,
            name        TEXT NOT NULL,
            whatsapp    TEXT NOT NULL,
            specialty   TEXT,
            active      INTEGER DEFAULT 1,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id       INTEGER NOT NULL,
            phone           TEXT NOT NULL,
            name            TEXT,
            classification  TEXT DEFAULT 'cold',
            category        TEXT,
            urgency         TEXT,
            budget          TEXT,
            property_type   TEXT,
            neighborhood    TEXT,
            summary         TEXT,
            raw_message     TEXT,
            score           INTEGER DEFAULT 0,
            sentiment       TEXT DEFAULT 'neutro',
            lgpd_consent    INTEGER DEFAULT 0,
            conversation_id TEXT,
            assigned_agent  INTEGER,
            status          TEXT DEFAULT 'new',
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (assigned_agent) REFERENCES agents(id)
        )
    """)

    # Migrations seguras para colunas novas
    for col in [
        "ALTER TABLE leads ADD COLUMN score INTEGER DEFAULT 0",
        "ALTER TABLE leads ADD COLUMN sentiment TEXT DEFAULT 'neutro'",
        "ALTER TABLE leads ADD COLUMN lgpd_consent INTEGER DEFAULT 0",
        "ALTER TABLE leads ADD COLUMN conversation_id TEXT",
    ]:
        try:
            cursor.execute(col)
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id        INTEGER NOT NULL,
            conversation_id TEXT,
            direction      TEXT NOT NULL,
            message        TEXT NOT NULL,
            model_used     TEXT,
            tokens_used    INTEGER DEFAULT 0,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)

    # Migrations seguras para colunas novas em conversations (bancos antigos)
    for col in [
        "ALTER TABLE conversations ADD COLUMN conversation_id TEXT",
        "ALTER TABLE conversations ADD COLUMN model_used TEXT",
        "ALTER TABLE conversations ADD COLUMN tokens_used INTEGER DEFAULT 0",
    ]:
        try:
            cursor.execute(col)
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_score_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id     INTEGER NOT NULL,
            week          TEXT NOT NULL,
            health_score  INTEGER NOT NULL,
            label         TEXT,
            velocity      INTEGER DEFAULT 0,
            qual_rate     INTEGER DEFAULT 0,
            conversion    INTEGER DEFAULT 0,
            recency       INTEGER DEFAULT 0,
            trend         INTEGER DEFAULT 0,
            alerted       INTEGER DEFAULT 0,
            email_sent    INTEGER DEFAULT 0,
            recorded_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            UNIQUE (client_id, week)
        )
    """)

    # Tabela de consentimento LGPD
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lgpd_consent (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            phone        TEXT NOT NULL,
            client_id    INTEGER NOT NULL,
            consented    INTEGER DEFAULT 0,
            consented_at DATETIME,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (phone, client_id)
        )
    """)

    # Tabela de rate limiting por telefone
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            phone      TEXT NOT NULL,
            client_id  INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rate_limit_phone_time
        ON rate_limit_log (phone, client_id, created_at)
    """)

    # Tabela de log de follow-ups (auditoria completa)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS followup_log (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id        INTEGER NOT NULL,
            client_id      INTEGER NOT NULL,
            followup_type  TEXT NOT NULL,   -- 'hot_30min', 'warm_24h', 'cold_3d', etc.
            scheduled_time DATETIME,
            executed_time  DATETIME DEFAULT CURRENT_TIMESTAMP,
            status         TEXT DEFAULT 'sent',  -- 'sent' | 'failed' | 'blocked' | 'simulated'
            provider       TEXT,           -- 'evolution' | 'twilio' | 'mock'
            error_msg      TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_followup_log_lead
        ON followup_log (lead_id, followup_type)
    """)

    # Tabela de heartbeat do scheduler (detecta scheduler parado)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduler_heartbeat (
            id          INTEGER PRIMARY KEY CHECK (id = 1),
            last_alive  DATETIME DEFAULT CURRENT_TIMESTAMP,
            jobs_count  INTEGER DEFAULT 0
        )
    """)
    # Insere registro inicial (singleton)
    cursor.execute("""
        INSERT OR IGNORE INTO scheduler_heartbeat (id, jobs_count)
        VALUES (1, 0)
    """)


def _init_postgres(cursor):
    """Schema PostgreSQL — para produção."""
    # Clientes
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id              SERIAL PRIMARY KEY,
            name            TEXT NOT NULL,
            niche           TEXT DEFAULT 'Imobiliária',
            phone           TEXT,
            email           TEXT,
            package         TEXT DEFAULT 'pro',
            status          TEXT DEFAULT 'active',
            whatsapp_number TEXT,
            username        TEXT UNIQUE,
            password_hash   TEXT,
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Corretores
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id          SERIAL PRIMARY KEY,
            client_id   INTEGER NOT NULL REFERENCES clients(id),
            name        TEXT NOT NULL,
            whatsapp    TEXT NOT NULL,
            specialty   TEXT,
            active      BOOLEAN DEFAULT TRUE
        )
    """)

    # Leads
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id              SERIAL PRIMARY KEY,
            client_id       INTEGER NOT NULL REFERENCES clients(id),
            phone           TEXT NOT NULL,
            name            TEXT,
            classification  TEXT DEFAULT 'cold',
            category        TEXT,
            urgency         TEXT,
            budget          TEXT,
            property_type   TEXT,
            neighborhood    TEXT,
            summary         TEXT,
            raw_message     TEXT,
            score           INTEGER DEFAULT 0,
            sentiment       TEXT DEFAULT 'neutro',
            lgpd_consent    BOOLEAN DEFAULT FALSE,
            conversation_id TEXT,
            assigned_agent  INTEGER REFERENCES agents(id),
            status          TEXT DEFAULT 'new',
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            updated_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Índices para performance
    cursor._raw.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_client_id ON leads(client_id)
    """)
    cursor._raw.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_classification ON leads(classification)
    """)
    cursor._raw.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at)
    """)

    # Conversas / Logs estruturados
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id              SERIAL PRIMARY KEY,
            lead_id         INTEGER NOT NULL REFERENCES leads(id),
            conversation_id TEXT,
            direction       TEXT NOT NULL,
            message         TEXT NOT NULL,
            model_used      TEXT,
            tokens_used     INTEGER DEFAULT 0,
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Health Score History
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS health_score_history (
            id           SERIAL PRIMARY KEY,
            client_id    INTEGER NOT NULL REFERENCES clients(id),
            week         TEXT NOT NULL,
            health_score INTEGER NOT NULL,
            label        TEXT,
            velocity     INTEGER DEFAULT 0,
            qual_rate    INTEGER DEFAULT 0,
            conversion   INTEGER DEFAULT 0,
            recency      INTEGER DEFAULT 0,
            trend        INTEGER DEFAULT 0,
            alerted      BOOLEAN DEFAULT FALSE,
            email_sent   BOOLEAN DEFAULT FALSE,
            recorded_at  TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (client_id, week)
        )
    """)

    # Consentimento LGPD
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS lgpd_consent (
            id           SERIAL PRIMARY KEY,
            phone        TEXT NOT NULL,
            client_id    INTEGER NOT NULL REFERENCES clients(id),
            consented    BOOLEAN DEFAULT FALSE,
            consented_at TIMESTAMPTZ,
            created_at   TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (phone, client_id)
        )
    """)

    # Rate limiting por telefone
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit_log (
            id         SERIAL PRIMARY KEY,
            phone      TEXT NOT NULL,
            client_id  INTEGER NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cursor._raw.execute("""
        CREATE INDEX IF NOT EXISTS idx_rate_limit_phone_time
        ON rate_limit_log (phone, client_id, created_at)
    """)

    # Log de follow-ups (auditoria)
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS followup_log (
            id             SERIAL PRIMARY KEY,
            lead_id        INTEGER NOT NULL REFERENCES leads(id),
            client_id      INTEGER NOT NULL,
            followup_type  TEXT NOT NULL,
            scheduled_time TIMESTAMPTZ,
            executed_time  TIMESTAMPTZ DEFAULT NOW(),
            status         TEXT DEFAULT 'sent',
            provider       TEXT,
            error_msg      TEXT
        )
    """)
    cursor._raw.execute("""
        CREATE INDEX IF NOT EXISTS idx_followup_log_lead
        ON followup_log (lead_id, followup_type)
    """)

    # Heartbeat do scheduler
    cursor._raw.execute("""
        CREATE TABLE IF NOT EXISTS scheduler_heartbeat (
            id         INTEGER PRIMARY KEY DEFAULT 1,
            last_alive TIMESTAMPTZ DEFAULT NOW(),
            jobs_count INTEGER DEFAULT 0,
            CHECK (id = 1)
        )
    """)
    cursor._raw.execute("""
        INSERT INTO scheduler_heartbeat (id, jobs_count)
        VALUES (1, 0)
        ON CONFLICT (id) DO NOTHING
    """)


# ── Funções de acesso (API pública mantida idêntica) ──────────────────────────

def insert_lead(client_id, phone, classification, category, urgency, budget,
                property_type, neighborhood, summary, raw_message,
                score=0, sentiment="neutro", conversation_id=None):
    """
    Insere ou atualiza lead (UPSERT por telefone + cliente).

    Lógica:
      - Se já existe um lead com mesmo phone + client_id criado nas últimas 48h
        E o status ainda não é 'converted' → ATUALIZA (reclassifica com o novo score)
      - Caso contrário → INSERT (nova intenção de compra)
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()

    cursor.execute("""
        SELECT id, score FROM leads
        WHERE client_id = ? AND phone = ?
          AND status NOT IN ('converted', 'lost')
          AND created_at >= ?
        ORDER BY created_at DESC LIMIT 1
    """, (client_id, phone, cutoff))
    existing = cursor.fetchone()

    if existing:
        # Atualiza somente se o novo score for >= ao atual (não rebaixa classificação)
        lead_id   = existing["id"]
        new_score = max(score, existing["score"] or 0)
        cursor.execute("""
            UPDATE leads SET
                classification  = ?,
                category        = ?,
                urgency         = ?,
                budget          = ?,
                property_type   = ?,
                neighborhood    = ?,
                summary         = ?,
                raw_message     = ?,
                score           = ?,
                sentiment       = ?,
                conversation_id = ?,
                updated_at      = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (classification, category, urgency, budget, property_type,
              neighborhood, summary, raw_message, new_score,
              sentiment, conversation_id, lead_id))
    else:
        cursor.execute("""
            INSERT INTO leads
                (client_id, phone, classification, category, urgency, budget,
                 property_type, neighborhood, summary, raw_message,
                 score, sentiment, conversation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (client_id, phone, classification, category, urgency, budget,
              property_type, neighborhood, summary, raw_message,
              score, sentiment, conversation_id))
        lead_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return lead_id



def get_leads(client_id=None, classification=None, limit=100):
    """Retorna leads com filtros opcionais."""
    conn   = get_connection()
    cursor = conn.cursor()
    query  = "SELECT * FROM leads WHERE 1=1"
    params = []
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    if classification:
        query += " AND classification = ?"
        params.append(classification)
    query += f" ORDER BY created_at DESC LIMIT {int(limit)}"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def log_conversation(lead_id, direction, message,
                     conversation_id=None, model_used=None, tokens_used=0):
    """Registra uma mensagem no histórico da conversa com logging estruturado."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations
            (lead_id, conversation_id, direction, message, model_used, tokens_used)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lead_id, conversation_id, direction, message, model_used, tokens_used))
    conn.commit()
    conn.close()


def check_lgpd_consent(phone: str, client_id: int) -> bool:
    """Verifica se o número já deu consentimento LGPD."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT consented FROM lgpd_consent WHERE phone = ? AND client_id = ?",
        (phone, client_id)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return False
    return bool(row["consented"])


def register_lgpd_consent(phone: str, client_id: int, consented: bool = True):
    """Registra ou atualiza o consentimento LGPD de um número."""
    from datetime import datetime, timezone
    conn   = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    if _IS_POSTGRES:
        cursor._raw.execute("""
            INSERT INTO lgpd_consent (phone, client_id, consented, consented_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (phone, client_id)
            DO UPDATE SET consented = EXCLUDED.consented, consented_at = EXCLUDED.consented_at
        """, (phone, client_id, consented, now if consented else None))
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO lgpd_consent (phone, client_id, consented, consented_at)
            VALUES (?, ?, ?, ?)
        """, (phone, client_id, 1 if consented else 0, now if consented else None))

    conn.commit()
    conn.close()


def check_rate_limit(phone: str, client_id: int, max_per_hour: int = 20) -> bool:
    """
    Verifica se o número excedeu o limite de mensagens por hora.
    Retorna True se BLOQUEADO (limite excedido), False se OK.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    if _IS_POSTGRES:
        cursor._raw.execute("""
            SELECT COUNT(*) as cnt FROM rate_limit_log
            WHERE phone = %s AND client_id = %s
            AND created_at > NOW() - INTERVAL '1 hour'
        """, (phone, client_id))
        row = cursor._raw.fetchone()
        count = row[0] if row else 0
    else:
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM rate_limit_log
            WHERE phone = ? AND client_id = ?
            AND created_at > datetime('now', '-1 hour')
        """, (phone, client_id))
        row = cursor.fetchone()
        count = row["cnt"] if row else 0

    conn.close()
    return count >= max_per_hour


def log_rate_limit(phone: str, client_id: int):
    """Registra uma mensagem recebida para controle de rate limit."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO rate_limit_log (phone, client_id) VALUES (?, ?)",
        (phone, client_id)
    )
    conn.commit()

    # Limpeza automática: remove registros com mais de 24h para não acumular lixo
    # Roda ~1% das vezes para não impactar performance
    import random
    if random.random() < 0.01:
        cleanup_rate_limit_log(conn)

    conn.close()


def cleanup_rate_limit_log(conn=None):
    """
    Remove registros mais antigos que 24h da tabela rate_limit_log.
    Mantém a tabela pequena sem precisar de Redis.
    Pode ser chamada manualmente ou automaticamente pelo log_rate_limit.
    """
    close_after = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()

    if _IS_POSTGRES:
        cursor._raw.execute(
            "DELETE FROM rate_limit_log WHERE created_at < NOW() - INTERVAL '24 hours'"
        )
    else:
        cursor.execute(
            "DELETE FROM rate_limit_log WHERE created_at < datetime('now', '-24 hours')"
        )

    conn.commit()
    if close_after:
        conn.close()


# ── Conversa com TTL ──────────────────────────────────────────────────────────

def get_active_conversation_id(phone: str, client_id: int, ttl_hours: int = 48) -> str | None:
    """
    Retorna o conversation_id ativo para um número, se existir e estiver dentro do TTL.

    Regra: Se o lead mandou mensagem há menos de `ttl_hours` (padrão 48h),
    considera a mesma conversa. Depois disso, nova conversa = novo UUID.

    Isso garante que um lead que 'some' por 10 dias seja tratado como novo contato ao retornar,
    sem contexto obsoleto da conversa anterior.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    if _IS_POSTGRES:
        cursor._raw.execute(f"""
            SELECT conversation_id, created_at FROM leads
            WHERE phone = %s AND client_id = %s
            AND created_at > NOW() - INTERVAL '{ttl_hours} hours'
            ORDER BY created_at DESC LIMIT 1
        """, (phone, client_id))
        row = cursor._raw.fetchone()
        result = row[0] if row else None
    else:
        cursor.execute(f"""
            SELECT conversation_id, created_at FROM leads
            WHERE phone = ? AND client_id = ?
            AND created_at > datetime('now', '-{ttl_hours} hours')
            ORDER BY created_at DESC LIMIT 1
        """, (phone, client_id))
        row = cursor.fetchone()
        result = row["conversation_id"] if row else None

    conn.close()
    return result


# ── Monitoramento de Custo de Tokens ─────────────────────────────────────────

# Custo aproximado por 1000 tokens (gpt-4o-mini: $0.00015 input + $0.00060 output)
# Usando média conservadora de $0.0005 por 1000 tokens
_COST_PER_1K_TOKENS_BRL = 0.0005 * 6.0  # ~$0.0005 USD × R$6 = R$0.003 por 1k tokens


def get_monthly_token_cost(client_id: int) -> dict:
    """
    Retorna o consumo de tokens e custo estimado do mês corrente para um cliente.
    Útil para auditoria e para o alerta de budget.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    if _IS_POSTGRES:
        cursor._raw.execute("""
            SELECT
                COALESCE(SUM(tokens_used), 0) as total_tokens,
                COUNT(*) as total_messages
            FROM conversations
            WHERE lead_id IN (
                SELECT id FROM leads WHERE client_id = %s
            )
            AND created_at >= DATE_TRUNC('month', NOW())
            AND model_used != 'mock'
            AND model_used IS NOT NULL
        """, (client_id,))
        row = cursor._raw.fetchone()
        total_tokens   = row[0] if row else 0
        total_messages = row[1] if row else 0
    else:
        cursor.execute("""
            SELECT
                COALESCE(SUM(tokens_used), 0) as total_tokens,
                COUNT(*) as total_messages
            FROM conversations
            WHERE lead_id IN (
                SELECT id FROM leads WHERE client_id = ?
            )
            AND created_at >= strftime('%Y-%m-01', 'now')
            AND model_used != 'mock'
            AND model_used IS NOT NULL
        """, (client_id,))
        row = cursor.fetchone()
        total_tokens   = row["total_tokens"] if row else 0
        total_messages = row["total_messages"] if row else 0

    conn.close()

    custo_brl = (total_tokens / 1000) * _COST_PER_1K_TOKENS_BRL

    return {
        "client_id":      client_id,
        "tokens_mes":     int(total_tokens),
        "mensagens_ia":   int(total_messages),
        "custo_estimado": round(custo_brl, 2),
        "moeda":          "BRL",
    }


def check_token_budget_alert(client_id: int, budget_brl: float = 100.0,
                             threshold_pct: float = 0.80) -> dict:
    """
    Verifica se o cliente está acima do threshold de custo de tokens (padrão: 80%).

    Retorna dict com:
      - alerted: True se deve enviar alerta
      - percent_used: porcentagem do budget consumida
      - custo_atual: custo no mês corrente em BRL
      - budget: limite configurado em BRL
    """
    stats     = get_monthly_token_cost(client_id)
    custo     = stats["custo_estimado"]
    pct_used  = custo / budget_brl if budget_brl > 0 else 0

    return {
        "alerted":      pct_used >= threshold_pct,
        "percent_used": round(pct_used * 100, 1),
        "custo_atual":  custo,
        "budget":       budget_brl,
        "tokens_mes":   stats["tokens_mes"],
    }


# ── Follow-up Log (Auditoria) ─────────────────────────────────────────────────

def log_followup(lead_id: int, client_id: int, followup_type: str,
                 status: str = "sent", provider: str = None,
                 error_msg: str = None, scheduled_time=None):
    """
    Registra uma tentativa de follow-up para auditoria completa.

    followup_type: 'hot_30min' | 'hot_4h_escalate' | 'warm_24h' | 'warm_72h'
                   'warm_7d' | 'cold_3d' | 'cold_10d'
    status:        'sent' | 'failed' | 'blocked' | 'simulated'
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO followup_log
            (lead_id, client_id, followup_type, status, provider, error_msg, scheduled_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lead_id, client_id, followup_type, status, provider, error_msg,
          scheduled_time.isoformat() if scheduled_time else None))
    conn.commit()
    conn.close()


def get_followup_log(lead_id: int = None, client_id: int = None,
                     limit: int = 50) -> list:
    """Retorna histórico de follow-ups para auditoria."""
    conn   = get_connection()
    cursor = conn.cursor()
    query  = "SELECT * FROM followup_log WHERE 1=1"
    params = []
    if lead_id:
        query += " AND lead_id = ?"
        params.append(lead_id)
    if client_id:
        query += " AND client_id = ?"
        params.append(client_id)
    query += f" ORDER BY executed_time DESC LIMIT {int(limit)}"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ── Scheduler Heartbeat ───────────────────────────────────────────────────────

def update_scheduler_heartbeat(jobs_count: int = 1):
    """
    Atualiza o heartbeat do scheduler. Chamado a cada execução do job.
    Se o scheduler travar, last_alive para de ser atualizado.
    """
    from datetime import datetime, timezone
    conn   = get_connection()
    cursor = conn.cursor()
    now    = datetime.now(timezone.utc).isoformat()

    if _IS_POSTGRES:
        cursor._raw.execute("""
            INSERT INTO scheduler_heartbeat (id, last_alive, jobs_count)
            VALUES (1, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET last_alive = EXCLUDED.last_alive,
                          jobs_count = EXCLUDED.jobs_count
        """, (now, jobs_count))
    else:
        cursor.execute("""
            UPDATE scheduler_heartbeat
            SET last_alive = ?, jobs_count = ?
            WHERE id = 1
        """, (now, jobs_count))

    conn.commit()
    conn.close()


def get_scheduler_heartbeat() -> dict:
    """
    Retorna status do heartbeat do scheduler.
    Retorna alerta se o scheduler não atualizou nos últimos 5 minutos.
    """
    from datetime import datetime, timezone
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_alive, jobs_count FROM scheduler_heartbeat WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"alive": False, "last_alive": None, "stale": True, "minutes_ago": None}

    last_alive_str = row["last_alive"]
    if not last_alive_str:
        return {"alive": False, "last_alive": None, "stale": True}

    try:
        if isinstance(last_alive_str, str):
            last_alive_str = last_alive_str.replace("Z", "+00:00")
            last_alive = datetime.fromisoformat(last_alive_str)
        else:
            last_alive = last_alive_str
        if not last_alive.tzinfo:
            last_alive = last_alive.replace(tzinfo=timezone.utc)

        now        = datetime.now(timezone.utc)
        minutes_ago = (now - last_alive).total_seconds() / 60
        is_stale   = minutes_ago > 5  # alerta se > 5 min sem heartbeat

        return {
            "alive":      not is_stale,
            "stale":      is_stale,
            "last_alive": last_alive.isoformat(),
            "minutes_ago": round(minutes_ago, 1),
            "jobs_count": row["jobs_count"],
        }
    except Exception as e:
        return {"alive": False, "stale": True, "error": str(e)}
