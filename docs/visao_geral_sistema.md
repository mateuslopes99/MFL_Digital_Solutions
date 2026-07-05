# Visão Geral do Sistema — MFL Digital Solutions

> **Para agentes de IA:** leia este documento antes de qualquer tarefa. Ele é a fonte de verdade sobre o que o sistema é, como funciona e quais são as decisões técnicas já tomadas.

---

## 1. O Que é a MFL Digital Solutions

A MFL Digital Solutions é uma plataforma **B2B SaaS** de automação de qualificação e follow-up de leads via WhatsApp com IA. Sediada em Maceió-AL, Brasil.

**Proposta de valor central:** pequenas e médias empresas perdem leads porque não conseguem responder rápido no WhatsApp — especialmente fora do horário comercial. A MFL qualifica automaticamente cada lead (score 0–100), classifica por temperatura (HOT/WARM/COLD), conduz follow-up automático e só aciona o vendedor humano quando o lead está pronto para fechar.

**Mercados atendidos:**

| Segmento | Produto | Público |
|---|---|---|
| **B2B — PMEs** | Triagem e qualificação de leads | Imobiliárias, Clínicas, Veículos, Contabilidade |
| **B2C — Pequenos negócios** | Agendamento e anti-falta | Manicures, Salões, Personal trainers, Dentistas de bairro |

**Fundador:** Mateus — CEO, atua como orquestrador estratégico com auxílio de IA (Claude + Gemini).

---

## 2. Fluxos de Funcionamento

### Fluxo B2B (Imobiliárias e PMEs)
1. **Captura:** Lead entra em contato via WhatsApp (Meta Ads, portais, links diretos)
2. **Atendimento 24/7:** IA inicia conversa instantaneamente, sem humano
3. **Qualificação:** GPT-4o avalia perfil, urgência, budget e intenção em linguagem natural
4. **Score 0–100:** Lead recebe pontuação baseada em critérios documentados
5. **Classificação:** TAG automática — HOT / WARM / COLD
6. **Ficha HOT:** Se score ≥ 75, o corretor recebe ficha estruturada no WhatsApp em ≤ 30 min
7. **Follow-up automático:** Cadências por temperatura — HOT (30 min) · WARM (24h/72h/7d) · COLD (3d/10d)
8. **CRM:** Dados inseridos automaticamente via webhook para Kommo, HubSpot, Pipedrive

### Fluxo Essencial (Pequenos negócios de serviço)
1. **Cliente envia mensagem no WhatsApp** (qualquer horário)
2. **IA responde:** tira dúvidas sobre serviços, preços e disponibilidade
3. **Agendamento pelo chat:** cliente informa dia/hora, IA confirma disponibilidade e registra
4. **Lembrete automático:** 24h antes e 1h antes do atendimento — cliente confirma ou reagenda
5. **Reativação:** clientes sem retorno há 30+ dias recebem mensagem automática personalizada
6. **Painel básico:** profissional vê agendamentos do dia, confirmações e faltas

---

## 3. Stack Tecnológica (Decisões Finais)

| Componente | Tecnologia | Observação |
|---|---|---|
| **Backend** | Python 3.11 + Flask | Modular, com rotas separadas por domínio |
| **Banco de Dados** | PostgreSQL via Supabase | SQLite apenas em desenvolvimento local |
| **IA Principal** | GPT-4o-mini | ~80% das conversas — custo otimizado |
| **IA Premium** | GPT-4o | Acionado quando score > 70 |
| **IA Fallback** | Claude Haiku (Anthropic) | Automático quando OpenAI está instável |
| **Voice-to-Text** | OpenAI Whisper | Transcrição de áudios — add-on R$190/mês |
| **WhatsApp Starter** | Evolution API (Baileys, self-hosted) | Até ~300 leads/mês por cliente, custo zero de licença |
| **WhatsApp Pro/Enterprise** | 360dialog ou Gupshup (WABA oficial) | Mais estável, dentro da política Meta |
| **Scheduler** | APScheduler | Migração para Celery + Redis apenas após 30+ clientes |
| **Frontend** | HTML/JS puro autocontido | Dashboards sem framework; Landing page HTML/JS |
| **Hosting Backend** | Railway | Com Procfile e railway.json configurados |
| **Hosting Frontend** | Vercel | Com vercel.json configurado |
| **Controle de Versão** | GitHub | |

> ⚠️ **Decisão técnica já tomada:** os Dashboards foram reconstruídos de React/JSX para HTML/JS puro. Não reverter para React sem necessidade justificada de complexidade.

---

## 4. Diferenciais Exclusivos (Nunca Comprometer)

Estes são os ativos centrais de venda. Qualquer refatoração deve preservá-los intactos:

1. **Ficha HOT automática** → enviada via WhatsApp ao corretor; nenhum concorrente tem
2. **Score IA generativa 0–100** → GPT-4o em linguagem natural, não baseado em regras rígidas
3. **Relatório PDF mensal** → entrega automática no dia 1; nenhum concorrente tem
4. **Isolamento multi-tenant contratual** → cláusula explícita no contrato, não apenas técnica
5. **Especialização vertical** → prompt/fluxo/score pré-configurado por nicho do cliente
6. **Preço fixo em BRL por empresa** → sem câmbio, sem cobrança por usuário (vantagem vs. Kommo)

---

## 5. Arquitetura de Segurança — Multi-Tenant

**Regra inegociável:** nenhum cliente pode, em nenhuma circunstância, acessar dados de outro cliente.

- Toda tabela carrega `tenant_id` obrigatório
- Toda query filtra por `tenant_id` — sem exceção
- Cada cliente tem número de WhatsApp próprio (instância dedicada na Evolution API)
- Autenticação JWT valida `tenant_id` em toda requisição
- Prompts de IA não compartilham contexto entre tenants
- Logs e auditoria registrados por `tenant_id`, usuário e timestamp

---

## 6. Manutenção, Suporte e Garantias

- **Monitoramento contínuo:** alertas automáticos quando API > 80% orçado, taxa de erro > 5% ou instância WA cai
- **Atualização de IA:** a evolução dos modelos (GPT-4o → futuras versões) é absorvida pela MFL sem custo adicional ao cliente
- **Sem lock-in:** o cliente cancela quando quiser; retenção por resultado, não por multa
- **Garantia de 14 dias:** devolução integral sem perguntas nas primeiras 2 semanas
- **LGPD nativo:** consentimento enviado automaticamente no início de toda conversa, com log de timestamp por tenant

---

*Última atualização: 2026-06-27 | Manter este arquivo em sincronia com decisões técnicas e estratégicas novas.*
