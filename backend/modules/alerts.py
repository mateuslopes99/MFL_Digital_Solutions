"""
MFL Digital Solutions — Alertas Automáticos
=============================================
Envia alertas via WhatsApp (Twilio) para o admin e e-mail para clientes
quando o health score cai abaixo de 50 (crítico).

Configuração no .env:
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
  TWILIO_FROM_NUMBER  — número Twilio da MFL (ex: whatsapp:+14155...)
  MFL_ADMIN_WHATSAPP  — seu WhatsApp pessoal (ex: whatsapp:+5582...)
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
  MFL_EMAIL_FROM      — remetente dos e-mails
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# WhatsApp (Twilio)
# ─────────────────────────────────────────────────────────────────────────────

def send_whatsapp_alert(client: dict, hs: dict) -> bool:
    """
    Envia alerta de churn risk para o WhatsApp do admin (MFL).
    Retorna True se enviado com sucesso.
    """
    try:
        from twilio.rest import Client as TwilioClient

        sid   = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        from_ = os.getenv("TWILIO_FROM_NUMBER")
        to_   = os.getenv("MFL_ADMIN_WHATSAPP")

        if not all([sid, token, from_, to_]):
            logger.warning("[ALERT-WA] Variáveis Twilio não configuradas. Simulando envio.")
            _log_simulated_whatsapp(client, hs)
            return False

        raw  = hs.get("raw", {})
        det  = hs.get("detail", {})
        score = hs.get("health_score", 0)
        label = hs.get("label", "Crítico")
        emoji = "🔴" if score < 50 else "🟡"

        body = (
            f"{emoji} *MFL Alert — Cliente em Risco*\n\n"
            f"*Cliente:* {client.get('name', '—')}\n"
            f"*Plano:* {client.get('package', '—').capitalize()}\n"
            f"*Health Score:* {score}/100 — *{label}*\n\n"
            f"📊 *Detalhamento:*\n"
            f"  • Leads (30d): {raw.get('leads_30d', 0)}\n"
            f"  • Qualificação: {raw.get('qualification_pct', 0)}%\n"
            f"  • Conversão: {raw.get('conversion_pct', 0)}%\n"
            f"  • Sem lead há: {_days_since(hs)} dias\n\n"
            f"⚡ *Pontuação por componente:*\n"
            f"  Velocity: {det.get('velocity', 0)}/30 · "
            f"Qual: {det.get('qual_rate', 0)}/30 · "
            f"Conv: {det.get('conversion', 0)}/20 · "
            f"Recency: {det.get('recency', 0)}/10 · "
            f"Trend: {det.get('trend', 0)}/10\n\n"
            f"🎯 *Recomendação:* LIGAR nas próximas 24h."
        )

        twilio = TwilioClient(sid, token)
        msg = twilio.messages.create(body=body, from_=from_, to=to_)
        logger.info(f"[ALERT-WA] Enviado para admin. SID: {msg.sid}")
        return True

    except ImportError:
        logger.warning("[ALERT-WA] Twilio não instalado. pip install twilio")
        _log_simulated_whatsapp(client, hs)
        return False
    except Exception as e:
        logger.error(f"[ALERT-WA] Erro ao enviar: {e}")
        return False


def _log_simulated_whatsapp(client: dict, hs: dict):
    score = hs.get("health_score", 0)
    print(
        f"\n[SIMULATED WA ALERT] → Admin\n"
        f"  Cliente: {client.get('name')} | Score: {score}/100 | "
        f"Label: {hs.get('label')}\n"
    )


def _days_since(hs: dict) -> str:
    """Retorna string dos dias desde o último lead."""
    raw = hs.get("raw", {})
    leads_week = raw.get("leads_this_week", 0)
    if leads_week > 0:
        return "< 7"
    leads_30d = raw.get("leads_30d", 0)
    if leads_30d > 0:
        return "7-30"
    return "> 30"


# ─────────────────────────────────────────────────────────────────────────────
# E-mail (SMTP)
# ─────────────────────────────────────────────────────────────────────────────

def send_email_report(client: dict, hs: dict) -> bool:
    """
    Envia relatório semanal por e-mail ao cliente.
    Retorna True se enviado com sucesso.
    """
    client_email = client.get("email")
    if not client_email:
        logger.warning(f"[ALERT-EMAIL] Cliente {client.get('name')} sem e-mail.")
        _log_simulated_email(client, hs)
        return False

    try:
        smtp_host = os.getenv("SMTP_HOST",     "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        from_addr = os.getenv("MFL_EMAIL_FROM", smtp_user)

        if not all([smtp_user, smtp_pass]):
            logger.warning("[ALERT-EMAIL] SMTP não configurado. Simulando envio.")
            _log_simulated_email(client, hs)
            return False

        subject, body_html = _build_email(client, hs)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"MFL Digital Solutions <{from_addr}>"
        msg["To"]      = client_email
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, client_email, msg.as_string())

        logger.info(f"[ALERT-EMAIL] Enviado para {client_email}")
        return True

    except Exception as e:
        logger.error(f"[ALERT-EMAIL] Erro: {e}")
        return False


def _build_email(client: dict, hs: dict) -> tuple[str, str]:
    """Retorna (assunto, html) do e-mail para o cliente."""
    raw   = hs.get("raw", {})
    score = hs.get("health_score", 0)
    label = hs.get("label", "Atenção")
    name  = client.get("name", "Cliente")
    week  = datetime.now().strftime("Semana %d/%m")

    color_score = "#00C853" if score >= 80 else "#FFD600" if score >= 60 else "#FF5252"

    # Dica personalizada baseada no score
    if score >= 80:
        tip = (
            "🎉 Excelente semana! Seu sistema está funcionando muito bem. "
            "Que tal revisar os leads HOT e garantir que os corretores estão fazendo follow-up?"
        )
        tip_title = "Tudo funcionando ótimo!"
    elif score >= 60:
        tip = (
            "⚠️ Percebemos uma queda na qualificação esta semana. "
            "Verifique se seus anúncios estão atraindo o público certo "
            "e se o bot está fazendo as perguntas adequadas para o seu nicho."
        )
        tip_title = "Ação recomendada esta semana"
    else:
        tip = (
            "🚨 Seu sistema está com baixo volume de leads qualificados. "
            "Entre em contato conosco o quanto antes — nossa equipe está pronta "
            "para revisar o fluxo e garantir que você não perca nenhuma oportunidade."
        )
        tip_title = "Atenção urgente necessária"

    subject = f"📊 Relatório {week} — {name} | MFL Digital Solutions"

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width">
  <style>
    body {{ font-family: 'DM Sans', Arial, sans-serif; background: #080C0A; color: #E8F0EA; margin: 0; padding: 0; }}
    .wrap {{ max-width: 600px; margin: 0 auto; }}
    .header {{ background: #0A0F0B; border-bottom: 2px solid #00C853; padding: 32px; text-align: center; }}
    .logo {{ font-size: 20px; font-weight: 800; color: #fff; }}
    .dot {{ color: #00C853; }}
    .body {{ padding: 32px; }}
    h2 {{ color: #fff; margin-top: 0; }}
    .score-box {{ background: #0E1410; border: 1px solid #1A2A1C; border-radius: 14px; padding: 24px; text-align: center; margin: 24px 0; }}
    .score-num {{ font-size: 64px; font-weight: 800; color: {color_score}; line-height: 1; }}
    .score-label {{ font-size: 18px; font-weight: 600; color: {color_score}; margin-top: 8px; }}
    .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 24px 0; }}
    .metric {{ background: #0E1410; border-radius: 10px; padding: 16px; }}
    .metric-val {{ font-size: 28px; font-weight: 800; color: #00C853; }}
    .metric-label {{ font-size: 12px; color: #5A7A5E; margin-top: 4px; }}
    .tip-box {{ background: #0E1410; border-left: 4px solid {color_score}; border-radius: 0 10px 10px 0; padding: 16px 20px; margin: 24px 0; }}
    .tip-title {{ font-weight: 700; color: #fff; margin-bottom: 8px; }}
    .tip-text {{ font-size: 14px; color: #7A917E; line-height: 1.6; }}
    .cta {{ background: #00C853; color: #060908; font-weight: 700; padding: 14px 28px; border-radius: 10px; text-decoration: none; display: inline-block; margin: 8px 0; }}
    .footer {{ background: #0A0F0B; padding: 24px 32px; text-align: center; font-size: 12px; color: #5A7A5E; border-top: 1px solid #1A2A1C; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="logo"><span class="dot">●</span> MFL Digital Solutions</div>
      <div style="font-size:13px;color:#5A7A5E;margin-top:8px;">Relatório Semanal • {week}</div>
    </div>

    <div class="body">
      <h2>Olá, {name}! 👋</h2>
      <p style="color:#7A917E;">Aqui está o resumo do seu sistema de qualificação de leads esta semana.</p>

      <div class="score-box">
        <div style="font-size:12px;color:#5A7A5E;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">Health Score</div>
        <div class="score-num">{score}</div>
        <div class="score-label">{label}</div>
      </div>

      <div class="metrics-grid">
        <div class="metric">
          <div class="metric-val">{raw.get('leads_30d', 0)}</div>
          <div class="metric-label">Leads (30 dias)</div>
        </div>
        <div class="metric">
          <div class="metric-val">{raw.get('hot', 0) + raw.get('warm', 0)}</div>
          <div class="metric-label">Leads Qualificados</div>
        </div>
        <div class="metric">
          <div class="metric-val">{raw.get('qualification_pct', 0)}%</div>
          <div class="metric-label">Taxa de Qualificação</div>
        </div>
        <div class="metric">
          <div class="metric-val">{raw.get('converted', 0)}</div>
          <div class="metric-label">Convertidos</div>
        </div>
      </div>

      <div class="tip-box">
        <div class="tip-title">💡 {tip_title}</div>
        <div class="tip-text">{tip}</div>
      </div>

      <div style="text-align:center;margin-top:28px;">
        <a href="http://localhost:5000/dashboard" class="cta">Ver Dashboard Completo →</a>
      </div>
    </div>

    <div class="footer">
      MFL Digital Solutions · Maceió-AL<br>
      <a href="#" style="color:#5A7A5E;">Cancelar recebimento</a> · 
      <a href="#" style="color:#5A7A5E;">Suporte</a>
    </div>
  </div>
</body>
</html>
"""
    return subject, html


def _log_simulated_email(client: dict, hs: dict):
    print(
        f"\n[SIMULATED EMAIL] → {client.get('email', 'sem email')}\n"
        f"  Cliente: {client.get('name')} | Score: {hs.get('health_score')}/100\n"
    )
