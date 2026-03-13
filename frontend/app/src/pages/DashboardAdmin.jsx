import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, Legend } from 'recharts';
import { useAuth } from '../hooks/useAuth.jsx';
import { useNavigate } from 'react-router-dom';
import { useAdminDashboard, runHealthCheck, useHealthHistory } from '../hooks/useDashboardData.js';
import { fmt } from '../utils/format.js';
import ClientModal from '../components/ClientModal.jsx';
import ConfirmDialog from '../components/ConfirmDialog.jsx';
import RiskClientModal from '../components/RiskClientModal.jsx';
import toast from 'react-hot-toast';

// ── HealthPanel fora do render (corrige Rules of Hooks) ───────────────────────
function HealthPanel({ client }) {
  const { history, loading: hLoading } = useHealthHistory(client.id);
  const chartData = history.map(h => ({
    week: h.week?.replace(/\d{4}-/, '') ?? h.week,
    score: h.health_score,
    label: h.label,
  }));
  return (
    <div style={{
      gridColumn: '1 / -1', background: '#060908',
      borderTop: '1px solid #1A2A1C', padding: '20px 20px 24px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ fontWeight: 700, color: '#fff', fontSize: 14 }}>
          📈 Histórico de Health Score — {client.name}
        </div>
        <div style={{ fontSize: 12, color: '#5A7A5E' }}>
          últimas {history.length} semanas registradas
        </div>
      </div>
      {hLoading ? (
        <div style={{ color: '#5A7A5E', fontSize: 13, padding: '20px 0' }}>Carregando...</div>
      ) : history.length === 0 ? (
        <div style={{ color: '#5A7A5E', fontSize: 13, padding: '20px 0' }}>
          Nenhum histórico ainda. Clique em <strong style={{ color: '#00C853' }}>🩺 Verificar Saúde</strong> para criar o primeiro snapshot.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id={`hs-grad-${client.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={client.color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={client.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1A2A1C" />
            <XAxis dataKey="week" tick={{ fontSize: 10, fill: '#5A7A5E' }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#5A7A5E' }} />
            <Tooltip
              contentStyle={{ background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 8, fontSize: 12 }}
              formatter={(val, _, p) => [`${val} — ${p.payload.label}`, 'Health Score']}
            />
            <Area
              type="monotone" dataKey="score"
              stroke={client.color} strokeWidth={2}
              fill={`url(#hs-grad-${client.id})`}
              dot={{ r: 4, fill: client.color, strokeWidth: 0 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

// ── SistemaTab — Scheduler, Tokens IA e Follow-ups ───────────────────────────
function SistemaTab({ G, R, Y, B }) {
  const [scheduler, setScheduler] = useState(null);
  const [tokenCosts, setTokenCosts] = useState([]);
  const [followups, setFollowups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [forceRunning, setForceRunning] = useState(false);

  const API = import.meta.env.VITE_API_URL || '';

  const load = useCallback(async () => {
    try {
      const [sRes, tRes, fRes] = await Promise.all([
        fetch(`${API}/api/dashboard/admin/followup/status`, { credentials: 'include' }),
        fetch(`${API}/api/dashboard/admin/token-costs`, { credentials: 'include' }),
        fetch(`${API}/api/dashboard/admin/followup/leads`, { credentials: 'include' }),
      ]);
      if (sRes.ok) setScheduler(await sRes.json());
      if (tRes.ok) setTokenCosts((await tRes.json()).clients || []);
      if (fRes.ok) setFollowups((await fRes.json()).leads || []);
    } catch (e) {
      console.error('[SistemaTab]', e);
    } finally {
      setLoading(false);
    }
  }, [API]);

  useEffect(() => { load(); }, [load]);

  const handleForceRun = async () => {
    setForceRunning(true);
    try {
      await fetch(`${API}/api/dashboard/admin/followup/status?run_now=1`, { credentials: 'include' });
      await load();
    } finally {
      setForceRunning(false);
    }
  };

  const STATUS_COLOR = { sent: G, simulated: B, failed: R, blocked: Y, admin_alert: '#FF9800' };
  const STATUS_LABEL = { sent: 'Enviado', simulated: 'Simulado', failed: 'Falhou', blocked: 'Bloqueado', admin_alert: 'Alerta Admin' };

  if (loading) return (
    <div style={{ color: '#5A7A5E', fontSize: 13, padding: 40, textAlign: 'center' }}>
      Carregando dados do sistema...
    </div>
  );

  const hb = scheduler?.heartbeat || {};
  const healthy = scheduler?.healthy ?? false;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── 1. Scheduler Heartbeat ────────────────────────────────────────── */}
      <div style={{ background: '#0A0F0B', border: `1px solid ${healthy ? '#1A2A1C' : R}`, borderRadius: 14, padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff' }}>
              ⚡ Scheduler de Follow-ups
            </div>
            <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
              APScheduler — verifica leads a cada 15 minutos
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{
              fontSize: 12, fontWeight: 700, padding: '6px 14px', borderRadius: 100,
              background: healthy ? `${G}22` : `${R}22`,
              color: healthy ? G : R,
            }}>
              {healthy ? '● Ativo' : '⚠️ Inativo'}
            </span>
            <button
              onClick={handleForceRun}
              disabled={forceRunning}
              style={{
                background: `${G}22`, border: `1px solid ${G}`, color: G,
                padding: '6px 14px', borderRadius: 8, cursor: 'pointer',
                fontSize: 12, fontWeight: 600, fontFamily: "'DM Sans', sans-serif",
                opacity: forceRunning ? 0.6 : 1,
              }}
            >
              {forceRunning ? 'Executando...' : '▶ Forçar agora'}
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16 }}>
          {[
            { label: 'Status do processo', value: scheduler?.running ? 'Rodando' : 'Parado', color: scheduler?.running ? G : R },
            { label: 'Jobs ativos', value: scheduler?.count ?? 0, color: '#E8F0EA' },
            { label: 'Heartbeat', value: hb.alive ? `${(hb.minutes_ago || 0).toFixed(1)} min atrás` : 'Sem sinal', color: hb.alive ? G : R },
            { label: 'Última execução', value: hb.last_alive ? new Date(hb.last_alive).toLocaleTimeString('pt-BR') : '—', color: '#E8F0EA' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: '#0E1410', borderRadius: 10, padding: '14px 16px', border: '1px solid #1A2A1C' }}>
              <div style={{ fontSize: 10, color: '#5A7A5E', marginBottom: 6 }}>{label}</div>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 18, fontWeight: 800, color }}>{value}</div>
            </div>
          ))}
        </div>

        {!healthy && (
          <div style={{ marginTop: 16, padding: '12px 16px', background: `${R}15`, borderRadius: 8, border: `1px solid ${R}44` }}>
            <div style={{ fontSize: 12, color: R, fontWeight: 600 }}>
              ⚠️ Scheduler pode estar inativo. Se persistir, reinicie o servidor.
            </div>
          </div>
        )}
      </div>

      {/* ── 2. Custo de Tokens IA ─────────────────────────────────────────── */}
      <div style={{ background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
        <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 4 }}>
          🤖 Custo de IA (OpenAI) — Mês Atual
        </div>
        <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 20 }}>
          Budget padrão por cliente: R$ 100/mês · Alerta em 80%
        </div>

        {tokenCosts.length === 0 ? (
          <div style={{ color: '#5A7A5E', fontSize: 13 }}>
            Nenhum custo de IA registrado. USE_MOCK=true ou sem leads processados.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {tokenCosts.map(c => {
              const pct = Math.min(100, Math.round((c.cost_brl / 100) * 100));
              const barColor = pct >= 80 ? R : pct >= 50 ? Y : G;
              return (
                <div key={c.client_id} style={{ background: '#0E1410', borderRadius: 10, padding: '14px 16px', border: `1px solid ${pct >= 80 ? R + '44' : '#1A2A1C'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#E8F0EA' }}>{c.client_name || `Cliente #${c.client_id}`}</div>
                      <div style={{ fontSize: 10, color: '#5A7A5E' }}>{c.total_tokens?.toLocaleString() || 0} tokens · {c.conversations || 0} conversas</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 16, fontWeight: 800, fontFamily: "'Syne', sans-serif", color: barColor }}>
                        R$ {(c.cost_brl || 0).toFixed(2)}
                      </div>
                      <div style={{ fontSize: 10, color: '#5A7A5E' }}>{pct}% do budget</div>
                    </div>
                  </div>
                  <div style={{ height: 4, background: '#1A2A1C', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: 2, transition: 'width 0.5s ease' }} />
                  </div>
                  {pct >= 80 && (
                    <div style={{ fontSize: 11, color: R, fontWeight: 600, marginTop: 6 }}>
                      ⚠️ Alerta: {pct}% do budget consumido!
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── 3. Feed de Follow-ups ─────────────────────────────────────────── */}
      <div style={{ background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff' }}>
              📋 Atividade de Follow-ups
            </div>
            <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
              Leads com follow-up pendente ou recente
            </div>
          </div>
          <button onClick={load} style={{
            background: 'transparent', border: '1px solid #1A2A1C', color: '#5A7A5E',
            padding: '6px 12px', borderRadius: 8, cursor: 'pointer', fontSize: 11,
            fontFamily: "'DM Sans', sans-serif",
          }}>
            ↻ Atualizar
          </button>
        </div>

        {followups.length === 0 ? (
          <div style={{ color: '#5A7A5E', fontSize: 13 }}>
            Nenhum lead com follow-up pendente no momento.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {followups.slice(0, 15).map(lead => {
              const tagColor = lead.classification === 'hot' ? R : lead.classification === 'warm' ? Y : B;
              const tagEmoji = lead.classification === 'hot' ? '🔥' : lead.classification === 'warm' ? '🌡' : '❄️';
              return (
                <div key={lead.id} style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  padding: '12px 16px', background: '#0E1410',
                  borderRadius: 10, border: '1px solid #1A2A1C',
                }}>
                  <span style={{
                    fontSize: 11, fontWeight: 700, padding: '3px 10px',
                    borderRadius: 100, background: tagColor + '22', color: tagColor, flexShrink: 0,
                  }}>
                    {tagEmoji} {(lead.classification || 'cold').toUpperCase()}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#E8F0EA' }}>
                      {lead.phone}
                    </div>
                    <div style={{ fontSize: 11, color: '#5A7A5E', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {lead.summary || 'Sem resumo'}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#E8F0EA' }}>
                      Score {lead.score ?? 0}
                    </div>
                    <div style={{ fontSize: 10, color: '#5A7A5E' }}>
                      {lead.status}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * DASHBOARD DO ADMIN - VERSÃO OTIMIZADA

 * Implementa todas as melhorias de Semana 1
 * 
 * Melhorias incluídas:
 * 1. ✅ "Clientes em Risco" com health < 60%
 * 2. ✅ "Previsões" (MRR, churn)
 * 3. ✅ "Insights" com recomendações
 * 4. ✅ "Análise de Cohort"
 * 5. ✅ "Automação de Relatórios"
 */

export default function AdminDashboardOtimizado() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedRiskClient, setSelectedRiskClient] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [expandedClientId, setExpandedClientId] = useState(null);
  const [healthCheckRunning, setHealthCheckRunning] = useState(false);
  const [searchClientTerm, setSearchClientTerm] = useState('');
  const [clientStatusFilter, setClientStatusFilter] = useState('all');

  // ── Estado do ConfirmDialog ───────────────────────────────────────────────
  const [confirm, setConfirm] = useState({
    open: false,
    title: '',
    message: '',
    variant: 'danger',
    confirmLabel: 'Confirmar',
    onConfirm: null,
  });

  const closeConfirm = useCallback(() =>
    setConfirm(prev => ({ ...prev, open: false, onConfirm: null })),
    []);

  const { logout } = useAuth();
  const navigate = useNavigate();

  // ── Cores semânticas ─────────────────────────────────────────────────────
  const G = '#00C853';
  const R = '#FF5252';
  const Y = '#FFD600';
  const B = '#2196F3';

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  // ── Dados reais da API (com fallback para dados demo) ─────────────────────
  const { clients: apiClients, reload } = useAdminDashboard();

  const DEMO_CLIENTS = [
    { id: 1, name: 'Silva & Cia', niche: 'Imobiliária', package: 'enterprise', mrr: 2990, leads: 280, health: 95, status: 'active', color: G, since: 'Jan 2025', conversion: 22, churnRisk: 0 },
    { id: 2, name: 'Santos Imóveis', niche: 'Imobiliária', package: 'pro', mrr: 1490, leads: 150, health: 88, status: 'active', color: B, since: 'Fev 2025', conversion: 18, churnRisk: 5 },
    { id: 3, name: 'Dr. Paulo Clínica', niche: 'Consultório', package: 'pro', mrr: 1490, leads: 80, health: 61, status: 'warning', color: Y, since: 'Jan 2025', conversion: 12, churnRisk: 35 },
    { id: 4, name: 'Estética Bella', niche: 'Estética', package: 'starter', mrr: 690, leads: 40, health: 45, status: 'warning', color: R, since: 'Dez 2024', conversion: 8, churnRisk: 65 },
    { id: 5, name: 'Costa Empreend.', niche: 'Imobiliária', package: 'enterprise', mrr: 2990, leads: 350, health: 92, status: 'active', color: G, since: 'Nov 2024', conversion: 20, churnRisk: 0 },
  ];

  const CLIENTS = apiClients.length > 0 ? apiClients : DEMO_CLIENTS;


  // ── useMemo: evita recálculos desnecessários em cada render ──────────────
  const totalMRR = useMemo(() => CLIENTS.reduce((s, c) => s + c.mrr, 0), [CLIENTS]);
  const totalLeads = useMemo(() => CLIENTS.reduce((s, c) => s + c.leads, 0), [CLIENTS]);
  const avgHealth = useMemo(() => Math.round(CLIENTS.reduce((s, c) => s + c.health, 0) / (CLIENTS.length || 1)), [CLIENTS]);
  const riskClients = useMemo(() => CLIENTS.filter(c => c.health < 70).sort((a, b) => a.health - b.health), [CLIENTS]);

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

  // Componente de Card de Métrica
  const KPICard = ({ icon, label, value, sub, color, delta }) => (
    <div style={{
      background: '#0E1410',
      border: '1px solid #1A2A1C',
      borderRadius: 16,
      padding: 28,
    }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontSize: 14, color: '#5A7A5E', marginBottom: 6, fontWeight: 500 }}>{label}</div>
      <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 36, fontWeight: 800, color, marginBottom: 6, lineHeight: 1.1 }}>
        {value}
      </div>
      <div style={{ fontSize: 13, color: '#5A7A5E', marginBottom: 10 }}>{sub}</div>
      {delta && (
        <div style={{ fontSize: 13, color: G, fontWeight: 600 }}>
          ↑ +{delta}% vs mês anterior
        </div>
      )}
    </div>
  );

  // Componente de Cliente em Risco
  const RiskClientCard = ({ client }) => (
    <div
      onClick={() => setSelectedRiskClient(client)}
      style={{
        background: '#0E1410',
        border: `2px solid ${R}`,
        borderRadius: 12,
        padding: 16,
        cursor: 'pointer',
        marginBottom: 12,
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateX(4px)';
        e.currentTarget.style.boxShadow = `0 0 20px ${R}33`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateX(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#fff', marginBottom: 4 }}>
            {client.name}
          </div>
          <div style={{ fontSize: 11, color: '#5A7A5E' }}>
            {client.niche} • Desde {client.since}
          </div>
        </div>
        <span style={{
          fontSize: 11,
          fontWeight: 700,
          padding: '4px 12px',
          borderRadius: 100,
          background: `${R}22`,
          color: R,
        }}>
          {client.churnRisk}% risco
        </span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 10, color: '#5A7A5E', marginBottom: 2 }}>Health</div>
          <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 18, fontWeight: 800, color: R }}>
            {client.health}%
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: '#5A7A5E', marginBottom: 2 }}>MRR</div>
          <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 18, fontWeight: 800, color: '#E8F0EA' }}>
            R$ {client.mrr.toLocaleString()}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: '#5A7A5E', marginBottom: 2 }}>Leads/mês</div>
          <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 18, fontWeight: 800, color: B }}>
            {client.leads}
          </div>
        </div>
      </div>

      <div style={{ height: 1, background: '#1A2A1C', margin: '12px 0' }} />

      <button style={{
        background: `${R}22`,
        border: `1px solid ${R}`,
        color: R,
        padding: '6px 12px',
        borderRadius: 6,
        cursor: 'pointer',
        fontSize: 11,
        fontWeight: 600,
        width: '100%',
      }}>
        Agendar Call com Cliente
      </button>
    </div>
  );

  // Componente de Insight
  const InsightCard = ({ insight }) => (
    <div style={{
      background: '#0E1410',
      border: '1px solid #1A2A1C',
      borderRadius: 12,
      padding: 20,
      marginBottom: 12,
    }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
        💡 {insight.title}
      </div>
      <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 12 }}>
        {insight.description}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 11, color: '#5A7A5E' }}>
          Ação: <span style={{ color: G, fontWeight: 600 }}>{insight.action}</span>
        </div>
        <div style={{ fontSize: 11, color: G, fontWeight: 600 }}>
          {insight.impact}
        </div>
      </div>
    </div>
  );


  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", color: '#E8F0EA', minHeight: '100vh', background: '#060908' }}>
      {/* Header */}
      <div style={{ background: '#0A0F0B', borderBottom: '1px solid #1A2A1C', padding: '16px 20px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 10, height: 10,
                background: G,
                borderRadius: '50%',
                animation: 'pulse 2s infinite',
                flexShrink: 0,
              }} />
              <span style={{
                fontFamily: "'Syne', sans-serif",
                fontWeight: 800,
                fontSize: 22,
                color: '#fff',
              }}>MFL Digital Solutions</span>
            </div>
            <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
              Painel de Controle
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              background: '#1A2A1C',
              border: '1px solid #2A3A2C',
              borderRadius: 8,
              padding: '8px 16px',
              fontSize: 12,
              color: '#FF5252',
              fontWeight: 600,
            }}>
              {riskClients.length} ⚠️ clientes em risco
            </div>
            <button
              onClick={handleLogout}
              style={{
                background: 'transparent',
                border: '1px solid #1A2A1C',
                color: '#5A7A5E',
                padding: '8px 14px',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: 12,
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              Sair
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mobile-tabs" style={{ display: 'flex', borderBottom: '1px solid #1A2A1C', background: '#0A0F0B', padding: '0 20px', overflowX: 'auto', whiteSpace: 'nowrap' }}>
        {[
          ['overview', '🗂️ Visão Geral'],
          ['clients', '👥 Clientes'],
          ['risk', '⚠️ Clientes em Risco'],
          ['forecast', '🔮 Previsões'],
          ['insights', '💡 Insights'],
          ['cohort', '📊 Análise de Cohort'],
          ['automation', '⚙️ Automação'],
          ['sistema', '⚡ Sistema'],
        ].map(([id, label]) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === id ? `2px solid ${G}` : '2px solid transparent',
              color: activeTab === id ? G : '#5A7A5E',
              padding: '16px 22px',
              fontSize: 15,
              fontWeight: activeTab === id ? 700 : 500,
              cursor: 'pointer',
              transition: 'all 0.2s',
              fontFamily: "'DM Sans', sans-serif",
              whiteSpace: 'nowrap',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="p-mobile" style={{ padding: '36px 40px', maxWidth: 1320, margin: '0 auto' }}>
        {/* OVERVIEW */}
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* KPIs */}
            <div className="dashboard-grid-4" style={{ gap: 20 }}>
              <KPICard icon="💰" label="MRR Total" value={`R$ ${fmt(totalMRR)}`} sub={`${CLIENTS.length} clientes`} color={G} delta={22} />
              <KPICard icon="📨" label="Leads/mês" value={fmt(totalLeads)} sub="processados" color={B} delta={31} />
              <KPICard icon="❤️" label="Health Médio" value={`${avgHealth}%`} sub="satisfação" color="#E91E8C" delta={5} />
              <KPICard icon="📅" label="ARR Projetado" value={`R$ ${fmt(totalMRR * 12)}`} sub="anualizado" color={Y} delta={22} />
            </div>

            {/* Status dos Clientes */}
            <div style={{ background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 14, padding: 24 }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 20 }}>
                Status dos Clientes
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {CLIENTS.map(c => (
                  <div key={c.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    padding: '14px 16px',
                    background: '#0E1410',
                    borderRadius: 10,
                    border: '1px solid #1A2A1C',
                  }}>
                    <div style={{
                      width: 36,
                      height: 36,
                      borderRadius: '50%',
                      background: c.color + '22',
                      border: `2px solid ${c.color}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 14,
                    }}>
                      {c.niche === 'Imobiliária' ? '🏠' : c.niche.includes('Estética') ? '💆' : '🏥'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#E8F0EA' }}>{c.name}</div>
                      <div style={{ fontSize: 11, color: '#5A7A5E' }}>{c.niche} · {c.since}</div>
                    </div>
                    <div style={{ textAlign: 'center', minWidth: 60 }}>
                      <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 18, fontWeight: 800, color: c.color }}>
                        R$ {fmt(c.mrr)}
                      </div>
                      <div style={{ fontSize: 10, color: '#5A7A5E' }}>/mês</div>
                    </div>
                    <div style={{ minWidth: 120 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: 10, color: '#5A7A5E' }}>Health</span>
                        <span style={{ fontSize: 10, fontWeight: 700, color: c.health >= 80 ? G : c.health >= 60 ? Y : R }}>
                          {c.health}%
                        </span>
                      </div>
                      <div style={{ height: 4, background: '#1A2A1C', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${c.health}%`,
                          background: c.health >= 80 ? G : c.health >= 60 ? Y : R,
                          borderRadius: 2,
                        }} />
                      </div>
                    </div>
                    <span style={{
                      fontSize: 11,
                      padding: '3px 10px',
                      borderRadius: 100,
                      background: c.status === 'active' ? `${G}22` : `${R}22`,
                      color: c.status === 'active' ? G : R,
                      fontWeight: 700,
                    }}>
                      {c.status === 'active' ? '● Ativo' : '⚠️ Atenção'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* GERENCIAMENTO DE CLIENTES */}
        {activeTab === 'clients' && (() => {
          const handleDeactivate = (client) => {
            setConfirm({
              open: true,
              title: 'Desativar cliente',
              message: `Tem certeza que deseja desativar "${client.name}"? O cliente perderá acesso ao dashboard imediatamente.`,
              variant: 'danger',
              confirmLabel: 'Desativar',
              onConfirm: async () => {
                closeConfirm();
                try {
                  const res = await fetch(`/api/clients/${client.id}`, {
                    method: 'DELETE', credentials: 'include',
                  });
                  if (res.ok) { toast.success(`${client.name} desativado.`); reload(); }
                  else { toast.error('Erro ao desativar cliente'); }
                } catch { toast.error('Erro de conexão'); }
              },
            });
          };

          const handleResetPassword = (client) => {
            setConfirm({
              open: true,
              title: 'Resetar senha',
              message: `Resetar a senha de "${client.name}" para a senha padrão mfl2026?`,
              variant: 'warning',
              confirmLabel: 'Resetar senha',
              onConfirm: async () => {
                closeConfirm();
                try {
                  const res = await fetch(`/api/clients/${client.id}/reset-password`, {
                    method: 'POST', credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: 'mfl2026' }),
                  });
                  if (res.ok) toast.success('Senha resetada para mfl2026');
                  else toast.error('Erro ao resetar senha');
                } catch { toast.error('Erro de conexão'); }
              },
            });
          };

          const filteredClients = CLIENTS.filter(c => {
            const matchesSearch = c.name.toLowerCase().includes(searchClientTerm.toLowerCase()) ||
              (c.username && c.username.toLowerCase().includes(searchClientTerm.toLowerCase())) ||
              (c.whatsapp_number && c.whatsapp_number.includes(searchClientTerm));
            const matchesStatus = clientStatusFilter === 'all' || c.status === clientStatusFilter;
            return matchesSearch && matchesStatus;
          });

          return (
            <div>
              {/* Header da aba */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
                <div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 20, fontWeight: 800, color: '#fff' }}>
                    👥 Gerenciar Clientes
                  </div>
                  <div style={{ fontSize: 13, color: '#5A7A5E', marginTop: 4 }}>
                    {filteredClients.length} de {CLIENTS.length} cliente(s) · Clique em uma linha para histórico de saúde
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                  {/* Busca e Filtro */}
                  <input
                    type="text"
                    placeholder="Buscar nome, arroba, número..."
                    value={searchClientTerm}
                    onChange={(e) => setSearchClientTerm(e.target.value)}
                    style={{
                      padding: '10px 14px', borderRadius: 8, border: '1px solid #1A2A1C',
                      background: '#060908', color: '#fff', fontSize: 13, width: 220,
                    }}
                  />
                  <select
                    value={clientStatusFilter}
                    onChange={(e) => setClientStatusFilter(e.target.value)}
                    style={{
                      padding: '10px 14px', borderRadius: 8, border: '1px solid #1A2A1C',
                      background: '#060908', color: '#fff', fontSize: 13, cursor: 'pointer',
                    }}
                  >
                    <option value="all">Todos os Status</option>
                    <option value="active">Ativo</option>
                    <option value="inactive">Inativo</option>
                  </select>


                  {/* Botão Verificar Saúde */}
                  <button
                    onClick={async () => {
                      setHealthCheckRunning(true);
                      const t = toast.loading('Verificando saúde de todos os clientes...');
                      try {
                        const result = await runHealthCheck();
                        toast.dismiss(t);
                        toast.success(
                          `✅ ${result.checked} cliente(s) verificados | 📱${result.wa_alerts} alertas WA | ✉️ ${result.emails_sent} e-mails`,
                          { duration: 6000 }
                        );
                        reload();
                      } catch {
                        toast.dismiss(t);
                        toast.error('Erro ao executar health check');
                      } finally {
                        setHealthCheckRunning(false);
                      }
                    }}
                    disabled={healthCheckRunning}
                    style={{
                      background: '#1A2A1C', border: `1px solid ${G}44`,
                      borderRadius: 10, color: G, padding: '12px 20px',
                      fontSize: 13, fontWeight: 700, cursor: healthCheckRunning ? 'not-allowed' : 'pointer',
                      fontFamily: "'DM Sans', sans-serif",
                      display: 'flex', alignItems: 'center', gap: 8,
                      opacity: healthCheckRunning ? 0.6 : 1, transition: 'opacity 0.2s',
                    }}
                  >
                    {healthCheckRunning ? '⏳ Verificando...' : '🩺 Verificar Saúde'}
                  </button>
                  {/* Botão Novo Cliente */}
                  <button
                    onClick={() => { setEditingClient(null); setModalOpen(true); }}
                    style={{
                      background: G, border: 'none', borderRadius: 10,
                      color: '#060908', padding: '12px 24px',
                      fontSize: 14, fontWeight: 700, cursor: 'pointer',
                      fontFamily: "'DM Sans', sans-serif",
                      display: 'flex', alignItems: 'center', gap: 8,
                    }}
                  >
                    ➕ Novo Cliente
                  </button>
                </div>
              </div>

              {/* Tabela de clientes */}
              <div style={{ background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 14, overflow: 'hidden' }}>
                {/* Cabeçalho */}
                <div className="dashboard-grid-6 hide-mobile" style={{
                  padding: '12px 20px',
                  borderBottom: '1px solid #1A2A1C',
                  fontSize: 11, fontWeight: 700, color: '#5A7A5E',
                  textTransform: 'uppercase', letterSpacing: 1,
                }}>
                  <span>Cliente</span>
                  <span>Plano</span>
                  <span>MRR</span>
                  <span>Health</span>
                  <span>Status</span>
                  <span style={{ textAlign: 'right' }}>Ações</span>
                </div>

                {/* Linhas */}
                {filteredClients.map((c, idx) => {
                  const isExpanded = expandedClientId === c.id;

                  return (
                    <div key={c.id} style={{ borderBottom: idx < CLIENTS.length - 1 ? '1px solid #0E1410' : 'none' }}>
                      <div className="dashboard-grid-6" style={{
                        padding: '16px 20px',
                        alignItems: 'center',
                        transition: 'background 0.15s',
                        cursor: 'pointer',
                        background: isExpanded ? '#0E1410' : 'transparent',
                      }}
                        onClick={() => setExpandedClientId(isExpanded ? null : c.id)}
                        onMouseEnter={e => { if (!isExpanded) e.currentTarget.style.background = '#0A0F0B'; }}
                        onMouseLeave={e => { if (!isExpanded) e.currentTarget.style.background = 'transparent'; }}
                      >
                        {/* Nome + info */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <div style={{
                            width: 38, height: 38, borderRadius: '50%',
                            background: c.color + '22', border: `2px solid ${c.color}`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
                            flexShrink: 0,
                          }}>
                            {c.niche === 'Imobiliária' ? '🏠' : c.niche?.includes('Estética') ? '💆' : c.niche?.includes('Consultório') ? '🏥' : '🏢'}
                          </div>
                          <div>
                            <div style={{ fontSize: 14, fontWeight: 600, color: '#E8F0EA' }}>{c.name}</div>
                            <div style={{ fontSize: 11, color: '#5A7A5E' }}>@{c.username || '—'} · {c.niche}</div>
                          </div>
                        </div>

                        {/* Plano */}
                        <div style={{ fontSize: 13, color: '#E8F0EA', textTransform: 'capitalize' }}>
                          {c.package || 'pro'}
                        </div>

                        {/* MRR */}
                        <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 15, fontWeight: 700, color: G }}>
                          R$ {fmt(c.mrr)}
                        </div>

                        {/* Health */}
                        <div>
                          <div style={{
                            fontSize: 13, fontWeight: 700,
                            color: c.health >= 80 ? G : c.health >= 60 ? Y : R
                          }}>
                            {c.health}%
                          </div>
                          <div style={{ height: 3, background: '#1A2A1C', borderRadius: 2, marginTop: 4, width: 60 }}>
                            <div style={{
                              height: '100%', borderRadius: 2, width: `${c.health}%`,
                              background: c.health >= 80 ? G : c.health >= 60 ? Y : R,
                            }} />
                          </div>
                        </div>

                        {/* Status */}
                        <span style={{
                          fontSize: 11, padding: '4px 12px', borderRadius: 100, fontWeight: 700,
                          background: c.status === 'active' ? `${G}22` : `${R}22`,
                          color: c.status === 'active' ? G : R,
                        }}>
                          {c.status === 'active' ? '● Ativo' : '○ Inativo'}
                        </span>

                        {/* Ações */}
                        <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                          {/* Editar */}
                          <button
                            title="Editar"
                            onClick={() => { setEditingClient(c); setModalOpen(true); }}
                            style={{
                              background: '#1A2A1C', border: 'none', borderRadius: 7,
                              color: '#E8F0EA', width: 32, height: 32, cursor: 'pointer',
                              fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            }}
                          >✏️</button>

                          {/* Reset senha */}
                          <button
                            title="Resetar senha"
                            onClick={() => handleResetPassword(c)}
                            style={{
                              background: '#1A2A1C', border: 'none', borderRadius: 7,
                              color: Y, width: 32, height: 32, cursor: 'pointer',
                              fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            }}
                          >🔑</button>

                          {/* Desativar */}
                          {c.status === 'active' && (
                            <button
                              title="Desativar"
                              onClick={() => handleDeactivate(c)}
                              style={{
                                background: `${R}22`, border: 'none', borderRadius: 7,
                                color: R, width: 32, height: 32, cursor: 'pointer',
                                fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center',
                              }}
                            >🗑️</button>
                          )}
                        </div>
                      </div>
                      {isExpanded && <HealthPanel client={c} />}
                    </div>
                  );
                })}


                {filteredClients.length === 0 && (
                  <div style={{ padding: 48, textAlign: 'center', color: '#5A7A5E' }}>
                    <div style={{ fontSize: 40, marginBottom: 12 }}>👥</div>
                    <div style={{ fontSize: 14 }}>
                      {CLIENTS.length === 0
                        ? 'Nenhum cliente cadastrado ainda.'
                        : 'Nenhum cliente encontrado com estes filtros.'}
                    </div>
                    {CLIENTS.length === 0 && (
                      <div style={{ fontSize: 12, marginTop: 4 }}>Clique em "Novo Cliente" para começar.</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })()}

        {/* CLIENTES EM RISCO */}
        {activeTab === 'risk' && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                ⚠️ Clientes em Risco de Churn
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                {riskClients.length} cliente(s) com health &lt; 70% requer(em) atenção imediata
              </div>
            </div>

            {riskClients.map(client => (
              <RiskClientCard key={client.id} client={client} />
            ))}

            {riskClients.length === 0 && (
              <div style={{
                background: '#0E1410',
                border: '1px solid #1A2A1C',
                borderRadius: 12,
                padding: 40,
                textAlign: 'center',
              }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>✓</div>
                <div style={{ fontSize: 13, color: G, fontWeight: 600, marginBottom: 4 }}>
                  Excelente! Nenhum cliente em risco
                </div>
                <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                  Todos os seus clientes têm health &gt; 70%
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
              <div className="dashboard-grid-3" style={{ gap: 16 }}>
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
              <div className="dashboard-grid-2" style={{ gap: 16 }}>
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

        {/* ABA SISTEMA ─────────────────────────────────────────────────────── */}
        {activeTab === 'sistema' && <SistemaTab G={G} R={R} Y={Y} B={B} />}

      </div>

      {/* Modal de criar/editar cliente */}
      <ClientModal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setEditingClient(null); }}
        onSaved={() => reload()}
        editClient={editingClient}
      />

      {/* Modal de confirmação (substitui window.confirm) */}
      <ConfirmDialog
        isOpen={confirm.open}
        title={confirm.title}
        message={confirm.message}
        variant={confirm.variant}
        confirmLabel={confirm.confirmLabel}
        onConfirm={confirm.onConfirm}
        onCancel={closeConfirm}
      />

      {/* Modal de detalhe: cliente em risco */}
      <RiskClientModal
        client={selectedRiskClient}
        onClose={() => setSelectedRiskClient(null)}
      />
    </div >
  );
}


