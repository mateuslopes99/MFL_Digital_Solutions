# MFL Digital Solutions
### Sistema de Triagem Automática de Leads via WhatsApp com IA

---

## Visão Geral

A **MFL Digital Solutions** oferece um sistema de automação inteligente que qualifica leads via WhatsApp 24/7 usando IA (GPT-4), distribui automaticamente para a equipe certa e registra tudo no CRM.

**Produto principal:** Triagem Automática de Leads via WhatsApp  
**Nicho inicial:** Imobiliárias em Maceió-AL  
**Modelo de negócio:** Setup (R$ 3.000) + Mensalidade (R$ 2.490/mês)

---

## Estrutura do Projeto

```
MFL_Digital_Solutions/
├── backend/                  ← API Flask + lógica do bot
│   ├── app.py                ← Servidor principal
│   ├── whatsapp_bot.py       ← Lógica de triagem com IA
│   ├── database.py           ← Gerenciamento do banco de dados
│   └── modules/
│       ├── ai_classifier.py  ← Classificação de leads com GPT-4
│       ├── crm_integration.py← Integração com CRM
│       └── notifier.py       ← Notificações para corretores
├── frontend/
│   ├── landing/              ← Landing page (HTML/CSS/JS)
│   └── dashboards/           ← Dashboard Admin e Cliente (React/JSX)
├── data/                     ← Banco de dados SQLite local
├── docs/                     ← Documentação técnica e comercial
├── .env.example              ← Template de variáveis de ambiente
├── requirements.txt          ← Dependências Python
└── README.md                 ← Este arquivo
```

---

## Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.11 + Flask |
| IA | OpenAI GPT-4 |
| WhatsApp | Twilio WhatsApp API |
| Banco de Dados | SQLite (dev) → PostgreSQL (prod) |
| Frontend | HTML/CSS/JS + React (dashboards) |
| Deploy | VPS (DigitalOcean/AWS) |

---

## Instalação e Setup

### 1. Clonar e criar ambiente virtual
```bash
cd MFL_Digital_Solutions
python -m venv .venv
.venv\Scripts\activate   # Windows
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente
```bash
copy .env.example .env
# Editar .env com suas chaves
```

### 4. Iniciar o servidor
```bash
python backend/app.py
```

---

## Pacotes Oferecidos

| Pacote | Setup | Mensalidade | Leads/mês |
|---|---|---|---|
| Basic | R$ 2.000 | R$ 990/mês | Até 200 |
| Pro | R$ 3.000 | R$ 2.490/mês | Até 500 |
| Enterprise | R$ 5.000 | R$ 4.990/mês | Ilimitado |

---

## Roadmap

- [x] Estrutura do projeto
- [x] Landing page
- [x] Dashboards (Admin + Cliente)
- [ ] Backend do bot (WhatsApp + IA)
- [ ] Integração Twilio
- [ ] Banco de dados de leads
- [ ] Dashboard funcional (conectado ao backend)
- [ ] Deploy em produção

---

*MFL Digital Solutions — Maceió-AL, 2026*
