"""
MFL Digital Solutions — Rotas do WhatsApp (Webhook) v3
=======================================================
Recebe mensagens de DOIS providers e processa com IA.

PROVIDERS SUPORTADOS:
  WHATSAPP_PROVIDER=evolution → POST /webhook/whatsapp/evolution
  WHATSAPP_PROVIDER=twilio    → POST /webhook/whatsapp (legado)

FLUXO COMPLETO (ambos os providers):
  Lead clica no anúncio → WhatsApp abre → mensagem chega
  → Webhook recebe (Twilio ou Evolution API)
  → Parser normaliza o payload para formato interno
  → [Rate Limit] → [LGPD] → [IA: score + sentimento]
  → Salva DB → Notifica corretor com ficha HOT
"""

import os
import hmac
import hashlib
import uuid
from functools import wraps
from flask import Blueprint, request, jsonify, abort
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.ai_classifier import classify_lead
from database import (
    insert_lead, log_conversation, get_connection,
    check_lgpd_consent, register_lgpd_consent,
    check_rate_limit, log_rate_limit,
    get_active_conversation_id
)

# ── Blueprint ─────────────────────────────────────────────────────────────────
whatsapp_bp = Blueprint("whatsapp", __name__)

# ── Constantes LGPD ───────────────────────────────────────────────────────────
LGPD_MESSAGE = (
    "👋 Olá! Antes de continuar, precisamos da sua autorização.\n\n"
    "🔐 *Política de Privacidade:* Suas informações serão usadas exclusivamente "
    "para ajudá-lo a encontrar o imóvel ideal e nunca serão compartilhadas com terceiros.\n\n"
    "✅ Ao responder *SIM*, você concorda com nossa política de privacidade (LGPD).\n"
    "Você pode revogar seu consentimento a qualquer momento enviando *CANCELAR*."
)

LGPD_CONSENT_WORDS = {"sim", "aceito", "ok", "pode", "concordo", "autorizo"}
LGPD_REVOKE_WORDS  = {"cancelar", "nao", "não", "sair", "stop", "remover"}


# ── Utilitários ───────────────────────────────────────────────────────────────

def _validate_twilio_signature(f):
    """
    Decorator que valida a assinatura HMAC-SHA1 do Twilio.
    Bloqueia qualquer requisição que não venha do Twilio real.
    Em modo dev (USE_MOCK=true) ou sem TWILIO_AUTH_TOKEN, pula a validação.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        use_mock   = os.getenv("USE_MOCK", "true").lower() == "true"

        if use_mock or not auth_token or len(auth_token) < 10:
            return f(*args, **kwargs)

        twilio_sig  = request.headers.get("X-Twilio-Signature", "")
        url         = request.url
        post_params = sorted(request.form.items())
        params_str  = "".join(f"{k}{v}" for k, v in post_params)
        message     = (url + params_str).encode("utf-8")
        expected_sig = hmac.new(
            auth_token.encode("utf-8"), message, hashlib.sha1
        ).digest()

        import base64
        expected_b64 = base64.b64encode(expected_sig).decode("utf-8")

        if not hmac.compare_digest(twilio_sig, expected_b64):
            print("[SECURITY] Webhook rejeitado: assinatura Twilio inválida!")
            abort(403)

        return f(*args, **kwargs)
    return decorated


def _twiml_response(text: str):
    """Monta resposta TwiML compatível com ou sem biblioteca Twilio."""
    try:
        from twilio.twiml.messaging_response import MessagingResponse
        twiml = MessagingResponse()
        twiml.message(text)
        return str(twiml), 200, {"Content-Type": "text/xml"}
    except ImportError:
        return (
            f'<?xml version="1.0"?><Response><Message>{text}</Message></Response>',
            200, {"Content-Type": "text/xml"}
        )


def _build_hot_ficha(phone: str, classification: dict, score: int) -> str:
    """Monta a ficha estruturada de lead HOT para envio ao corretor."""
    tag = "🔥 HOT" if classification.get("classification") == "hot" else "🌡 WARM"
    return (
        f"{tag} — *LEAD QUALIFICADO*\n\n"
        f"📞 Contato: {phone}\n"
        f"🏠 Interesse: {classification.get('property_type', 'N/I')} "
        f"em {classification.get('neighborhood', 'N/I')}\n"
        f"💰 Budget: {classification.get('budget', 'não informado')}\n"
        f"⏰ Urgência: {classification.get('urgency', 'média').upper()}\n"
        f"🎯 Score: {score}/100\n"
        f"😊 Sentimento: {classification.get('sentiment', 'neutro').capitalize()}\n"
        f"📋 Categoria: {classification.get('category', 'N/I')}\n\n"
        f"💬 *Resumo:* {classification.get('summary', '')}\n\n"
        f"👉 Entre em contato em até 1 hora!"
    )


def get_or_create_lead(client_id: int, phone: str) -> dict | None:
    """Busca um lead existente pelo telefone ou retorna None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM leads WHERE client_id = ? AND phone = ? ORDER BY created_at DESC LIMIT 1",
        (client_id, phone)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_client_by_whatsapp_number(to_number: str) -> int | None:
    """Identifica qual cliente MFL é dono do número de WhatsApp."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM clients WHERE whatsapp_number = ? AND status = 'active' LIMIT 1",
            (to_number,)
        )
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None
    except Exception:
        return None


def notify_agent(agent_whatsapp: str, lead_info: dict, classification: dict, ficha: str = None):
    """
    Envia notificação ao corretor via whatsapp_sender (multi-provider).
    Funciona com Evolution API ou Twilio — configuração via WHATSAPP_PROVIDER.
    """
    from modules.whatsapp_sender import send_message

    msg = ficha if ficha else (
        f"{'🔥' if lead_info['classification'] == 'hot' else '🟡'} "
        f"*NOVO LEAD — {lead_info['classification'].upper()}*\n\n"
        f"📱 Telefone: {lead_info['phone']}\n"
        f"📋 Categoria: {classification.get('category', 'N/A')}\n"
        f"⏰ Urgência: {classification.get('urgency', 'N/A')}\n"
        f"💰 Orçamento: {classification.get('budget', 'N/A')}\n"
        f"🏠 Imóvel: {classification.get('property_type', 'N/A')}\n"
        f"📍 Bairro: {classification.get('neighborhood', 'N/A')}\n\n"
        f"💬 Resumo: {classification.get('summary', 'N/A')}\n\n"
        f"👉 Responda rapidamente!"
    )

    result = send_message(agent_whatsapp, msg)
    if result["success"] or result.get("simulated"):
        print(f"[NOTIFY] Corretor notificado: {agent_whatsapp}")
    else:
        print(f"[NOTIFY] Erro ao notificar corretor: {result.get('error')}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@whatsapp_bp.route("/whatsapp", methods=["POST"])
@_validate_twilio_signature
def receive_whatsapp():
    """
    Webhook do Twilio (legado / enterprise).
    URL: https://SEU_DOMINIO/webhook/whatsapp
    Delega toda a lógica para _process_inbound_message.
    """
    incoming_msg = request.form.get("Body", "").strip()
    sender_phone = request.form.get("From", "").replace("whatsapp:", "").replace("+", "")
    to_number    = request.form.get("To", "")
    client_id    = get_client_by_whatsapp_number(to_number) or 1

    print(f"[TWILIO] De: {sender_phone} | Msg: {incoming_msg[:60]}")

    response_text = _process_inbound_message(
        sender_phone=sender_phone,
        incoming_msg=incoming_msg,
        client_id=client_id
    )

    return _twiml_response(response_text or "Olá! 👋 Recebemos sua mensagem!")


@whatsapp_bp.route("/whatsapp/test", methods=["POST"])
def test_webhook():
    """
    Endpoint de teste — simula recebimento de mensagem sem Twilio.
    Body JSON: { "message": "...", "save": true/false, "client_id": 1 }
    Protegido por WEBHOOK_SECRET para evitar injeção de dados em produção.
    """
    # Verificação de segurança: requer token secreto no header ou no body
    secret = os.getenv("WEBHOOK_SECRET", "")
    if secret:
        provided = request.headers.get("X-Webhook-Secret", "") or (request.get_json() or {}).get("secret", "")
        if not hmac.compare_digest(provided, secret):
            print("[SECURITY] /whatsapp/test bloqueado: token inválido")
            return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Campo 'message' obrigatório"}), 400

    message        = data["message"]
    classification = classify_lead(message)

    lead_id = None
    if data.get("save", False):
        lead_id = insert_lead(
            client_id=data.get("client_id", 1),
            phone="whatsapp:+55TEST",
            classification=classification.get("classification", "warm"),
            category=classification.get("category", "outro"),
            urgency=classification.get("urgency", "media"),
            budget=classification.get("budget", "não informado"),
            property_type=classification.get("property_type", "não informado"),
            neighborhood=classification.get("neighborhood", "não informado"),
            summary=classification.get("summary", ""),
            raw_message=message,
            score=classification.get("score", 0),
            sentiment=classification.get("sentiment", "neutro"),
        )

    return jsonify({
        "status":         "success",
        "input":          message,
        "lead_id":        lead_id,
        "saved":          data.get("save", False),
        "classification": classification
    })


@whatsapp_bp.route("/whatsapp/status", methods=["GET"])
def whatsapp_status():
    """Verifica status da integração WhatsApp (provider ativo + Twilio legado)."""
    from modules.whatsapp_sender import get_provider_status, WHATSAPP_PROVIDER
    provider_status = get_provider_status()

    # Status Twilio (legado)
    sid    = os.getenv("TWILIO_ACCOUNT_SID", "")
    token  = os.getenv("TWILIO_AUTH_TOKEN", "")
    number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    twilio_ok = bool(sid and not sid.startswith("AC...") and
                     token and len(token) > 10 and number)

    use_mock = os.getenv("USE_MOCK", "true").lower() == "true"

    return jsonify({
        "active_provider":   WHATSAPP_PROVIDER,
        "provider_status":   provider_status,
        "twilio_configured": twilio_ok,
        "use_mock_ai":       use_mock,
        "ai_mode":           "MOCK (regras locais)" if use_mock else "REAL (GPT-4o-mini)",
        "endpoints": {
            "evolution": "/webhook/whatsapp/evolution",
            "twilio":    "/webhook/whatsapp",
            "test":      "/webhook/whatsapp/test",
        },
        "lgpd":       "Ativo — consentimento solicitado na 1ª mensagem",
        "rate_limit": "20 mensagens/hora por número",
    })


# ── EVOLUTION API WEBHOOK ──────────────────────────────────────────────────────

@whatsapp_bp.route("/whatsapp/evolution", methods=["POST"])
def receive_whatsapp_evolution():
    """
    Webhook da Evolution API (Baileys).
    URL configurada na Evolution API:
      POST /webhook/set/{instance}
      { "url": "https://SEU-BACKEND/webhook/whatsapp/evolution" }

    Payload JSON da Evolution API:
    {
      "event": "MESSAGES_UPSERT",
      "instance": "mfl-default",
      "data": {
        "key": { "remoteJid": "5582999998888@s.whatsapp.net", "fromMe": false },
        "message": { "conversation": "Quero comprar um apartamento" },
        "messageTimestamp": 1234567890
      }
    }
    """
    payload = request.get_json(silent=True) or {}

    # ── Validação da chave de API da Evolution API ─────────────────────────────
    evolution_key = os.getenv("EVOLUTION_API_KEY", "")
    if evolution_key:
        req_key = request.headers.get("apikey", "") or request.headers.get("Authorization", "")
        if req_key and req_key != evolution_key:
            print("[SECURITY] Evolution webhook rejeitado: API key inválida")
            return jsonify({"error": "Unauthorized"}), 403

    # ── Parse do payload Evolution API ────────────────────────────────────────
    event = payload.get("event", "")
    if event not in ("MESSAGES_UPSERT", "messages.upsert"):
        return jsonify({"ignored": True, "event": event}), 200

    data = payload.get("data", {})
    key  = data.get("key", {})

    # Ignora mensagens enviadas pelo próprio bot
    if key.get("fromMe", False):
        return jsonify({"ignored": True, "reason": "fromMe"}), 200

    # Extrai número do remetente (formato: 5582999998888@s.whatsapp.net)
    remote_jid = key.get("remoteJid", "")
    sender_phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
    if not sender_phone:
        return jsonify({"error": "remoteJid ausente"}), 400

    # Extrai a mensagem (texto, legenda de imagem ou localização)
    msg_obj      = data.get("message", {})
    incoming_msg = (
        msg_obj.get("conversation") or
        msg_obj.get("extendedTextMessage", {}).get("text") or
        msg_obj.get("imageMessage", {}).get("caption") or
        msg_obj.get("videoMessage", {}).get("caption") or
        "[Mídia recebida]"
    ).strip()

    # Identifica qual cliente MFL é dono desta instância
    instance      = payload.get("instance", os.getenv("EVOLUTION_INSTANCE", "mfl-default"))
    client_id     = _get_client_by_instance(instance) or 1

    print(f"[EVOLUTION] De: {sender_phone} | Inst: {instance} | Msg: {incoming_msg[:60]}")

    # ── Processa com a lógica compartilhada ────────────────────────────────────
    response_text = _process_inbound_message(
        sender_phone=sender_phone,
        incoming_msg=incoming_msg,
        client_id=client_id
    )

    # Envia resposta ao lead via Evolution API
    if response_text:
        from modules.whatsapp_sender import send_message
        send_message(sender_phone, response_text, instance=instance)

    return jsonify({"status": "processed", "provider": "evolution"}), 200


def _get_client_by_instance(instance_name: str) -> int | None:
    """Identifica qual cliente MFL corresponde a uma instância Evolution API."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # A instância pode ser o próprio nome ou estar em whatsapp_number
        cursor.execute(
            """SELECT id FROM clients
               WHERE (whatsapp_number = ? OR whatsapp_number LIKE ?)
               AND status = 'active' LIMIT 1""",
            (instance_name, f"%{instance_name}%")
        )
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None
    except Exception:
        return None


def _process_inbound_message(sender_phone: str, incoming_msg: str, client_id: int) -> str | None:
    """
    Lógica central de processamento (shared by Twilio and Evolution API).
    Returns the response text to send back to the lead, or None.
    """
    # ── 1. Rate Limiting ──────────────────────────────────────────────────────
    if check_rate_limit(sender_phone, client_id, max_per_hour=20):
        print(f"[RATE-LIMIT] Bloqueado: {sender_phone}")
        return "⏸️ Você enviou muitas mensagens. Aguarde 1 hora e tente novamente."
    log_rate_limit(sender_phone, client_id)

    # ── 2. Consentimento LGPD ─────────────────────────────────────────────────
    has_consent = check_lgpd_consent(sender_phone, client_id)
    msg_lower   = incoming_msg.lower().strip()

    if not has_consent:
        if any(w in msg_lower for w in LGPD_REVOKE_WORDS):
            return "✅ Sem problemas! Não entraremos em contato. Até mais!"
        if any(w in msg_lower for w in LGPD_CONSENT_WORDS):
            register_lgpd_consent(sender_phone, client_id, consented=True)
            return (
                "✅ Obrigado por autorizar! Agora posso te ajudar. 😊\n\n"
                "Me conte: o que você está procurando? (tipo de imóvel, bairro, orçamento)"
            )
        return LGPD_MESSAGE

    if any(w in msg_lower for w in LGPD_REVOKE_WORDS):
        register_lgpd_consent(sender_phone, client_id, consented=False)
        return "✅ Consentimento revogado. Seus dados serão removidos em até 15 dias."

    # ── 3. Classificação IA ───────────────────────────────────────────────────
    classification = classify_lead(incoming_msg)
    tag   = classification.get("classification", "warm")
    score = classification.get("score", 0)
    print(f"[AI] {tag.upper()} | Score: {score} | {classification.get('summary', '')[:50]}")

    # ── 4. Salvar lead ────────────────────────────────────────────────────────
    conv_id = (
        get_active_conversation_id(sender_phone, client_id, ttl_hours=48)
        or str(uuid.uuid4())[:12]
    )
    lead_id = insert_lead(
        client_id=client_id,
        phone=sender_phone,
        classification=tag,
        category=classification.get("category", "outro"),
        urgency=classification.get("urgency", "media"),
        budget=classification.get("budget", "não informado"),
        property_type=classification.get("property_type", "não informado"),
        neighborhood=classification.get("neighborhood", "não informado"),
        summary=classification.get("summary", ""),
        raw_message=incoming_msg,
        score=score,
        sentiment=classification.get("sentiment", "neutro"),
        conversation_id=conv_id,
    )
    log_conversation(
        lead_id, "inbound", incoming_msg,
        conversation_id=conv_id,
        model_used="mock" if classification.get("_mock") else "gpt-4o-mini",
        tokens_used=classification.get("_tokens", 0)
    )

    # ── 5. Resposta ao cliente ────────────────────────────────────────────────
    response_text = classification.get(
        "suggested_response",
        "Olá! 👋 Recebemos sua mensagem. Nossa equipe entrará em contato em breve!"
    )

    # ── 6. Notificar corretor ────────────────────────────────────────────────
    if tag == "hot":
        ficha    = _build_hot_ficha(sender_phone, classification, score)
        agent_wa = os.getenv("CORRETOR_A_WHATSAPP", "")
        if agent_wa:
            notify_agent(agent_wa, {"phone": sender_phone, "classification": "hot"}, classification, ficha)

    elif tag == "warm":
        agent_wa = os.getenv("CORRETOR_B_WHATSAPP", "")
        if agent_wa:
            notify_agent(agent_wa, {"phone": sender_phone, "classification": "warm"}, classification)

    log_conversation(lead_id, "outbound", response_text, conversation_id=conv_id)
    return response_text

