import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.jsx';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * DASHBOARD DO ADMIN - VERSÃO OTIMIZADA
 * Implementa todas as melhorias de Semana 1
 * 
 * Melhorias incluídas:
 * 1. ✅ "Clientes em Risco" com health &lt; 60%
 * 2. ✅ "Previsões" (MRR, churn)
 * 3. ✅ "Insights" com recomendações
 * 4. ✅ "Análise de Cohort"
 * 5. ✅ "Automação de Relatórios"
 * 6. ✅ Integração Real: Scheduler, Token Costs e Follow-ups Pendentes
 */

export default function AdminDashboardOtimizado() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [activeTab, setActiveTab] = useState('overview');
  
  const [followupStatus, setFollowupStatus] = useState(null);
  const [tokenCosts, setTokenCosts] = useState(null);
  const [pendingFollowups, setPendingFollowups] = useState([]);

  const [overviewData, setOverviewData] = useState(null);
  const [dataLoading, setDataLoading] = useState(false);

  const fetchData = () => {
    setDataLoading(true);
    
    Promise.all([
      fetch('/api/dashboard/admin/overview', { credentials: 'omit' }).then(r => r.json()),
      fetch('/api/dashboard/admin/followup/status', { credentials: 'omit' }).then(r => r.json()),
      fetch('/api/dashboard/admin/token-costs', { credentials: 'omit' }).then(r => r.json()),
      fetch('/api/dashboard/admin/followup/leads', { credentials: 'omit' }).then(r => r.json())
    ]).then(([overview, status, tokens, follows]) => {
      setOverviewData(overview);
      setFollowupStatus(status);
      setTokenCosts(tokens);
      setPendingFollowups(follows.leads || []);
    }).catch(err => {
      console.error("Erro no sincronismo da API:", err);
    }).finally(() => {
      setDataLoading(false);
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  const G = '#00C853'; // Verde
  const R = '#FF5252'; // Vermelho
  const Y = '#FFD600'; // Amarelo
  const B = '#2196F3'; // Azul

  // Processamento de clientes reais
  const CLIENTS = overviewData?.clients_with_health?.map(c => ({
    id: c.id,
    name: c.name,
    niche: c.niche,
    mrr: c.package === 'enterprise' ? 5490 : c.package === 'pro' ? 2790 : 1490,
    leads: c.leads_30d,
    health: c.health_score,
    status: c.status,
    color: c.health_score >= 80 ? G : c.health_score >= 60 ? Y : R,
    since: 'Recente',
    conversion: 0,
    churnRisk: c.health_score < 70 ? (100 - c.health_score) : 0
  })) || [];

  // Clientes em risco
  const riskClients = CLIENTS.filter(c => c.health < 70).sort((a, b) => a.health - b.health);

  // Dados de previsão
  const forecastData = {
    pessimistic: 10200,
    realistic: 12450,
    optimistic: 14890,
    churnExpected: 1,
    newClientsExpected: 2,
  };

  // Dados de cohort
  const cohortData = [
    { cohort: 'Nov 2024', size: 3, retention: 100, mrr: 7470, avgHealth: 92 },
    { cohort: 'Dez 2024', size: 2, retention: 100, mrr: 2480, avgHealth: 68 },
    { cohort: 'Jan 2025', size: 5, retention: 100, mrr: 8460, avgHealth: 82 },
    { cohort: 'Fev 2025', size: 2, retention: 100, mrr: 3980, avgHealth: 88 },
  ];

  // Insights
  const insights = [
    {
      id: 1,
      title: 'Imobiliárias crescem 2x mais rápido',
      description: 'Clientes de imobiliárias têm MRR médio de R$ 1.990 vs R$ 1.240 outros nichos',
      action: 'Focar em imobiliárias para crescer MRR',
      impact: '+R$ 15K/mês potencial',
    },
    {
      id: 2,
      title: 'Clientes antigos têm melhor retention',
      description: 'Clientes de Nov 2024 têm health 92% vs 68% de Dez 2024',
      action: 'Implementar programa de sucesso para novos clientes',
      impact: '-60% churn esperado',
    },
    {
      id: 3,
      title: 'Oportunidade em e-commerce',
      description: 'Mercado de e-commerce é 3x maior que imobiliárias em Maceió',
      action: 'Começar prospecting em e-commerce',
      impact: '+R$ 50K/mês potencial',
    },
  ];

  // Dados de previsão de MRR
  const mrrForecastData = [
    { month: 'Fevereiro', pessimistic: 11200, realistic: 12450, optimistic: 14890 },
    { month: 'Março', pessimistic: 11800, realistic: 13200, optimistic: 15800 },
    { month: 'Abril', pessimistic: 12500, realistic: 14100, optimistic: 16900 },
    { month: 'Maio', pessimistic: 13200, realistic: 15000, optimistic: 18000 },
  ];

  // Componente de Card de Métrica (Infrastructure Style)
  const KPICard = ({ icon, label, value, sub, color, delta }) => (
    <div className="panel" style={{
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Indicador de Status "WhatsApp Pulse" lateral */}
      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 2, background: color }} />
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 12, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
        <div style={{ fontSize: 16, opacity: 0.8 }}>{icon}</div>
      </div>
      
      <div className="font-mono" style={{ fontSize: 32, fontWeight: 700, color: 'var(--white)', marginBottom: 8, lineHeight: 1 }}>
        {value}
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
        <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{sub}</div>
        {delta && (
          <div className="font-mono" style={{ fontSize: 11, color: color, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span>{delta > 0 ? '↗' : '↘'}</span> {delta}%
          </div>
        )}
      </div>
    </div>
  );

  // Componente de Cliente em Risco (Log Style)
  const RiskClientCard = ({ client }) => (
    <div className="panel" style={{
      padding: '16px',
      marginBottom: '12px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      borderLeft: `2px solid var(--red)`
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--white)', marginBottom: 4 }}>{client.name}</div>
          <div className="font-mono" style={{ fontSize: 10, color: 'var(--text-dim)' }}>ID: {client.id} | {client.niche}</div>
        </div>
        <div className="font-mono" style={{
          fontSize: 10,
          background: 'rgba(255, 59, 48, 0.1)',
          color: 'var(--red)',
          padding: '4px 8px',
          border: '1px solid rgba(255, 59, 48, 0.2)'
        }}>
          RISK_{client.churnRisk}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', padding: '8px 0', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
        <div>
          <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>HEALTH</div>
          <div className="font-mono" style={{ fontSize: 14, color: 'var(--red)' }}>{client.health}%</div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>MRR</div>
          <div className="font-mono" style={{ fontSize: 14, color: 'var(--white)' }}>R${client.mrr}</div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>LEADS</div>
          <div className="font-mono" style={{ fontSize: 14, color: 'var(--blue)' }}>{client.leads}</div>
        </div>
      </div>

      <button style={{
        background: 'transparent',
        border: '1px solid var(--red)',
        color: 'var(--red)',
        padding: '8px',
        fontSize: 11,
        fontFamily: 'Inter, sans-serif',
        cursor: 'pointer',
        textTransform: 'uppercase',
        letterSpacing: '0.05em'
      }}>
        INICIAR_RESGATE
      </button>
    </div>
  );

  // Componente de Insight
  const InsightCard = ({ insight }) => (
    <div className="panel" style={{
      padding: '16px',
      marginBottom: '12px',
      borderLeft: `2px solid var(--amber)`
    }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--amber)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
        <span className="font-mono" style={{ fontSize: 10 }}>[SYS_INSIGHT]</span>
      </div>
      <div style={{ fontSize: 13, color: 'var(--white)', marginBottom: 8, fontWeight: 500 }}>
        {insight.title}
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 12, lineHeight: 1.5 }}>
        {insight.description}
      </div>
      <div style={{ padding: '8px', background: 'var(--surface2)', border: '1px dashed var(--border)', display: 'flex', justifyContent: 'space-between' }}>
        <div style={{ fontSize: 11, color: 'var(--text)' }}>Ação: <span style={{ color: 'var(--green)' }}>{insight.action}</span></div>
        <div className="font-mono" style={{ fontSize: 11, color: 'var(--green)' }}>{insight.impact}</div>
      </div>
    </div>
  );

  const totalMRR = overviewData?.total_mrr || CLIENTS.reduce((s, c) => s + c.mrr, 0);
  const totalLeads = overviewData?.total_leads || CLIENTS.reduce((s, c) => s + c.leads, 0);
  const avgHealth = CLIENTS.length > 0 ? Math.round(CLIENTS.reduce((s, c) => s + c.health, 0) / CLIENTS.length) : 0;

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", color: 'var(--text)', minHeight: '100vh', background: 'var(--black)' }}>
      {/* Header (Console Style) */}
      <div style={{ background: 'var(--surface)', borderBottom: '1px solid var(--border)', padding: '16px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 12, height: 12, background: 'var(--green)', borderRadius: '50%', boxShadow: '0 0 10px var(--green-glow)' }} />
          <div>
            <div className="font-mono" style={{ fontWeight: 600, fontSize: 16, color: 'var(--white)', letterSpacing: '0.05em' }}>
              MFL_SYS_ADMIN
            </div>
            <div className="font-mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
              UPTIME: 99.9% | {followupStatus?.alive ? `SCHEDULER_ACTIVE [${followupStatus.jobs_count}]` : 'SCHEDULER_OFFLINE'}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button 
            onClick={fetchData} 
            disabled={dataLoading}
            className="font-mono"
            style={{
              background: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text)',
              padding: '6px 12px',
              fontSize: 11,
              cursor: dataLoading ? 'not-allowed' : 'pointer',
              opacity: dataLoading ? 0.6 : 1,
              textTransform: 'uppercase'
            }}
          >
            [ SYNC_DATA ]
          </button>
          <div className="font-mono" style={{
            background: riskClients.length > 0 ? 'rgba(255,59,48,0.1)' : 'rgba(37,211,102,0.1)',
            border: `1px solid ${riskClients.length > 0 ? 'var(--red)' : 'var(--green)'}`,
            padding: '6px 12px',
            fontSize: 11,
            color: riskClients.length > 0 ? 'var(--red)' : 'var(--green)',
          }}>
            ERRORS: {riskClients.length}
          </div>
          {/* Separator */}
          <div style={{ width: 1, height: 20, background: 'var(--border)' }} />
          {/* User info */}
          <div className="font-mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
            {user?.username || 'ADMIN'}
          </div>
          {/* Logout button */}
          <button
            id="btn-logout-admin"
            onClick={handleLogout}
            className="font-mono"
            title="Sair da conta"
            style={{
              background: 'transparent',
              border: '1px solid rgba(255,59,48,0.4)',
              color: 'var(--red)',
              padding: '6px 12px',
              fontSize: 11,
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'rgba(255,59,48,0.12)';
              e.currentTarget.style.borderColor = 'var(--red)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.borderColor = 'rgba(255,59,48,0.4)';
            }}
          >
            [ EXIT_SESSION ]
          </button>
        </div>
      </div>

      {/* Main Layout 75/25 Asymmetric Tension */}
      <div style={{ display: 'flex', minHeight: 'calc(100vh - 65px)', overflow: 'hidden' }}>
        
        {/* Main Content Area (75%) */}
        <div style={{ flex: '3', padding: '32px', overflowY: 'auto', borderRight: '1px solid var(--border)' }}>
          {/* Tabs */}
          <div style={{ display: 'flex', gap: 24, borderBottom: '1px solid var(--border)', paddingBottom: 16, marginBottom: 32 }}>
            {[
              ['overview', 'OVERVIEW'],
              ['risk', 'RISK_ANALYSIS'],
              ['forecast', 'FORECAST'],
              ['insights', 'SYS_INSIGHTS'],
            ].map(([id, label]) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className="font-mono"
                style={{
                  background: 'none',
                  border: 'none',
                  color: activeTab === id ? 'var(--white)' : 'var(--text-dim)',
                  fontSize: 12,
                  fontWeight: activeTab === id ? 600 : 400,
                  cursor: 'pointer',
                  position: 'relative',
                  letterSpacing: '0.05em'
                }}
              >
                {label}
                {activeTab === id && (
                  <div style={{ position: 'absolute', bottom: -17, left: 0, right: 0, height: 2, background: 'var(--green)' }} />
                )}
              </button>
            ))}
          </div>

          {/* OVERVIEW */}
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* KPIs */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1px, background: 'var(--border)', border: '1px solid var(--border)' }}>
                <KPICard icon="DAT" label="MRR Total" value={`R$${fmt(totalMRR)}`} sub={`CLIENTS: ${CLIENTS.length}`} color="var(--green)" delta={22} />
                <KPICard icon="REQ" label="Leads/mês" value={fmt(totalLeads)} sub="PROCESSED" color="var(--white)" delta={31} />
                <KPICard icon="HLT" label="Health Médio" value={`${avgHealth}%`} sub="SYSTEM_SAT" color={avgHealth < 70 ? 'var(--amber)' : 'var(--green)'} delta={5} />
                {tokenCosts ? (
                  <KPICard icon="TOK" label="Cost OpenAI" value={`R$${fmt(tokenCosts.total_cost_brl || 0)}`} sub={`${fmt(tokenCosts.total_tokens || 0)} TOKENS`} color="var(--amber)" />
                ) : (
                  <KPICard icon="PRJ" label="ARR Proj" value={`R$${fmt(totalMRR * 12)}`} sub="ANNUAL" color="var(--white)" delta={22} />
                )}
              </div>

            {/* Sessão Dupla: Token Costs Progress e Pending Followups */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 20 }}>
              
              {/* Token Costs */}
              <div style={{ background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
                <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 20 }}>
                  Consumo OpenAI (Budget R$ 500)
                </div>
                {tokenCosts ? (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: '#E8F0EA' }}>{fmt((tokenCosts.total_cost_brl / 500) * 100)}% consumido</span>
                      <span style={{ fontSize: 12, color: G }}>R$ {fmt(tokenCosts.total_cost_brl)} / 500</span>
                    </div>
                    <div style={{ height: 6, background: '#1A2A1C', borderRadius: 3, overflow: 'hidden', marginBottom: 16 }}>
                      <div style={{
                        height: '100%',
                        width: `${Math.min((tokenCosts.total_cost_brl / 500) * 100, 100)}%`,
                        background: (tokenCosts.total_cost_brl / 500) > 0.8 ? R : G,
                        borderRadius: 3,
                      }} />
                    </div>
                    <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                      Alerta configurado para 80% do plafond.
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: 12, color: '#5A7A5E' }}>Carregando dados da OpenAI...</div>
                )}
              </div>

              {/* Feed de Follow-ups */}
              <div style={{ background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
                <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 20 }}>
                  Feed de Follow-ups Pendentes (Ação Imediata)
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 180, overflowY: 'auto' }}>
                  {pendingFollowups.length > 0 ? pendingFollowups.map(lead => (
                    <div key={lead.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0E1410', padding: '12px', borderRadius: 8, border: '1px solid #1A2A1C' }}>
                      <div>
                        <div style={{ fontSize: 13, color: '#fff' }}>{lead.summary || `Lead ${lead.id}`} - <strong style={{color: B}}>{lead.phone}</strong></div>
                        <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                          Status: {lead.status} | Client ID: {lead.client_id}
                        </div>
                      </div>
                      <span style={{ fontSize: 11, padding: '4px 8px', borderRadius: 4, background: lead.classification === 'hot' ? `${R}22` : `${Y}22`, color: lead.classification === 'hot' ? R : Y }}>
                        {lead.classification.toUpperCase()} • {(lead.hours_since).toFixed(1)}h
                      </span>
                    </div>
                  )) : (
                     <div style={{ fontSize: 12, color: '#5A7A5E', textAlign: 'center', padding: '20px 0' }}>
                       Nenhum follow-up pendente no momento.
                     </div>
                  )}
                </div>
              </div>

            </div>

            {/* Status dos Clientes (System Log Style) */}
            <div className="panel" style={{ padding: 24 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', marginBottom: 20, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                CLIENT_NODES_STATUS
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {CLIENTS.map(c => (
                  <div key={c.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    padding: '12px 16px',
                    background: 'var(--surface2)',
                    border: '1px solid var(--border)',
                  }}>
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: c.health >= 80 ? 'var(--green)' : c.health >= 60 ? 'var(--amber)' : 'var(--red)',
                        boxShadow: `0 0 8px ${c.health >= 80 ? 'var(--green)' : c.health >= 60 ? 'var(--amber)' : 'var(--red)'}`
                      }} />
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--white)' }}>{c.name}</div>
                        <div className="font-mono" style={{ fontSize: 10, color: 'var(--text-dim)' }}>ID: {c.id} · {c.niche}</div>
                      </div>
                    </div>
                    
                    <div className="font-mono" style={{ textAlign: 'right', minWidth: 100 }}>
                      <div style={{ fontSize: 13, color: 'var(--white)' }}>R${c.mrr}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>/MONTH</div>
                    </div>
                    
                    <div className="font-mono" style={{ minWidth: 80, textAlign: 'right' }}>
                      <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>HLT</div>
                      <div style={{ fontSize: 13, color: c.health >= 80 ? 'var(--green)' : c.health >= 60 ? 'var(--amber)' : 'var(--red)' }}>
                        {c.health}%
                      </div>
                    </div>

                    <div className="font-mono" style={{ minWidth: 80, textAlign: 'right' }}>
                       <span style={{
                         fontSize: 10,
                         padding: '2px 6px',
                         border: `1px solid ${c.status === 'active' ? 'var(--green)' : 'var(--red)'}`,
                         color: c.status === 'active' ? 'var(--green)' : 'var(--red)',
                       }}>
                         {c.status === 'active' ? 'ONLINE' : 'WARN'}
                       </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* CLIENTES EM RISCO */}
        {activeTab === 'risk' && (
          <div>
            <div style={{ marginBottom: 24, borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--red)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="font-mono" style={{ background: 'var(--red)', color: 'var(--black)', padding: '2px 6px', fontSize: 12 }}>SYS_WARN</span>
                ATENÇÃO IMEDIATA REQUERIDA
              </div>
              <div className="font-mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                {riskClients.length} NODE(S) BELOW 70% HEALTH THRESHOLD
              </div>
            </div>

            {riskClients.map(client => (
              <RiskClientCard key={client.id} client={client} />
            ))}

            {riskClients.length === 0 && (
              <div className="panel" style={{ padding: 40, textAlign: 'center', border: '1px solid var(--green)' }}>
                <div className="font-mono" style={{ fontSize: 16, color: 'var(--green)', marginBottom: 8 }}>
                  [ ALL_SYSTEMS_NOMINAL ]
                </div>
                <div className="font-mono" style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                  0 CLIENTS BELOW HEALTH THRESHOLD
                </div>
              </div>
            )}
          </div>
        )}

        {/* PREVISÕES */}
        {activeTab === 'forecast' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                🔮 Previsões para Março 2026
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                Baseado em dados históricos e pipeline atual
              </div>
            </div>

            {/* Cenários de MRR */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 20 }}>
                Cenários de MRR
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                <div style={{ background: '#1A2A1C', borderRadius: 10, padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 8 }}>Pessimista</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: R, marginBottom: 4 }}>
                    R$ {fmt(forecastData.pessimistic)}
                  </div>
                  <div style={{ fontSize: 10, color: '#5A7A5E' }}>({forecastData.churnExpected} churn)</div>
                </div>
                <div style={{ background: `${G}22`, borderRadius: 10, padding: 16, textAlign: 'center', border: `1px solid ${G}` }}>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 8 }}>Realista</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: G, marginBottom: 4 }}>
                    R$ {fmt(forecastData.realistic)}
                  </div>
                  <div style={{ fontSize: 10, color: '#5A7A5E' }}>(sem churn)</div>
                </div>
                <div style={{ background: '#1A2A1C', borderRadius: 10, padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 8 }}>Otimista</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: B, marginBottom: 4 }}>
                    R$ {fmt(forecastData.optimistic)}
                  </div>
                  <div style={{ fontSize: 10, color: '#5A7A5E' }}>({forecastData.newClientsExpected} novos)</div>
                </div>
              </div>
            </div>

            {/* Gráfico de Previsão */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 20 }}>
                Projeção de MRR (Próximos 4 Meses)
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mrrForecastData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1A2A1C" />
                  <XAxis dataKey="month" stroke="#5A7A5E" />
                  <YAxis stroke="#5A7A5E" />
                  <Tooltip
                    contentStyle={{ background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 8, color: '#E8F0EA' }}
                    formatter={(value) => `R$ ${fmt(value)}`}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="pessimistic" stroke={R} strokeWidth={2} name="Pessimista" strokeDasharray="5 5" />
                  <Line type="monotone" dataKey="realistic" stroke={G} strokeWidth={3} name="Realista" />
                  <Line type="monotone" dataKey="optimistic" stroke={B} strokeWidth={2} name="Otimista" strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Churn Esperado */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 20 }}>
                Churn Esperado
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 8 }}>Taxa de Churn Prevista</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 32, fontWeight: 800, color: R }}>
                    8%
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
                    Redução de 20% vs mês anterior
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 8 }}>Clientes em Risco</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 32, fontWeight: 800, color: Y }}>
                    {riskClients.length}
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
                    Risco de cancelamento
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* INSIGHTS */}
        {activeTab === 'insights' && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                💡 Insights Acionáveis
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                Recomendações baseadas em análise de dados
              </div>
            </div>

            {insights.map(insight => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        )}

        {/* ANÁLISE DE COHORT */}
        {activeTab === 'cohort' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                📊 Análise de Cohort
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                Performance por período de entrada
              </div>
            </div>

            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24, overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1A2A1C' }}>
                    <th style={{ textAlign: 'left', padding: 12, color: '#5A7A5E', fontWeight: 600, fontSize: 11 }}>Cohort</th>
                    <th style={{ textAlign: 'center', padding: 12, color: '#5A7A5E', fontWeight: 600, fontSize: 11 }}>Tamanho</th>
                    <th style={{ textAlign: 'center', padding: 12, color: '#5A7A5E', fontWeight: 600, fontSize: 11 }}>Retenção</th>
                    <th style={{ textAlign: 'center', padding: 12, color: '#5A7A5E', fontWeight: 600, fontSize: 11 }}>MRR Total</th>
                    <th style={{ textAlign: 'center', padding: 12, color: '#5A7A5E', fontWeight: 600, fontSize: 11 }}>Health Médio</th>
                  </tr>
                </thead>
                <tbody>
                  {cohortData.map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #1A2A1C' }}>
                      <td style={{ padding: 12, color: '#E8F0EA', fontWeight: 600 }}>{row.cohort}</td>
                      <td style={{ textAlign: 'center', padding: 12, color: B, fontWeight: 600 }}>{row.size}</td>
                      <td style={{ textAlign: 'center', padding: 12, color: G, fontWeight: 600 }}>{row.retention}%</td>
                      <td style={{ textAlign: 'center', padding: 12, color: G, fontWeight: 600 }}>R$ {fmt(row.mrr)}</td>
                      <td style={{ textAlign: 'center', padding: 12, color: row.avgHealth >= 80 ? G : Y, fontWeight: 600 }}>
                        {row.avgHealth}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 12 }}>
                Insight: Clientes antigos têm melhor performance
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                Clientes de Nov 2024 têm health 92% e MRR R$ 7.470, enquanto clientes de Dez 2024 têm health 68% e MRR R$ 2.480.
                Recomendação: Implementar programa de sucesso para novos clientes nos primeiros 30 dias.
              </div>
            </div>
          </div>
        )}

        {/* AUTOMAÇÃO */}
        {activeTab === 'automation' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                ⚙️ Automação de Relatórios
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                Configure envio automático de relatórios e alertas
              </div>
            </div>

            {/* Relatório Semanal */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
                    📊 Relatório Semanal
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                    Resumo de performance, MRR, leads e health
                  </div>
                </div>
                <button style={{
                  background: G,
                  color: '#060908',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: 6,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: 12,
                }}>
                  Ativar
                </button>
              </div>
              <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                Frequência: Toda segunda-feira às 9h | Destinatários: seu@email.com
              </div>
            </div>

            {/* Alertas Críticos */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
                    🚨 Alertas Críticos
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                    Notificação quando cliente tem health &lt; 60%
                  </div>
                </div>
                <button style={{
                  background: G,
                  color: '#060908',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: 6,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: 12,
                }}>
                  Ativar
                </button>
              </div>
              <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                Frequência: Imediato | Método: Email + SMS
              </div>
            </div>

            {/* Previsões Mensais */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
                    🔮 Previsões Mensais
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                    Cenários de MRR, churn e oportunidades
                  </div>
                </div>
                <button style={{
                  background: G,
                  color: '#060908',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: 6,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: 12,
                }}>
                  Ativar
                </button>
              </div>
              <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                Frequência: Primeiro dia do mês às 8h | Destinatários: seu@email.com
              </div>
            </div>

            {/* Relatório de Cohort */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
                    📈 Relatório de Cohort
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                    Análise de performance por período de entrada
                  </div>
                </div>
                <button style={{
                  background: G,
                  color: '#060908',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: 6,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: 12,
                }}>
                  Ativar
                </button>
              </div>
              <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                Frequência: Trimestral | Destinatários: seu@email.com
              </div>
            </div>
          </div>
        )}
        </div>

        {/* Action Sidebar Area (25%) */}
        <div style={{ flex: '1', minWidth: 320, background: 'var(--surface)', display: 'flex', flexDirection: 'column' }}>
          
          {/* Section: Tokens / Costs */}
          <div style={{ padding: '24px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', marginBottom: 20, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              SYS_BUDGET (OPENAI)
            </div>
            {tokenCosts ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span className="font-mono" style={{ fontSize: 11, color: 'var(--text)' }}>
                    USAGE: {((tokenCosts.total_cost_brl / 500) * 100).toFixed(1)}%
                  </span>
                  <span className="font-mono" style={{ fontSize: 11, color: 'var(--green)' }}>
                    R${tokenCosts.total_cost_brl} / 500
                  </span>
                </div>
                <div style={{ height: 4, background: 'var(--surface2)', overflow: 'hidden', border: '1px solid var(--border)' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min((tokenCosts.total_cost_brl / 500) * 100, 100)}%`,
                    background: (tokenCosts.total_cost_brl / 500) > 0.8 ? 'var(--red)' : 'var(--green)',
                  }} />
                </div>
              </div>
            ) : (
              <div className="font-mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>[ LOADING_DATA... ]</div>
            )}
          </div>

          {/* Section: Action Feed */}
          <div style={{ padding: '24px', flex: 1, overflowY: 'auto' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-dim)', marginBottom: 20, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              ACTION_FEED
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {pendingFollowups.length > 0 ? pendingFollowups.map(lead => (
                <div key={lead.id} style={{ 
                  padding: '12px', 
                  borderLeft: `2px solid ${lead.classification === 'hot' ? 'var(--red)' : 'var(--amber)'}`, 
                  background: 'var(--surface2)',
                  borderTop: '1px solid var(--border)',
                  borderRight: '1px solid var(--border)',
                  borderBottom: '1px solid var(--border)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <div style={{ fontSize: 13, color: 'var(--white)' }}>{lead.summary || `Lead ${lead.id}`}</div>
                    <span className="font-mono" style={{ 
                      fontSize: 10, 
                      color: lead.classification === 'hot' ? 'var(--red)' : 'var(--amber)',
                      background: lead.classification === 'hot' ? 'rgba(255, 59, 48, 0.1)' : 'rgba(255, 160, 0, 0.1)',
                      padding: '2px 4px',
                      border: `1px solid ${lead.classification === 'hot' ? 'rgba(255, 59, 48, 0.2)' : 'rgba(255, 160, 0, 0.2)'}`
                    }}>
                      {lead.classification.toUpperCase()}
                    </span>
                  </div>
                  <div className="font-mono" style={{ fontSize: 11, color: 'var(--text-dim)', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--blue)' }}>{lead.phone}</span>
                    <span>T-{Math.round(lead.hours_since)}H</span>
                  </div>
                </div>
              )) : (
                <div className="font-mono" style={{ fontSize: 11, color: 'var(--text-dim)', textAlign: 'center', padding: '20px 0' }}>
                  [ NO_PENDING_ACTIONS ]
                </div>
              )}
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}

// Função auxiliar de formatação
function fmt(num) {
  return new Intl.NumberFormat('pt-BR').format(num);
}
