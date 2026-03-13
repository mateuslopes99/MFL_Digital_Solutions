# Visão Geral do Sistema - MFL Digital Solutions

Este documento serve como um guia consolidado sobre a arquitetura, funcionalidades, ferramentas, planos e operações de suporte da **MFL Digital Solutions**, com foco em nosso Produto Principal: **Triagem Automática de Leads via WhatsApp com IA**.

---

## 1. O Sistema: Triagem Automática de Leads via WhatsApp

O sistema da MFL Digital Solutions é uma plataforma inteligente B2B projetada inicialmente para o nicho de imobiliárias em Maceió-AL. Ele automatiza completamente o atendimento inicial de leads capturados em campanhas (ex. Meta Ads, Google Ads).

### Fluxo de Funcionamento:
1. **Captura:** O lead entra em contato via WhatsApp através de anúncios ou links diretos.
2. **Atendimento 24/7:** O bot integrado ao WhatsApp inicia a conversa instantaneamente.
3. **Qualificação com IA:** Utilizando inteligência artificial (GPT-4), o sistema entende o perfil, as necessidades e a urgência do lead.
4. **Classificação:** O lead recebe uma TAG de temperatura (HOT, WARM, COLD) baseada no seu grau de interesse.
5. **Distribuição/Roteamento:** A depender das regras da imobiliária (e do plano contratado), o lead é roteado para o corretor correto de forma inteligente.
6. **Integração CRM:** Todos os dados da conversa, resumo do perfil e contatos são inseridos automaticamente no CRM (Ex: RD Station, Pipedrive).

---

## 2. Principais Funções e Capacidades

- **Atendimento Contínuo e Automático (24/7):** Sem perda de leads de madrugada ou finais de semana e feriados.
- **Análise Perceptiva:** O bot utiliza IA avançada não apenas para seguir menus de opções, mas conversar em linguagem natural, entendendo contexto.
- **Dashboards em Tempo Real:** 
  - **Dashboard Cliente:** Onde o cliente (imobiliária) acompanha o tráfego de leads qualificados, taxas de conversão e relatórios.
  - **Dashboard Admin:** Onde a MFL gerencia as instâncias dos clientes e performance dos bots.
- **Roteamento Inteligente:** Distribuição dos leads de acordo com o corretor, a região desejada do imóvel ou equipe responsável.
- **Follow-up Automático:** Automação multi-etapas para re-engajar leads que pararam de responder.

---

## 3. Stack Tecnológica e Ferramentas Usadas

A arquitetura do sistema foi desenhada para ser escalável, modular e robusta:

### **Backend (Cérebro do Sistema)**
- **Linguagem / Framework:** Python 3.11 + Flask (Gerenciamento da lógica da API e integração de rotas).
- **Inteligência Artificial:** OpenAI GPT-4 API (Para processamento de linguagem natural e classificação do lead).
- **Integração de Mensageria:** Twilio WhatsApp API (Gerenciamento seguro dos disparos e recebimento de mensagens do WhatsApp).
- **Banco de Dados:** SQLite (Desenvolvimento) com transição para PostgreSQL (Produção).

### **Frontend (Painéis Administrativos e Landing Page)**
- **Tecnologias Básicas:** HTML5, CSS3, e JavaScript Vanilla para a arquitetura de apresentação comercial.
- **Dashboards:** React / JSX para interfaces reativas, de alta performance e experiência "seamless".

### **Infraestrutura e Deploy**
- **Hospedagem:** Servidores dedicados virtuais (VPS) via DigitalOcean e/ou AWS.

---

## 4. Planos e Pacotes Oferecidos

A MFL Digital Solutions oferece 4 modelos flexíveis de assinatura (valores de referência):

1. **Starter (R$ 790/mês | Zero Setup):** 
   - Até 50 leads/mês. Qualificação IA, Dashboard, integração com 1 CRM e Relatório mensal.
2. **Básico (R$ 1.490/mês | Setup R$ 990):** 
   - Até 200 leads/mês. Incrementa velocidade no suporte e volume.
3. **Pro (R$ 2.790/mês | Setup R$ 2.500):** *Mais Vendido*
   - Até 600 leads/mês. Inclui Distribuição Inteligente, Follow-up automático multi-etapa, 3 integrações CRM, e Suporte WhatsApp Prioritário.
4. **Enterprise (R$ 5.490/mês | Setup R$ 4.500):** 
   - Leads Ilimitados. Customização extrema, Account Manager, Treinamentos da equipe e Uptime garantido em SLA.

---

## 5. Add-ons (Módulos Expansíveis)
Clientes de qualquer pacote podem comprar melhorias avulsas para suas operações sem precisar mudar de assinatura imediatamente:

- **WhatsApp Extra:** + R$ 490/mês
- **Integração CRM Extra:** + R$ 290/mês
- **Relatório PDF Semanal Customizado:** + R$ 190/mês
- **Onboarding Acelerado (em 1 dia):** Pagamento Único de R$ 1.490
- **Treinamento Extra de Equipe (4h):** Pagamento Único de R$ 990

---

## 6. Manutenção e Suporte (Política de Qualidade)

Temos como premissa ser um parceiro que elimina as dores tecnológicas das imobiliárias. Nosso modelo de segurança e retenção inclui:

- **Hospedagem "White-Glove":** Servidores integralmente monitorados. Caso ocorra queda nas integrações externas, nossas instâncias se reerguem e tratam engarrafamentos automaticamente, processo 100% invisível ao cliente.
- **Atualização Contínua da IA:** Acompanhamos a evolução das LLMs mantendo a API GPT sempre em suas versões mais precisas. O cliente não gasta com integrações de novos modelos, nós absorvemos o upgrade de fluxo.
- **Sem "Lock-in" / Fidelidade:** Retemos o cliente pelos resultados e clareza, não por multas (SaaS puro).
- **Garantia de 14 dias:** Política de arrependimento (Risco Zero / Money-Back) sem perguntas nas duas primeiras semanas.
