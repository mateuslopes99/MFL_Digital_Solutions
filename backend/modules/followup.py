"""
MFL Digital Solutions — Cadências de Follow-up Automático
==========================================================
Gerencia o follow-up automático de leads por temperatura usando APScheduler.

FLUXO POR TEMPERATURA:
  🔥 HOT   → +30min: 2ª notificação ao corretor se não respondido
             +4h:    escalar ao gestor/admin se ainda sem resposta
  🌡 WARM  → +24h:   mensagem de nutrição
             +72h:   reflorestamento moderado
             +7 dias: última tentativa antes de marcar como COLD
  ❄️ COLD  → +3 dias: reativação leve
             +10 dias: arquivar (marcar como lost se sem resposta)

EXECUÇÃO:
  APScheduler roda em background dentro da mesma instância Flask.
  Sem Redis, sem Celery — adequado para fase pré-escala.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Tipos de follow-up auditados (para followup_log)
_FOLLOWUP_HOT_30MIN    = "hot_30min"
_FOLLOWUP_HOT_ESCALATE = "hot_4h_escalate"
_FOLLOWUP_WARM_24H     = "warm_24h"
_FOLLOWUP_WARM_72H     = "warm_72h"
_FOLLOWUP_WARM_7D      = "warm_7d"
_FOLLOWUP_COLD_3D      = "cold_3d"
_FOLLOWUP_COLD_10D     = "cold_10d"

# ── Mensagens de follow-up por temperatura ────────────────────────────────────

_HOT_ESCALATION = (
    "⚡ *Atenção [CORRETOR]!*\n\n"
    "Este lead HOT ainda não foi contatado nos últimos 30 minutos.\n"
    "📱 Telefone: {phone}\n"
    "🎯 Score: {score}/100\n"
    "💬 Resumo: {summary}\n\n"
    "🚨 Leads HOT esfriáram em menos de 1 hora. Contato AGORA!"
)

_WARM_24H = (
    "Oi novamente! 👋 Vi que você estava interessado em encontrar um imóvel.\n\n"
    "Nosso time ainda está disponível para ajudar. "
    "Gostaria de mais informações ou agendar uma visita? 🏠"
)

_WARM_72H = (
    "Olá! 😊 Temos algumas novidades que podem interessar você.\n\n"
    "Imóveis novos chegaram na região que você pesquisou. "
    "Posso te mostrar as opções? Basta responder aqui!"
)

_WARM_7D = (
    "Oi! 📅 Faz uma semana desde seu contato conosco.\n\n"
    "Se você ainda está procurando o imóvel ideal, estamos aqui. "
    "Se já encontrou, fico feliz por você! 🎉\n\n"
    "Qualquer dúvida futura, é só chamar! 😊"
)

_COLD_3D = (
    "Olá! Vimos que você pesquisou sobre imóveis conosco. 🏡\n\n"
    "O mercado imobiliário está aquecido em Maceió — "
    "há ótimas oportunidades no momento. Quer saber mais?"
)

_COLD_10D = (
    "Última mensagem por aqui! 😊\n\n"
    "Se um dia precisar de ajuda para encontrar o imóvel dos seus sonhos, "
    "estaremos aqui. Até a próxima! 🙏"
)


# ── Lógica principal de follow-up ─────────────────────────────────────────────

def process_followups():
    """
    Função executada pelo scheduler a cada 15 minutos.
    Atualiza heartbeat a cada execução para monitoramento de saúde.
    """
    try:
        from database import get_connection, update_scheduler_heartbeat
        update_scheduler_heartbeat(jobs_count=1)  # 💓 heartbeat

        conn   = get_connection()
        cursor = conn.cursor()
        now    = datetime.now(timezone.utc)

        cursor.execute("""
            SELECT id, client_id, phone, classification, score,
                   summary, status, created_at, updated_at
            FROM leads
            WHERE status IN ('new', 'contacted')
            ORDER BY created_at ASC
        """)
        leads = cursor.fetchall()
        conn.close()

        if not leads:
            return

        processed = 0
        for lead in leads:
            try:
                _process_lead_followup(lead, now)
                processed += 1
            except Exception as e:
                logger.error(f"[FOLLOWUP] Erro no lead {lead['id']}: {e}")

        if processed > 0:
            logger.info(f"[FOLLOWUP] {processed} leads verificados.")

    except Exception as e:
        logger.error(f"[FOLLOWUP] Erro geral: {e}")


def _process_lead_followup(lead: dict, now: datetime):
    """Processa o follow-up de um lead específico baseado na idade e temperatura."""
    from database import get_connection, log_conversation, log_followup
    from modules.whatsapp_sender import send_message, WHATSAPP_PROVIDER

    created_at = _parse_dt(lead["created_at"])
    updated_at = _parse_dt(lead.get("updated_at") or lead["created_at"])
    tag        = lead.get("classification", "cold")
    lead_id    = lead["id"]
    phone      = lead["phone"]
    client_id  = lead["client_id"]
    score      = lead.get("score", 0)
    summary    = lead.get("summary", "")
    status     = lead.get("status", "new")

    minutes_since = (now - updated_at).total_seconds() / 60
    hours_since   = minutes_since / 60
    days_since    = hours_since / 24

    conn   = get_connection()
    cursor = conn.cursor()

    msg_to_send   = None
    new_status    = None
    notify_admin  = False
    notif_msg     = None
    followup_type = None

    # ── 🔥 HOT ────────────────────────────────────────────────────────────────
    if tag == "hot":
        if status == "new" and 30 <= minutes_since < 240:
            notify_admin  = True
            followup_type = _FOLLOWUP_HOT_30MIN
            notif_msg     = _HOT_ESCALATION.format(phone=phone, score=score, summary=summary)
            new_status    = "contacted"
            logger.info(f"[FOLLOWUP] HOT 30min: lead {lead_id}")

        elif hours_since >= 4 and status == "contacted":
            notify_admin  = True
            followup_type = _FOLLOWUP_HOT_ESCALATE
            notif_msg = (
                f"🚨 *LEAD HOT PERDENDO TEMPERATURA!*\n\n"
                f"Lead ID: {lead_id}\nTelefone: {phone}\n"
                f"Score: {score}/100\nHoras sem contato: {int(hours_since)}h\n\n"
                f"Ação imediata necessária."
            )
            logger.warning(f"[FOLLOWUP] HOT ignorado há {int(hours_since)}h")

    # ── 🌡 WARM ───────────────────────────────────────────────────────────────
    elif tag == "warm":
        if 22 <= hours_since <= 26 and status == "new":
            msg_to_send = _WARM_24H;  new_status = "contacted"; followup_type = _FOLLOWUP_WARM_24H
        elif 70 <= hours_since <= 74 and status == "contacted":
            msg_to_send = _WARM_72H;  followup_type = _FOLLOWUP_WARM_72H
        elif 6.5 <= days_since <= 7.5:
            msg_to_send = _WARM_7D;   new_status = "lost"; followup_type = _FOLLOWUP_WARM_7D

    # ── ❄️ COLD ───────────────────────────────────────────────────────────────
    elif tag == "cold":
        if 2.8 <= days_since <= 3.2 and status == "new":
            msg_to_send = _COLD_3D;   new_status = "contacted"; followup_type = _FOLLOWUP_COLD_3D
        elif 9.5 <= days_since <= 10.5:
            msg_to_send = _COLD_10D;  new_status = "lost"; followup_type = _FOLLOWUP_COLD_10D

    # ── Executar e logar ──────────────────────────────────────────────────────
    if msg_to_send and followup_type:
        result     = send_message(phone, msg_to_send)
        status_log = "simulated" if result.get("simulated") else (
                     "sent" if result["success"] else "failed")
        log_followup(
            lead_id=lead_id, client_id=client_id, followup_type=followup_type,
            status=status_log, provider=result.get("provider", WHATSAPP_PROVIDER),
            error_msg=result.get("error")
        )
        log_conversation(lead_id, "outbound", msg_to_send,
                         model_used=f"followup_{followup_type}")

    if notify_admin and notif_msg and followup_type:
        _notify_mfl_admin(notif_msg)
        log_followup(lead_id=lead_id, client_id=client_id,
                     followup_type=followup_type, status="sent", provider="admin_alert")

    if new_status:
        cursor.execute(
            "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now.isoformat(), lead_id)
        )
        conn.commit()

    conn.close()



def _send_whatsapp_to_lead(phone: str, client_id: int, message: str, lead_id: int):
    """Delega ao whatsapp_sender (multi-provider)."""
    from modules.whatsapp_sender import send_message
    result = send_message(phone, message)
    if not result["success"] and not result.get("simulated"):
        logger.error(f"[FOLLOWUP] Falha ao enviar para {phone}: {result.get('error')}")


def _notify_mfl_admin(message: str):
    """Notifica o admin da MFL via whatsapp_sender (multi-provider)."""
    try:
        from modules.whatsapp_sender import send_message
        admin_wa = os.getenv("MFL_ADMIN_WHATSAPP", "")
        if not admin_wa:
            logger.info(f"[FOLLOWUP-SIM] Admin notificado: {message[:60]}...")
            return
        send_message(admin_wa, message)
    except Exception as e:
        logger.error(f"[FOLLOWUP] Erro ao notificar admin: {e}")


def _get_client_whatsapp(client_id: int) -> str | None:
    """Retorna o número WhatsApp do cliente."""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT whatsapp_number FROM clients WHERE id = ? LIMIT 1",
            (client_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row["whatsapp_number"] if row else None
    except Exception:
        return None


def _parse_dt(value) -> datetime:
    """Converte string ISO ou datetime para datetime com timezone UTC."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        value = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            # Fallback para formatos sem timezone
            dt = datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


# ── Scheduler ─────────────────────────────────────────────────────────────────

_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    """
    Inicia o scheduler de follow-ups em background.
    Deve ser chamado uma única vez no startup do Flask.
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        logger.warning("[FOLLOWUP] Scheduler já está rodando.")
        return

    _scheduler = BackgroundScheduler(
        timezone="America/Maceio",
        job_defaults={"misfire_grace_time": 60}
    )

    # Roda a cada 15 minutos para verificar follow-ups pendentes
    _scheduler.add_job(
        func=process_followups,
        trigger=IntervalTrigger(minutes=15),
        id="followup_check",
        name="Verificação de Follow-ups",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("[FOLLOWUP] Scheduler iniciado (intervalo: 15 min).")
    print("[FOLLOWUP] ✅ Scheduler de follow-ups ativo.")


def stop_scheduler():
    """Para o scheduler graciosamente."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[FOLLOWUP] Scheduler encerrado.")


def get_scheduler_status() -> dict:
    """Retorna o status completo do scheduler + heartbeat do banco."""
    from database import get_scheduler_heartbeat

    in_memory = {"running": False, "jobs": [], "count": 0}
    if _scheduler:
        jobs = []
        for job in _scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id":       job.id,
                "name":     job.name,
                "next_run": next_run.isoformat() if next_run else None,
            })
        in_memory = {
            "running": _scheduler.running,
            "jobs":    jobs,
            "count":   len(jobs),
        }

    heartbeat = get_scheduler_heartbeat()

    return {
        **in_memory,
        "heartbeat": heartbeat,
        "healthy":   in_memory["running"] and heartbeat.get("alive", False),
    }
