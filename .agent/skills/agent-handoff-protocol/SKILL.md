---
name: agent-handoff-protocol
description: |
  Define o protocolo de hierarquia de agentes de IA e transicao de contexto para o projeto
  MFL Digital Solutions. Ativado sempre que um novo agente (Claude ou Gemini) iniciar uma
  sessao de trabalho neste projeto. Garante continuidade total das tarefas sem perda de contexto.
---

# Protocolo de Hierarquia de Agentes - MFL Digital Solutions

## REGRA FUNDAMENTAL

Este projeto opera com um sistema de dois agentes em cascata:

| Agente | Modelo | Papel | Quando Ativo |
|--------|--------|-------|--------------|
| Agente Principal | Claude (Sonnet/Opus) | Estrategia, arquitetura, decisoes complexas, implementacoes criticas | Sempre que disponivel |
| Agente Intermediario | Gemini (Pro/Flash) | Continuidade de tarefas, execucao incremental, revisao de progresso | Quando Claude atingir limite de tokens ou estiver indisponivel |

**Instrucao OBRIGATORIA para qualquer agente que inicie uma sessao:**
Antes de qualquer acao, leia os artefatos de contexto da sessao atual e o estado das tarefas abertas. Voce esta continuando o trabalho de outro agente - NAO comece do zero.

---

## 1. CONTEXTO MESTRE DO PROJETO

A MFL Digital Solutions e uma plataforma B2B SaaS de automacao de qualificacao e follow-up de leads via WhatsApp, usando IA (GPT-4o / Claude Haiku). Sediada em Maceio-AL, Brasil.

Proposta de valor: PMEs (especialmente imobiliarias) perdem leads por nao responder rapido fora do horario comercial. A MFL qualifica leads automaticamente (score 0-100), classifica por temperatura (HOT/WARM/COLD) e so aciona o vendedor humano quando o lead esta pronto para fechar.

Nicho ancora: Imobiliarias. Expansao mapeada para: Clinicas -> Veiculos -> Contabilidade.

Fundador: Mateus - CEO, atua como orquestrador estrategico com auxilio de IA.

---

## 2. STACK TECNICA (FONTE DE VERDADE)

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.11 + Flask |
| Banco | SQLite (dev) -> PostgreSQL via Supabase (prod) |
| IA Principal | GPT-4o-mini (rotina) / GPT-4o (leads score > 70) |
| IA Fallback | Claude Haiku (Anthropic API) |
| Voice-to-Text | OpenAI Whisper API |
| WhatsApp Starter | Evolution API (self-hosted, Baileys) |
| WhatsApp Pro/Enterprise | 360dialog ou Gupshup (WABA oficial) |
| Scheduler | APScheduler (Celery+Redis apos 30+ clientes) |
| Frontend | HTML/JS puro autocontido (sem framework) |
| Hosting Backend | Railway |
| Hosting Frontend | Vercel |
| Controle de Versao | GitHub |

---

## 3. DIFERENCIAIS EXCLUSIVOS (INTOCAVEIS)

Estes sao os pilares de venda. Nenhuma decisao tecnica pode compromete-los:

1. Ficha HOT automatica - enviada ao corretor via WhatsApp quando o lead atinge score alto
2. Score de IA generativa (0-100) - avaliacao via GPT-4o em linguagem natural (nao regras)
3. Relatorio PDF mensal - gerado e entregue automaticamente no dia 1
4. Isolamento multi-tenant contratual - clausula explicita no contrato do cliente
5. Especializacao vertical - prompt/fluxo/score pre-configurado por nicho

---

## 4. MODELO DE NEGOCIO

| Plano | Mensalidade | Setup | Leads/mes |
|---|---|---|---|
| Starter | R$ 690 | Isento | Ate 50 |
| Pro | R$ 1.490 | R$ 990 | 50-300 |
| Enterprise | R$ 2.990 | R$ 1.990 | Ilimitado |

Add-ons ativos: WhatsApp extra (R), CRM extra (R), Calendly (R-390), Voice-to-Text (R), Relatorio PDF semanal (R).
Add-ons a criar: Campanha reativacao (R/mes), Instagram canal (R/mes), PWA mobile (incluso nos planos).

---

## 5. LACUNAS CRITICAS VS CONCORRENTES

Baseado na analise competitiva (Kommo, ManyChat, RD Conversas, SocialHub):

CRITICO (Antes do 5 cliente):
- PWA / App Mobile: Todos concorrentes tem. Solucao: transformar Dashboard atual em PWA.
- Instagram (Multicanal): Leads de trafego pago chegam pelo IG. Evolution API ja suporta via Baileys.

ALTA (Mes 3-4):
- Voice-to-Text (Whisper): 60% das msgs BR sao audio. API ja na arquitetura.
- Modulo de Reativacao de Leads: Add-on de alto ROI - disparo para base inativa.
- Analise de Sentimento: Flag visual no painel (irritado/empolgado/confuso).

ESCALA (Mes 5+):
- Integracao portais imobiliarios (ZAP/OLX/VivaReal): Nenhum concorrente tem.
- Construtor visual de fluxo (no-code): Interface para o cliente configurar prompts.
- IA Analyst no Dashboard: Gestor pergunta metricas em linguagem natural.

---

## 6. SEGURANCA - REGRA INEGOCIAVEL

- Toda tabela carrega tenant_id obrigatorio
- Toda query DEVE filtrar por tenant_id (sem excecao)
- Qualquer nova rota/query: avaliar impacto no isolamento multi-tenant antes de implementar
- Em caso de duvida sobre vazamento entre tenants: parar e perguntar

---

## 7. PROTOCOLO DE HANDOFF ENTRE AGENTES

Quando Claude (Principal) encerra uma sessao:
1. Registrar progresso no artefato task.md marcando [x] no feito e [/] no andamento.
2. Deixar nota de handoff descrevendo: o que foi feito, o pendente, e o proximo passo exato.
3. Atualizar o feature_backlog.md se alguma feature foi implementada ou mudou de status.

Quando Gemini (Intermediario) assume:
1. PRIMEIRO: Ler artefatos de sessao mais recentes em C:\Users\lenov\.gemini\antigravity-ide\brain\[conversation-id]\
2. SEGUNDO: Verificar task.md para entender estado das tarefas.
3. TERCEIRO: Verificar feature_backlog.md para entender backlog de produto.
4. QUARTO: Retomar exatamente de onde Claude parou - NAO recomecou do zero.
5. Ao encerrar: Seguir o mesmo protocolo de registro de progresso.

Principio central: Continuidade antes de criatividade. O agente que assume nunca recria o que ja existe. Verifica, compreende e continua.

---

## 8. PRINCIPIOS DE DECISAO (PARA QUALQUER AGENTE)

1. Reaproveitar antes de recriar - verificar o codigo existente antes de propor nova implementacao
2. Isolamento multi-tenant e inegociavel - toda feature nova passa por essa validacao
3. Simplicidade ate volume justificar complexidade - sem Redis/Celery/React antes de 30+ clientes
4. Custo de API e variavel de produto - decisoes de LLM impactam margem dos planos
5. Estabilizar antes de expandir - imobiliarias primeiro, depois clinicas, veiculos, etc.
6. Onboarding deve levar menos de 7 dias (meta: 3 dias) - toda feature e avaliada por esse criterio

---

## 9. ARQUIVOS-CHAVE DO REPOSITORIO

backend/app.py                     - Servidor Flask principal
backend/database.py                - Schema e ORM (verificar tenant_id em tudo)
backend/config.py                  - Configuracoes gerais
backend/modules/ai_classifier.py   - Integracao GPT-4o (3 camadas de IA aqui)
backend/modules/whatsapp_routes.py - Webhook Evolution API
backend/modules/whatsapp_sender.py - Envio ativo de mensagens
backend/modules/dashboard_routes.py- API de dados para os dashboards
backend/modules/auth_routes.py     - Autenticacao JWT
backend/modules/health_score.py    - Motor de score 0-100
backend/modules/followup.py        - Cadencias de follow-up
backend/modules/alerts.py          - Notificacoes proativas
frontend/landing/index.html        - Landing page (HTML/JS puro)
frontend/dashboards/               - Dashboards (migrar de JSX para HTML/JS)

---

Skill criada em: 2026-06-27. Atualizar sempre que novas decisoes estrategicas ou tecnicas forem tomadas.
