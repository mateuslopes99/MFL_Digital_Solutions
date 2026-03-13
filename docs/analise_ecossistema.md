# Análise do Ecossistema: MFL Digital Solutions

## 1. Visão Geral do Sistema
O sistema MFL Digital Solutions atua como um software de agência (SaaS White-label) desenhado para gerenciar leads, automações e comunicação (via WhatsApp) de forma escalável. Ele possui duas principais visões no Dashboard (Cliente e Admin) permitindo tanto o acompanhamento de KPIs de vendas quanto a gestão de custos (uso de tokens e APIs).

## 2. O Que Falta Implementar ou Configurar

### A. Backend e Processamentos
- **Deduplicação de Leads (Edge Cases):** Refinamento da lógica de deduplicação no banco de dados (por número de telefone e email) para evitar cobranças indevidas de tokens em repetições, melhorando a consistência em `leads_routes.py`.
- **Sistema de Filas (Queueing) e Retry:** Implementação de um gerenciador de filas robusto (como Celery + Redis ou similar) para garantir que requisições falhas de APIs externas (WhatsApp, LLMs) sejam tentadas novamente (`retry mechanism`).
- **Agendamento de Follow-ups Dinâmico:** Conversão dos agendamentos engatilhados na base de dados para executarem via cron jobs/processos em background automaticamente de acordo com o status modificado do Lead.
- **Segurança de Endpoints:** Inclusão/revisão rigorosa de `rate-limiting` (proteção contra brute-force) nas rotas sensíveis e validação JWT baseada em permissões (RBAC) para separar Administrador vs. Cliente de forma robusta.

### B. Frontend (Dashboard)
- **Dashboard Admin (`DashboardAdmin.jsx`):** Ligação fluída (binding) de dados com o backend real, incluindo:
  - Gerenciamento do custo total de tokens (Visão da Agência).
  - Status em tempo real dos workers e schedulers.
  - Monitoramento de gastos com provedores de Inteligência Artificial.
- **Ações em Massa no Dashboard do Cliente (`DashboardCliente.jsx`):** Refinamento de UI/UX para permitir seleção de múltiplos leads para ações como mudança de pipeline ou exportação rápida para CSV/Excel.

### C. Deploy e Integração Contínua (CI/CD)
- **Railway Deployment:** Consolidar e validar os arquivos `Procfile` e `railway.json` no Railway, configurando ou provisionando também um banco de dados persistente (ex: PostgreSQL gerenciado) substituindo o SQLite para ambiente de produção.
- **Integração Git (CI/CD):** Configuração de um pipeline seguro via GitHub Actions para execução de testes unitários antes do deploy automático à produção.

## 3. APIs e Integrações Necessárias
Para tornar a automação do sistema 100% autônoma e inteligente:

1. **Evolution API / Baileys (ou Cloud API WhatsApp Oficial):**
   - **Objetivo:** Disparo e recebimento reativo/massivo de mensagens de WhatsApp. Requer Webhooks conectados à URL do Railway.
2. **OpenAI (GPT-4) / Anthropic (Claude 3.5):**
   - **Objetivo:** O motor cognitivo de triagem. Avalia intenções, agenda conexões e filtra Leads. É vital controlar rigorosamente os limites de consumo de tokens.
3. **Meta Graph API (Facebook / Instagram Ads):**
   - **Objetivo:** Ingresso instantâneo dos formulários do Meta Leads nativamente no pipeline do `leads_routes.py`, reduzindo a dependência de plataformas como Zapier e mantendo tempo real.
4. **Gateway de Faturamento (Stripe / Mercado Pago):**
   - **Objetivo:** Emitir faturamentos baseados nos planos de uso/tokens adotados pelos clientes. Possibilita travar operações do whitelabel em caso de inadimplência de cobrança de add-ons/mensalidades.
5. **Google Calendar API (Integração de Agenda):**
   - **Objetivo:** Após a negociação bem-sucedida liderada pela IA, adicionar de forma síncrona os eventos ao calendário dos clientes para não ocorrer conflitos de horários.

## 4. Próxima Etapas (Memória do Sistema)
Este mapeamento será usado para priorizar o roadmap tecnológico do MFL Digital Solutions. A infraestrutura exige foco inicial na estabilidade em nuvem (Railway) e na fluidez dos dados perante os dois Dashboards do ecossistema.
