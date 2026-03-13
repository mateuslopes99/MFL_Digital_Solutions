
# -*- coding: utf-8 -*-
"""
Reconstrói o dashboard_completo_html.html com encoding correto e JS limpo.
"""
import re, sys

FILE = r"C:\Users\lenov\MFL_Digital_Solutions\frontend\dashboards\dashboard_completo_html.html"

# Lê o arquivo como bytes e decodifica corretamente
with open(FILE, 'rb') as f:
    raw = f.read()

# Tenta detectar o encoding correto
try:
    content = raw.decode('utf-8')
    print("Lido como UTF-8")
except UnicodeDecodeError:
    content = raw.decode('latin-1')
    # Reconverte: latin-1 → bytes → utf-8 (corrige double-encoding)
    try:
        content = content.encode('latin-1').decode('utf-8')
        print("Corrigido double-encoding latin-1→utf-8")
    except Exception:
        print("Mantendo latin-1 decodificado")

# ── JS limpo para substituir renderClientTab, renderLeadsTab, renderPerformanceTab ──
NEW_JS = r"""
    // ── CLIENT RENDERING ─────────────────────────────────────────────────────────
    function renderClientTab(tab) {
      const content = document.getElementById('clientContent');
      const G = TEMPLATES[currentNiche].colors.primary;
      const hotCount  = LEADS.filter(l => l.classification === 'HOT').length;
      const warmCount = LEADS.filter(l => l.classification === 'WARM').length;
      const coldCount = LEADS.filter(l => l.classification === 'COLD').length;

      if (tab === 'resumo') {
        const alerts = [
          { level:'warn', icon:'⚠️', msg:'Taxa de resposta subiu para 2m 47s — acima da meta (2min)', action:'Contratar mais 1 corretor' },
          { level:'ok',   icon:'✅', msg:'Taxa HOT acima da média do mercado esta semana', action:null },
          { level:'info', icon:'💡', msg:'89 leads recebidos na sexta — pico da semana, considere reforço', action:'Agendar corretor extra' },
        ];
        const alertsHtml = alerts.map(a => `
          <div style="display:flex;align-items:flex-start;gap:12px;padding:12px 0;border-bottom:1px solid var(--border);">
            <span style="font-size:18px;">${a.icon}</span>
            <div style="flex:1;">
              <div style="font-size:13px;color:var(--white);">${a.msg}</div>
              ${a.action ? `<div style="font-size:11px;color:var(--green);margin-top:4px;">→ Ação sugerida: ${a.action}</div>` : ''}
            </div>
            <span style="font-size:10px;color:${a.level==='warn'?'var(--orange)':a.level==='ok'?'var(--green)':'var(--blue)'};font-weight:700;padding:3px 10px;border-radius:100px;background:${a.level==='warn'?'rgba(255,152,0,0.13)':a.level==='ok'?'rgba(0,200,83,0.13)':'rgba(33,150,243,0.13)'};white-space:nowrap;">${a.level==='warn'?'Atenção':a.level==='ok'?'Ótimo':'Info'}</span>
          </div>`).join('');

        const benchmarks = [
          { label:'Taxa de qualificação', you:78,  market:65,  unit:'%', hb:true  },
          { label:'Tempo de resposta',    you:107, market:110, unit:'s', hb:false },
          { label:'Taxa de conversão',    you:18,  market:22,  unit:'%', hb:true  },
          { label:'Follow-up médio',      you:2,   market:3.5, unit:'x', hb:true  },
        ];
        const benchHtml = benchmarks.map(b => {
          const ok = b.hb ? b.you >= b.market : b.you <= b.market;
          const py = b.hb ? Math.min(b.you/(b.market*1.5)*100,100) : Math.min((b.market*1.5-b.you)/(b.market*1.5)*100,100);
          const pm = b.hb ? Math.min(b.market/(b.market*1.5)*100,100) : 33;
          const yl = b.unit==='s' ? Math.floor(b.you/60)+'m '+(b.you%60)+'s' : b.you+b.unit;
          const ml = b.unit==='s' ? Math.floor(b.market/60)+'m '+(b.market%60)+'s' : b.market+b.unit;
          return `<div style="margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
              <span style="font-size:12px;color:var(--white);">${b.label}</span>
              <span style="font-size:12px;color:${ok?'var(--green)':'var(--orange)'};font-weight:700;">${ok?'▲ Acima':'▼ Abaixo'} do mercado</span>
            </div>
            <div style="position:relative;height:8px;background:var(--surface2);border-radius:100px;margin-bottom:4px;">
              <div style="position:absolute;height:8px;border-radius:100px;background:rgba(120,144,156,0.4);width:${pm}%;"></div>
              <div style="position:absolute;height:8px;border-radius:100px;background:${ok?G:'var(--orange)'};width:${py}%;transition:width .6s;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;">
              <span style="font-size:10px;color:${ok?G:'var(--orange)'};font-weight:700;">Você: ${yl}</span>
              <span style="font-size:10px;color:var(--muted);">Mercado: ${ml}</span>
            </div>
          </div>`;
        }).join('');

        const weeks=['Sem 1','Sem 2','Sem 3','Sem 4'];
        const tv=[210,248,289,312], th=[38,44,52,61], mx=312;
        const trendHtml = tv.map((v,i)=>{
          const hp=(v/mx)*100, hotp=(th[i]/v)*hp, last=i===3;
          return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;">
            <span style="font-size:10px;color:${last?G:'var(--muted)'};font-weight:${last?700:400};">${v}</span>
            <div style="width:100%;display:flex;flex-direction:column;justify-content:flex-end;height:60px;gap:2px;">
              <div style="width:100%;border-radius:4px 4px 0 0;background:rgba(255,61,0,0.7);height:${hotp*0.6}px;"></div>
              <div style="width:100%;background:${last?G:'rgba(0,200,83,0.4)'};height:${(hp-hotp)*0.6}px;"></div>
            </div>
            <span style="font-size:10px;color:var(--muted);">${weeks[i]}</span>
          </div>`;
        }).join('');

        const recs=[
          {num:'1️⃣',title:'Aumentar tempo de resposta',cur:'2m 47s',tgt:'< 2min',imp:'R$ 5.200/mês',act:'Escalar equipe em 1 corretor no pico (sexta-feira)'},
          {num:'2️⃣',title:'Melhorar follow-up',cur:'2 tentativas',tgt:'4 tentativas',imp:'R$ 2.100/mês',act:'Ativar follow-up automático no painel de configurações'},
          {num:'3️⃣',title:'Qualificar leads COLD',cur:'24% cold sem retorno',tgt:'< 15% descartados',imp:'R$ 3.800/mês',act:'Reativar leads COLD com mensagem automática de 7 dias'},
        ];
        const recsHtml=recs.map(r=>`<div style="padding:14px 0;border-bottom:1px solid var(--border);">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div style="font-size:13px;font-weight:700;color:var(--white);">${r.num} ${r.title}</div>
            <span style="font-size:11px;color:var(--green);font-weight:700;white-space:nowrap;margin-left:12px;">${r.imp}</span>
          </div>
          <div style="display:flex;gap:16px;margin-top:6px;">
            <span style="font-size:11px;color:var(--muted);">Atual: <b style="color:var(--orange);">${r.cur}</b></span>
            <span style="font-size:11px;color:var(--muted);">Meta: <b style="color:${G};">${r.tgt}</b></span>
          </div>
          <div style="font-size:11px;color:var(--muted);margin-top:4px;">→ ${r.act}</div>
        </div>`).join('');

        content.innerHTML = `
        <div class="kpi-grid">
          <div class="kpi-card"><div class="kpi-glow" style="background:radial-gradient(circle,${G},transparent);"></div><div class="kpi-icon">📨</div><div class="kpi-label">Leads recebidos</div><div class="kpi-value" style="color:${G};">${fmt(312)}</div><div class="kpi-sub">Fevereiro 2026</div><div class="kpi-delta positive">↑ 18% vs mês anterior</div></div>
          <div class="kpi-card"><div class="kpi-glow" style="background:radial-gradient(circle,#2196F3,transparent);"></div><div class="kpi-icon">⏱️</div><div class="kpi-label">Tempo médio resposta</div><div class="kpi-value" style="color:#2196F3;">1m 47s</div><div class="kpi-sub">Meta: &lt; 2 min</div><div class="kpi-delta positive">↑ 34% melhor</div></div>
          <div class="kpi-card"><div class="kpi-glow" style="background:radial-gradient(circle,#FF3D00,transparent);"></div><div class="kpi-icon">🔥</div><div class="kpi-label">Leads HOT</div><div class="kpi-value" style="color:#FF3D00;">${hotCount}</div><div class="kpi-sub">${Math.round(hotCount/LEADS.length*100)}% do total</div><div class="kpi-delta positive">↑ 22% mais</div></div>
          <div class="kpi-card"><div class="kpi-glow" style="background:radial-gradient(circle,#00C853,transparent);"></div><div class="kpi-icon">✅</div><div class="kpi-label">Fechamentos</div><div class="kpi-value" style="color:#00C853;">18</div><div class="kpi-sub">este mês</div><div class="kpi-delta positive">↑ 12% vs anterior</div></div>
        </div>
        <div class="card" style="margin-bottom:16px;"><div class="card-title">🔔 Alertas Proativos</div>${alertsHtml}</div>
        <div class="card" style="margin-bottom:16px;">
          <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;">📈 Tendência (últimas 4 semanas)<span style="font-size:11px;color:var(--green);font-weight:600;">↑ +18%</span></div>
          <div style="display:flex;align-items:flex-end;gap:8px;height:80px;">${trendHtml}</div>
          <div style="display:flex;gap:16px;margin-top:10px;">
            <span style="font-size:11px;color:var(--muted);"><span style="display:inline-block;width:8px;height:8px;background:var(--green);border-radius:2px;margin-right:4px;"></span>Leads totais</span>
            <span style="font-size:11px;color:var(--muted);"><span style="display:inline-block;width:8px;height:8px;background:rgba(255,61,0,0.7);border-radius:2px;margin-right:4px;"></span>HOTs</span>
          </div>
        </div>
        <div class="card" style="margin-bottom:16px;"><div class="card-title">📊 Você vs Mercado</div>${benchHtml}</div>
        <div class="card" style="margin-bottom:16px;">
          <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;">🎯 Recomendações<span style="font-size:11px;color:var(--green);font-weight:700;background:rgba(0,200,83,0.13);padding:3px 10px;border-radius:100px;">💰 +R$ 11.100/mês</span></div>
          ${recsHtml}
        </div>
        <div class="card"><div class="card-title">Classificação de Leads</div>${renderClassification(hotCount,warmCount,coldCount)}</div>
        <div class="card" style="margin-top:16px;"><div class="card-title">Atividade recente</div>
          ${LEADS.slice(0,4).map(l=>`<div class="activity-item">${getClassificationBadge(l.classification)}<div class="activity-lead"><span class="activity-name">${l.name}</span><span class="activity-property">${l.property}</span></div><span class="activity-time">${l.time} · ${l.day}</span><span class="activity-status" style="background:${l.status==='Fechado ✓'?'rgba(0,200,83,0.13)':'var(--surface2)'};color:${l.status==='Fechado ✓'?G:'var(--muted)'};">${l.status}</span></div>`).join('')}
        </div>`;

      } else if (tab === 'leads') {
        renderLeadsTab(content);
      } else if (tab === 'performance') {
        renderPerformanceTab(content);
      }
    }

    function renderLeadsTab(content) {
      const G = TEMPLATES[currentNiche].colors.primary;
      const filtered = LEADS.filter(l => {
        const mf = currentFilter === 'Todos' || l.classification === currentFilter;
        const ms = l.name.toLowerCase().includes(searchQuery.toLowerCase()) || l.phone.includes(searchQuery);
        return mf && ms;
      });
      content.innerHTML = `
      <div class="filter-bar">
        <input type="text" class="search-input" placeholder="🔍  Buscar por nome ou telefone..." value="${searchQuery}" onkeyup="handleSearch(event)">
        ${['Todos','HOT','WARM','COLD'].map(f=>`<button class="filter-btn ${currentFilter===f?'active':''} ${f.toLowerCase()}" onclick="setFilter('${f}')">${f}</button>`).join('')}
        <span class="filter-count">${filtered.length} leads</span>
      </div>
      <div class="table-wrapper"><table>
        <thead><tr><th>Lead</th><th>Contato</th><th>Origem</th><th>Imóvel</th><th>Orçamento</th><th>Urgência</th><th>Classificação</th><th>Corretor</th><th>Status</th></tr></thead>
        <tbody>${filtered.map(l=>`<tr>
          <td><div class="cell-name">${l.name}</div><div class="cell-time">${l.time} · ${l.day}</div></td>
          <td style="color:var(--muted);">${l.phone}</td><td>${l.source}</td>
          <td style="max-width:140px;">${l.property}</td>
          <td style="color:${G};font-weight:600;">${l.budget}</td>
          <td><span style="font-size:11px;color:${l.urgency==='Alta'?'var(--red)':l.urgency==='Média'?'var(--orange)':'var(--gray)'};font-weight:600;">${l.urgency}</span></td>
          <td>${getClassificationBadge(l.classification)}</td>
          <td>${l.agent}</td>
          <td><span style="font-size:11px;padding:3px 10px;border-radius:100px;background:${l.status==='Fechado ✓'?'rgba(0,200,83,0.13)':l.status.includes('Reunião')?'rgba(255,61,0,0.13)':'var(--surface2)'};color:${l.status==='Fechado ✓'?'var(--green)':l.status.includes('Reunião')?'var(--orange)':'var(--muted)'};font-weight:600;white-space:nowrap;">${l.status}</span></td>
        </tr>`).join('')}</tbody>
      </table></div>`;
    }

    function renderPerformanceTab(content) {
      const G = TEMPLATES[currentNiche].colors.primary;
      const upsell = LEADS.length > 200 ? `
        <div class="card" style="border-color:rgba(255,215,0,0.3);background:linear-gradient(135deg,var(--surface) 0%,rgba(255,215,0,0.04) 100%);margin-top:16px;">
          <div class="card-title" style="color:#FFD600;">🚀 Próximo Passo — Maximize seus Resultados</div>
          <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <div style="flex:1;min-width:200px;">
              <div style="font-size:13px;color:var(--white);margin-bottom:8px;">Você está processando <b style="color:#FFD600;">${LEADS.length} leads/mês</b>. Seu plano atual suporta até 300.</div>
              <div style="font-size:12px;color:var(--muted);">Com o plano <b style="color:#FFD600;">Enterprise</b> você tem leads ilimitados, PDFs automáticos e 3 corretores notificados simultaneamente.</div>
            </div>
            <div style="background:rgba(255,215,0,0.13);border:1px solid rgba(255,215,0,0.3);border-radius:10px;padding:14px 20px;text-align:center;min-width:140px;">
              <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">Upgrade para</div>
              <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#FFD600;">Enterprise</div>
              <div style="font-size:10px;color:var(--muted);margin-top:4px;">Fale com seu gerente</div>
            </div>
          </div>
        </div>` : '';

      content.innerHTML = `
      <div class="card" style="margin-bottom:16px;">
        <div class="card-title">Antes vs Depois da Automação</div>
        <div class="compare-grid">
          ${[{label:"Tempo de resposta",before:"3h 20min",after:"1m 47s"},{label:"Taxa de qualificação",before:"40%",after:"78%"},{label:"Taxa de conversão",before:"8%",after:"18.2%"},{label:"Horas manuais/semana",before:"28h",after:"4h"}].map(i=>`
          <div class="compare-box"><div class="compare-label">${i.label}</div><div class="compare-row">
            <div class="compare-item"><div class="compare-tag before">Antes</div><div class="compare-value before">${i.before}</div></div>
            <div class="compare-arrow">→</div>
            <div class="compare-item"><div class="compare-tag after">Depois</div><div class="compare-value after">${i.after}</div></div>
          </div></div>`).join('')}
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="card"><div class="card-title">ROI Estimado</div><div class="roi-box">
          <div class="roi-section"><div class="roi-label">Investimento mensal</div><div class="roi-big" style="font-size:22px;color:var(--red);">R$ 2.490</div></div>
          <div class="roi-math">÷</div>
          <div class="roi-section"><div class="roi-label">Receita adicional estimada</div><div class="roi-big" style="font-size:32px;color:${G};">R$ 168.000</div></div>
          <div class="roi-divider"></div>
          <div class="roi-section"><div class="roi-label">ROI do mês</div><div class="roi-big" style="font-size:48px;color:${G};">67x</div><div class="roi-small">Para cada R$ 1 investido, R$ 67 de retorno</div></div>
        </div></div>
        <div class="card"><div class="card-title">Horas Economizadas</div>
          ${[{label:"Qualificação manual",b:28,a:4,u:"h/sem"},{label:"Registro no CRM",b:6,a:0,u:"h/sem"},{label:"Follow-up manual",b:12,a:1,u:"h/sem"},{label:"Distribuição de leads",b:4,a:0,u:"h/sem"}].map(i=>`
          <div class="progress-item"><div class="progress-header"><span class="progress-label">${i.label}</span><span class="progress-value" style="color:${G};">-${i.b-i.a}${i.u}</span></div>
          <div class="progress-bar-bg"><div class="progress-bar" style="width:${(i.a/i.b)*100||2}%;background:${G};"></div></div></div>`).join('')}
          <div style="margin-top:16px;padding:14px;background:rgba(0,200,83,0.13);border:1px solid rgba(0,200,83,0.27);border-radius:10px;text-align:center;">
            <div style="font-size:11px;color:var(--muted);">Total economizado por semana</div>
            <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:${G};">41 horas</div>
            <div style="font-size:11px;color:var(--muted);">= 1 corretor extra sem contratar ninguém</div>
          </div>
        </div>
      </div>
      ${upsell}`;
    }

    // ── ADMIN RENDERING ───────────────────────────────────────────────────────────
    function renderAdminTab(tab) {
      const content = document.getElementById('adminContent');

      if (tab === 'overview') {
        const totalMRR = CLIENTS.reduce((s,c)=>s+c.mrr,0);
        const totalLeads = CLIENTS.reduce((s,c)=>s+c.leads,0);
        const avgHealth = Math.round(CLIENTS.reduce((s,c)=>s+c.health,0)/CLIENTS.length);

        // Clientes em risco
        const riskClients = CLIENTS.filter(c=>c.health<70);
        const riskReasons = {61:'Taxa de conversão caiu 40% este mês',58:'Sem leads qualificados nos últimos 7 dias',55:'Baixa taxa de resposta — 4m 12s (meta: 2min)'};
        const riskHtml = riskClients.length ? `
          <div class="card" style="margin-bottom:16px;border-color:rgba(255,152,0,0.3);background:linear-gradient(135deg,var(--surface) 0%,rgba(255,152,0,0.04) 100%);">
            <div class="card-title" style="color:var(--orange);">⚠️ Clientes em Risco de Churn</div>
            ${riskClients.map(c=>`<div style="padding:14px 0;border-bottom:1px solid var(--border);">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                <div class="client-avatar" style="background:${c.color}33;border:2px solid ${c.color};width:36px;height:36px;font-size:14px;">${c.niche==='Imobiliária'?'🏠':c.niche.includes('Estética')?'💆':'🏥'}</div>
                <div style="flex:1;"><div style="font-size:13px;font-weight:700;color:var(--white);">${c.name}</div>
                  <div style="font-size:11px;color:var(--muted);">Health: <span style="color:${c.health<60?'var(--red)':'var(--orange)'};">${c.health}%</span></div></div>
                <div style="text-align:right;">
                  <div style="font-size:10px;color:var(--orange);font-weight:700;">Risco ${c.health<60?'alto':'médio'}</div>
                  <div style="font-size:18px;font-weight:800;color:${c.health<60?'var(--red)':'var(--orange)'};">${c.health<60?'35%':'22%'}</div>
                </div>
              </div>
              <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">⚠️ ${riskReasons[c.health]||'Performance abaixo da média'}</div>
              <div style="font-size:11px;color:var(--green);">→ Ação: Agendar call de sucesso do cliente</div>
            </div>`).join('')}
          </div>` : '';

        // Previsões e Insights
        const p = totalMRR, fmt2=n=>n.toLocaleString('pt-BR');
        const forecastHtml = `
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
            <div class="card"><div class="card-title">🔮 Previsão Março 2026</div>
              ${[{l:'Pessimista',v:Math.round(p*0.9),c:'var(--red)',n:'1 churn provável',pct:'-10%'},{l:'Realista',v:Math.round(p*1.04),c:'var(--blue)',n:'crescimento orgânico',pct:'+4%'},{l:'Otimista',v:Math.round(p*1.2),c:'var(--green)',n:'2 novos clientes',pct:'+20%'}].map(s=>`
              <div style="padding:10px 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;">
                <div><div style="font-size:12px;font-weight:700;color:${s.c};">${s.l}</div><div style="font-size:11px;color:var(--muted);">${s.n}</div></div>
                <div style="text-align:right;"><div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:${s.c};">R$ ${fmt2(s.v)}</div><div style="font-size:10px;color:${s.c};">${s.pct} vs fev</div></div>
              </div>`).join('')}
            </div>
            <div class="card"><div class="card-title">💡 Insights</div>
              ${[{i:'🏠',t:'Clientes de Imobiliária têm 2x mais leads qualificados — foco de captação',tag:'Oportunidade',c:'var(--green)'},{i:'📈',t:'Clientes com health >80% têm churn zero — investir em success',tag:'Estratégia',c:'var(--blue)'},{i:'⚡',t:'Resposta <1min aumenta conversão em 35%',tag:'HOT',c:'var(--red)'},{i:'🔄',t:'3 clientes prontos para upsell',tag:'Upsell',c:'var(--yellow)'}].map(ins=>`
              <div style="padding:8px 0;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;gap:8px;">
                <span style="font-size:16px;">${ins.i}</span>
                <div style="flex:1;font-size:11px;color:var(--white);">${ins.t}</div>
                <span style="font-size:10px;color:${ins.c};font-weight:700;padding:2px 8px;border-radius:100px;background:${ins.c}22;white-space:nowrap;">${ins.tag}</span>
              </div>`).join('')}
            </div>
          </div>`;

        content.innerHTML = `
        <div class="kpi-grid">
          ${[{icon:'💰',label:'MRR Total',value:`R$ ${fmt(totalMRR)}`,sub:`${CLIENTS.length} clientes ativos`,color:'var(--green)',delta:22},{icon:'📨',label:'Leads processados',value:fmt(totalLeads),sub:'este mês',color:'var(--blue)',delta:31},{icon:'❤️',label:'Health médio',value:`${avgHealth}%`,sub:'satisfação dos clientes',color:'var(--pink)',delta:5},{icon:'📅',label:'ARR projetado',value:`R$ ${fmt(totalMRR*12)}`,sub:'anualizado',color:'var(--yellow)',delta:22}].map(k=>`
          <div class="kpi-card"><div class="kpi-glow" style="background:radial-gradient(circle,${k.color},transparent);"></div><div class="kpi-icon">${k.icon}</div><div class="kpi-label">${k.label}</div><div class="kpi-value" style="color:${k.color};">${k.value}</div><div class="kpi-sub">${k.sub}</div><div class="kpi-delta positive">↑ ${k.delta}% vs anterior</div></div>`).join('')}
        </div>
        ${riskHtml}
        ${forecastHtml}
        <div class="card"><div class="card-title">Status dos Clientes</div>
          ${CLIENTS.map(c=>`<div class="client-item" onclick="selectClient(${c.id})">
            <div class="client-avatar" style="background:${c.color}33;border:2px solid ${c.color};">${c.niche==='Imobiliária'?'🏠':c.niche.includes('Estética')?'💆':'🏥'}</div>
            <div class="client-info"><div class="client-name">${c.name}</div><div class="client-meta">${c.niche} · ${c.plan} · desde ${c.since}</div></div>
            <div class="client-mrr"><div class="mrr-value" style="color:${c.color};">R$ ${fmt(c.mrr)}</div><div class="mrr-label">/mês</div></div>
            <div class="client-health"><div class="health-header"><span class="health-label">Health</span><span class="health-value" style="color:${c.health>=80?'var(--green)':c.health>=60?'var(--orange)':'var(--red)'};">${c.health}%</span></div>
              <div class="health-bar-bg"><div class="health-bar" style="width:${c.health}%;background:${c.health>=80?'var(--green)':c.health>=60?'var(--orange)':'var(--red)'};"></div></div></div>
            <span style="font-size:11px;padding:3px 10px;border-radius:100px;background:${c.status==='active'?'rgba(0,200,83,0.13)':'rgba(255,152,0,0.13)'};color:${c.status==='active'?'var(--green)':'var(--orange)'};font-weight:700;">${c.status==='active'?'● Ativo':'⚠️ Atenção'}</span>
          </div>`).join('')}
        </div>`;

      } else if (tab === 'clients') {
        renderClientsTab(content);
      } else if (tab === 'templates') {
        renderTemplatesTab(content);
      } else if (tab === 'billing') {
        renderBillingTab(content);
      }
    }
"""

# Encontra o trecho a substituir: de "// ── CLIENT RENDERING" até "// ── ADMIN RENDERING"
# (o bloco completo que foi corrompido)
pattern = r'(// ── CLIENT RENDERING\s*─+\s*)(.*?)(// ── INTERACTIVITY)'
match = re.search(pattern, content, re.DOTALL)

if match:
    print(f"Encontrou bloco JS nas posições {match.start()}-{match.end()}")
    new_content = content[:match.start()] + NEW_JS + "\n    " + content[match.start(3):]
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Arquivo reconstruído com sucesso!")
    print(f"   Tamanho: {len(new_content)} bytes")
else:
    # Tenta encontrar as marcações individualmente
    idx_client = content.find('CLIENT RENDERING')
    idx_interact = content.find('INTERACTIVITY')
    print(f"CLIENT RENDERING em: {idx_client}")
    print(f"INTERACTIVITY em: {idx_interact}")
    if idx_client > 0 and idx_interact > 0:
        # Encontra o início da linha do CLIENT RENDERING
        start = content.rfind('\n', 0, idx_client - 10) + 1
        # Encontra o início da linha do INTERACTIVITY
        end = content.rfind('\n', 0, idx_interact - 10) + 1
        print(f"Substituindo de char {start} a {end}")
        new_content = content[:start] + NEW_JS + "\n" + content[end:]
        with open(FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Arquivo reconstruído com sucesso (método alternativo)!")
    else:
        print("❌ Não encontrou os marcadores. Verifique o arquivo.")
        sys.exit(1)
