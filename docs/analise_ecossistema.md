# Análise do Ecossistema: MFL Digital Solutions

## 1. Visão Geral do Sistema

O sistema MFL Digital Solutions é uma plataforma **B2B SaaS** de automação de qualificação e follow-up de leads via WhatsApp com IA. Possui duas visões de Dashboard (Cliente e Admin) e opera com arquitetura **multi-tenant** — cada cliente (imobiliária, clínica, etc.) opera em isolamento total de dados.

> **Fonte de verdade:** este documento cruza a análise do ecossistema técnico com o Contexto Mestre do projeto e a análise competitiva (vs. Kommo, ManyChat, RD Conversas, SocialHub). Qualquer agente de IA deve ler este arquivo antes de iniciar uma tarefa.

---

## 2. Tarefas Prioritizadas — Do Básico ao Avançado

As tarefas estão ordenadas em 5 níveis de prioridade. **Não avançar para o próximo nível sem concluir o anterior.**

---

### 🔴 P0 — BLOQUEADORES (Sem isso, nenhum cliente pode entrar em produção)

Estas tarefas são pré-requisitos absolutos. Falhar aqui compromete segurança, dados e a viabilidade legal do produto.

| # | Tarefa | Status | Ação Restante |
|---|---|---|---|
| 1 | **Migração SQLite → PostgreSQL (Supabase)** | ⚠️ 95% pronto | Criar banco no Supabase, copiar `DATABASE_URL` para Railway, executar `init_db()` em produção |
| 2 | **Rate Limiting + RBAC** | ✅ **FEITO** | `flask-limiter` ativo: 10 req/min no auth, 60/min no webhook. Nenhuma ação restante |
| 3 | **Isolamento Multi-Tenant — Auditoria Formal** | ✅ **CORRIGIDO** | `get_leads()` sem `client_id` agora lança `ValueError` — vazamento bloqueado em `database.py` |
| 4 | **Variáveis de Ambiente Seguras** | ✅ **CORRIGIDO** | Chave OpenAI removida do `.env`; `.env` nunca foi commitado no git. **Revogar chave antiga em platform.openai.com e gerar nova** |
| 5 | **Consentimento LGPD** | ✅ **FEITO** | Implementado em `whatsapp_routes.py` com log no banco por tenant. Nenhuma ação restante |

> ⚠️ **Única pendência real do P0:** configurar o Supabase e apontar `DATABASE_URL` no Railway. Todos os outros bloqueadores estão resolvidos.

---

### 🟠 P1 — NÚCLEO DO PRODUTO (O que faz a MFL funcionar e ser vendável)

Com P0 resolvido, estas tarefas constroem o valor central entregue ao cliente.

| # | Tarefa | Arquivo(s) Afetado(s) | Critério de Conclusão |
|---|---|---|---|
| 6 | **3 Camadas de IA com Fallback Automático** | `ai_classifier.py` | GPT-4o-mini (padrão) → GPT-4o (score > 70) → Claude Haiku (fallback OpenAI down) |
| 7 | **Score de Lead 0–100 visível no Dashboard** | `health_score.py`, `dashboard_routes.py`, `DashboardCliente` | Score calculado + exibido com critérios legíveis (urgência, budget, região) |
| 8 | **TAGs automáticas HOT / WARM / COLD** | `health_score.py`, `leads_routes.py` | Tags atribuídas automaticamente com base no score, visíveis no painel |
| 9 | **Ficha HOT enviada ao vendedor via WhatsApp** | `whatsapp_sender.py`, `followup.py` | Quando score ≥ 75: mensagem estruturada (nome, interesse, budget, urgência) enviada ao corretor em ≤ 30 min |
| 10 | **Cadências de Follow-up por Temperatura** | `followup.py`, APScheduler | HOT: 30 min · WARM: 24h/72h/7 dias · COLD: 3 dias/10 dias — todas funcionando e testadas |
| 11 | **Agendamento de Follow-ups Dinâmico (cron)** | `followup.py`, `app.py` | Follow-ups disparam automaticamente via background process ao mudar status do lead |
| 12 | **Dashboard do Cliente conectado a dados reais** | `DashboardCliente.jsx` → migrar para HTML/JS | Volume de leads, score médio, conversão e histórico de conversa — todos de API real |
| 13 | **Dashboard Admin conectado a dados reais** | `DashboardAdmin.jsx` → migrar para HTML/JS | Visão de todos os clientes, consumo de tokens por tenant, margem por cliente |

---

### 🟡 P2 — INFRAESTRUTURA & CONFIABILIDADE (Estabilidade para operar com clientes reais)

| # | Tarefa | Arquivo(s) Afetado(s) | Critério de Conclusão |
|---|---|---|---|
| 14 | **Deduplicação de Leads (telefone + email)** | `leads_routes.py`, `database.py` | Mesmo lead não duplicado; sem dupla cobrança de tokens |
| 15 | **Logging estruturado por `conversation_id`** | `ai_classifier.py`, `whatsapp_routes.py` | Cada conversa loga: tokens usados, custo estimado, modelo acionado, tenant |
| 16 | **Sistema de Alertas Internos** | `alerts.py` | Alerta ao admin quando: API > 80% orçado, taxa erro > 5%, instância WA cai |
| 17 | **Relatório PDF Mensal Automático** | Novo: `pdf_report.py` (WeasyPrint/ReportLab) | Gerado e enviado por email no dia 1 de cada mês, por tenant |
| 18 | **Deploy CI/CD via GitHub Actions** | `.github/workflows/`, `Procfile`, `railway.json` | Push na `main` → testes rodam → deploy automático no Railway se passar |
| 19 | **Retry Mechanism para APIs externas** | `whatsapp_sender.py`, `ai_classifier.py` | Falha na OpenAI ou WhatsApp: retry automático com exponential backoff (3x) |

---

### 🟢 P3 — EXPANSÃO COMERCIAL (Features que aumentam receita e fecham lacunas vs. concorrentes)

| # | Tarefa | Diferencial vs. Concorrente | Critério de Conclusão |
|---|---|---|---|
| 20 | **PWA (Progressive Web App)** | Todos concorrentes têm app mobile — MFL não | Dashboard acessível no celular via navegador sem instalação, com ícone na tela inicial |
| 21 | **Voice-to-Text via Whisper** | Kommo Pro tem; MFL no roadmap | Áudios de WhatsApp transcritos antes da qualificação; add-on R$190/mês ativável |
| 22 | **Instagram como canal adicional** | Kommo/ManyChat têm multicanal | Evolution API conectada ao Instagram Direct; leads do IG entram no mesmo funil |
| 23 | **Módulo de Reativação de Leads** | ChatGuru/SocialHub têm; MFL não | Interface no Admin para disparar campanha para base inativa segmentada por tag |
| 24 | **Análise de Sentimento básica** | Raro no mercado — diferencial | Flag visual no painel: irritado / empolgado / confuso por lead |
| 25 | **Integração webhook de saída para CRMs** | Kommo e SocialHub têm nativo | Webhook configurável para Kommo, HubSpot, Pipedrive via painel do cliente |
| 26 | **Meta Graph API — Leads de formulário** | Elimina dependência do Zapier | Lead de anúncio Meta cai direto no pipeline sem intermediário |
| 27 | **Gateway de Cobrança Recorrente** | Necessidade operacional | Asaas ou Mercado Pago: planos + add-ons cobrados automaticamente, bloqueio por inadimplência |

---

### 🔵 P4 — ESCALA E DIFERENCIAÇÃO MÁXIMA (Após 10+ clientes ativos)

| # | Tarefa | Impacto | Quando |
|---|---|---|---|
| 28 | **Integração portais imobiliários (ZAP/OLX/VivaReal)** | Maior diferencial possível para nicho âncora — nenhum concorrente tem | Após 5 clientes |
| 29 | **Construtor visual de fluxo (no-code)** | Reduz dependência do suporte; cliente configura seus próprios prompts | Mês 4–5 |
| 30 | **IA Analyst no Dashboard** | Gestor pergunta "qual corretor fechou mais?" em linguagem natural | Mês 4–6 |
| 31 | **Prospecção por CNPJ integrada** | Para nichos B2B (contabilidade, agro) | Mês 5+ |
| 32 | **Agendamento automático (Google Calendar / Calendly)** | Leads HOT viram reuniões sem intervenção humana | Mês 3–4 (add-on R$290-390) |
| 33 | **Migração APScheduler → Celery + Redis** | Necessário apenas com 30+ clientes simultâneos | Só quando volume justificar |
| 34 | **Modelo White-label para agências** | Revenda por parceiros com comissão 25–30% recorrente | Mês 5–6 |
| 35 | **Templates de prompt por nicho (Clínicas, Veículos)** | Expansão para 2º e 3º mercado | Após estabilizar imobiliárias |

---

## 3. APIs e Integrações — Status e Ordem de Implementação

| API / Serviço | Status | Prioridade | Observação |
|---|---|---|---|
| **Evolution API (WhatsApp)** | ⚠️ Parcial | P0 | Webhook deve estar conectado ao Railway em produção |
| **OpenAI GPT-4o / GPT-4o-mini** | ⚠️ Parcial | P1 | Implementar as 3 camadas com lógica de custo |
| **Anthropic Claude Haiku** | ❌ Falta | P1 | Fallback automático quando OpenAI cair |
| **OpenAI Whisper** | ❌ Falta | P3 | Transcrição de áudios; add-on R$190/mês |
| **Supabase (PostgreSQL)** | ⚠️ Script pronto | P0 | Migrar e validar antes de qualquer cliente |
| **Meta Graph API (Instagram/Leads)** | ❌ Falta | P3 | Leads de formulário + multicanal Instagram |
| **Google Calendar API** | ❌ Falta | P4 | Add-on agendamento para leads HOT |
| **Asaas / Mercado Pago** | ❌ Falta | P3 | Cobrança recorrente automatizada |

---

## 4. Diferenciais Exclusivos — Nunca Comprometer

Estas features são o argumento central de venda. **Qualquer refatoração deve preservá-las intactas:**

1. **Ficha HOT automática** → enviada via WhatsApp ao corretor (nenhum concorrente tem)
2. **Score IA generativa 0–100** → GPT-4o em linguagem natural, não regras rígidas
3. **Relatório PDF mensal** → entrega automática no dia 1 (nenhum concorrente tem)
4. **Isolamento multi-tenant contratual** → cláusula explícita, não apenas técnica
5. **Especialização vertical** → prompt/fluxo pré-configurado para o nicho do cliente

---

## 5. Próximas Etapas Imediatas

Foco total em **P0** antes de qualquer outra coisa:

1. Finalizar migração PostgreSQL/Supabase e validar em ambiente Railway
2. Auditar todas as rotas para isolamento `tenant_id`
3. Configurar rate limiting e RBAC no `auth_routes.py`
4. Ativar consentimento LGPD no webhook de entrada do WhatsApp

Depois de P0 validado → iniciar P1 (Motor de IA, Score, Ficha HOT, Follow-up).

---

*Última atualização: 2026-06-27 | Documento mantido como fonte de verdade técnica e estratégica do projeto.*
