"""
MFL Digital Solutions — Integração WhatsApp (Multi-Provider)
=============================================================
Abstrai o envio de mensagens WhatsApp para múltiplos provedores:

  WHATSAPP_PROVIDER=evolution  → Evolution API + Baileys (open-source, grátis)
  WHATSAPP_PROVIDER=twilio     → Twilio (oficial Meta, pago por mensagem)
  WHATSAPP_PROVIDER=mock       → Simulação local (nenhuma mensagem enviada)

EVOLUTION API — SETUP RÁPIDO:
  1. Railway: deploy do repositório atende.io/evolution-api
  2. Criar instância: POST /instance/create
  3. Conectar QR Code: GET /instance/connect/{instance}
  4. Configurar webhook: POST /webhook/set/{instance}
  5. Preencher EVOLUTION_API_URL e EVOLUTION_API_KEY no .env

VANTAGENS DA EVOLUTION API (vs Twilio):
  - Zero custo por mensagem
  - Conecta qualquer número via QR Code (em minutos)
  - Sem aprovação da Meta
  - Suporta áudios, imagens, documentos
  - Ideal para piloto e clientes iniciais
"""

import os
import logging
import requests as http_requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Configuração de provider ──────────────────────────────────────────────────
WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "mock").lower()
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")


# ── Interface pública ─────────────────────────────────────────────────────────

def send_message(to: str, message: str, instance: str = None) -> dict:
    """
    Envia mensagem WhatsApp via o provider configurado.

    Args:
        to: número no formato internacional sem símbolo (ex: '5582999998888')
            ou com whatsapp: prefix (whatsapp:+5582999998888)
        message: texto da mensagem
        instance: nome da instância Evolution API (opcional, usa EVOLUTION_INSTANCE padrão)

    Returns:
        dict com 'success', 'provider', e 'details' (ou 'error')
    """
    to_clean = _normalize_phone(to)

    provider = WHATSAPP_PROVIDER
    if not EVOLUTION_API_URL and provider == "evolution":
        logger.warning("[WA] EVOLUTION_API_URL não configurada. Usando modo mock.")
        provider = "mock"

    if provider == "evolution":
        return _send_evolution(to_clean, message, instance)
    elif provider == "twilio":
        return _send_twilio(to_clean, message)
    else:
        return _send_mock(to_clean, message)


def get_provider_status() -> dict:
    """Retorna o status do provider configurado."""
    provider = WHATSAPP_PROVIDER

    if provider == "evolution":
        return _check_evolution_status()

    elif provider == "twilio":
        sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        return {
            "provider": "twilio",
            "configured": bool(sid and not sid.startswith("AC...")),
            "ready": bool(sid and not sid.startswith("AC...")),
        }
    else:
        return {"provider": "mock", "configured": True, "ready": True}


def get_qr_code(instance: str = None) -> dict:
    """
    Retorna QR Code para conectar número WhatsApp (apenas Evolution API).
    """
    if WHATSAPP_PROVIDER != "evolution":
        return {"error": f"QR Code disponível apenas para Evolution API. Provider atual: {WHATSAPP_PROVIDER}"}

    _instance = instance or os.getenv("EVOLUTION_INSTANCE", "mfl-default")
    url = f"{EVOLUTION_API_URL}/instance/connect/{_instance}"
    try:
        r = http_requests.get(url, headers=_evolution_headers(), timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def create_instance(instance_name: str) -> dict:
    """
    Cria uma nova instância na Evolution API.
    Cada cliente pode ter sua própria instância (número WhatsApp).
    """
    if WHATSAPP_PROVIDER != "evolution":
        return {"error": "Apenas para Evolution API"}

    url = f"{EVOLUTION_API_URL}/instance/create"
    payload = {
        "instanceName": instance_name,
        "qrcode":       True,
        "integration":  "WHATSAPP-BAILEYS",
    }
    try:
        r = http_requests.post(url, json=payload, headers=_evolution_headers(), timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def list_instances() -> dict:
    """Lista todas as instâncias Evolution API ativas."""
    if WHATSAPP_PROVIDER != "evolution":
        return {"instances": [], "provider": WHATSAPP_PROVIDER}

    url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
    try:
        r = http_requests.get(url, headers=_evolution_headers(), timeout=10)
        return {"instances": r.json(), "provider": "evolution"}
    except Exception as e:
        return {"instances": [], "error": str(e)}


# ── Providers internos ────────────────────────────────────────────────────────

def _send_evolution(to: str, message: str, instance: str = None) -> dict:
    """Envia via Evolution API (Baileys)."""
    _instance = instance or os.getenv("EVOLUTION_INSTANCE", "mfl-default")
    url       = f"{EVOLUTION_API_URL}/message/sendText/{_instance}"

    payload = {
        "number":  to,
        "text":    message,
        "options": {
            "delay":      1200,       # delay de digitação (ms) — parece mais humano
            "presence":   "composing" # exibe "digitando..."
        }
    }

    try:
        r = http_requests.post(
            url, json=payload,
            headers=_evolution_headers(),
            timeout=15
        )

        if r.status_code == 200:
            logger.info(f"[WA-EVOLUTION] Enviado para {to}")
            return {"success": True, "provider": "evolution", "details": r.json()}
        else:
            logger.error(f"[WA-EVOLUTION] Erro {r.status_code}: {r.text[:100]}")
            return {"success": False, "provider": "evolution", "error": r.text[:200]}

    except http_requests.Timeout:
        logger.error(f"[WA-EVOLUTION] Timeout ao enviar para {to}")
        return {"success": False, "provider": "evolution", "error": "Timeout"}
    except Exception as e:
        logger.error(f"[WA-EVOLUTION] Erro: {e}")
        return {"success": False, "provider": "evolution", "error": str(e)}


def _send_twilio(to: str, message: str) -> dict:
    """Envia via Twilio (mantido para compatibilidade e clientes enterprise)."""
    try:
        from twilio.rest import Client
        sid   = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        from_ = os.getenv("TWILIO_WHATSAPP_NUMBER") or os.getenv("TWILIO_FROM_NUMBER")

        if not all([sid, token, from_]):
            return {"success": False, "provider": "twilio", "error": "Credenciais não configuradas"}

        # Normaliza formato Twilio
        to_twilio = f"whatsapp:+{to}" if not to.startswith("whatsapp:") else to

        client  = Client(sid, token)
        message = client.messages.create(body=message, from_=from_, to=to_twilio)

        logger.info(f"[WA-TWILIO] Enviado. SID: {message.sid}")
        return {"success": True, "provider": "twilio", "details": {"sid": message.sid}}

    except Exception as e:
        logger.error(f"[WA-TWILIO] Erro: {e}")
        return {"success": False, "provider": "twilio", "error": str(e)}


def _send_mock(to: str, message: str) -> dict:
    """Simula envio para desenvolvimento/teste."""
    short_msg = message[:60].replace("\n", " ")
    logger.info(f"[WA-MOCK] → {to}: {short_msg}...")
    print(f"[WA-MOCK] Mensagem para {to}:\n{message[:120]}...\n")
    return {"success": True, "provider": "mock", "simulated": True}


def _check_evolution_status() -> dict:
    """Verifica se a Evolution API está respondendo."""
    if not EVOLUTION_API_URL:
        return {"provider": "evolution", "configured": False, "ready": False,
                "error": "EVOLUTION_API_URL não configurada"}

    _instance = os.getenv("EVOLUTION_INSTANCE", "mfl-default")
    url = f"{EVOLUTION_API_URL}/instance/connectionState/{_instance}"
    try:
        r = http_requests.get(url, headers=_evolution_headers(), timeout=5)
        data  = r.json()
        state = data.get("instance", {}).get("state", "unknown")
        return {
            "provider":   "evolution",
            "configured": True,
            "ready":      state == "open",
            "state":      state,
            "instance":   _instance,
        }
    except Exception as e:
        return {"provider": "evolution", "configured": True, "ready": False, "error": str(e)}


def _evolution_headers() -> dict:
    return {
        "apikey":       EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }


def _normalize_phone(phone: str) -> str:
    """
    Normaliza número de telefone para formato limpo (só dígitos, sem +, sem whatsapp:).
    Ex: 'whatsapp:+5582999998888' → '5582999998888'
    """
    p = phone.strip()
    p = p.replace("whatsapp:", "").replace("+", "").strip()
    # Remove caracteres não numéricos
    p = "".join(c for c in p if c.isdigit())
    return p
