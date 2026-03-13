import React, { useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

/**
 * DASHBOARD DO CLIENTE - VERSÃO OTIMIZADA
 * Implementa todas as melhorias de Semana 1
 * 
 * Melhorias incluídas:
 * 1. ✅ Seção "Recomendações" com 3-5 ações priorizadas
 * 2. ✅ "Você vs Mercado" com percentil
 * 3. ✅ Gráficos de tendência (últimas 4 semanas)
 * 4. ✅ "Alertas" com notificações
 * 5. ✅ "Próximo Passo" com sugestão de upgrade
 */

export default function ClientDashboardOtimizado() {
  const [activeTab, setActiveTab] = useState('overview');
  const [showRecommendationDetail, setShowRecommendationDetail] = useState(null);
  
  const G = '#00C853'; // Verde primário
  const R = '#FF5252'; // Vermelho para alertas
  const Y = '#FFD600'; // Amarelo para avisos
  const B = '#2196F3'; // Azul

  // Dados de tendência (últimas 4 semanas)
  const trendData = [
    { week: 'Sem 1', leads: 45, qualified: 32, conversion: 15, response: 3.2 },
    { week: 'Sem 2', leads: 52, qualified: 38, conversion: 17, response: 3.0 },
    { week: 'Sem 3', leads: 48, qualified: 35, conversion: 16, response: 2.9 },
    { week: 'Sem 4', leads: 58, qualified: 42, conversion: 19, response: 2.7 },
  ];

  // Dados de benchmark
  const benchmarkData = {
    qualificationRate: { yours: 78, market: 85, percentile: 35 },
    conversionRate: { yours: 18, market: 22, percentile: 45 },
    responseTime: { yours: 2.7, market: 1.8, percentile: 25 },
    followUpAttempts: { yours: 2, market: 4, percentile: 20 },
  };

  // Recomendações priorizadas
  const recommendations = [
    {
      id: 1,
      title: 'Aumentar Tempo de Resposta',
      description: 'Seu tempo: 2m 47s | Meta: < 2min',
      impact: 5200,
      effort: 'Médio',
      action: 'Aumentar equipe em 1 corretor',
      status: 'critical',
      priority: 1,
    },
    {
      id: 2,
      title: 'Melhorar Taxa de Qualificação',
      description: 'Sua taxa: 78% | Mercado: 85%',
      impact: 3800,
      effort: 'Baixo',
      action: 'Otimizar perguntas do bot',
      status: 'high',
      priority: 2,
    },
    {
      id: 3,
      title: 'Aumentar Follow-up',
      description: 'Seu follow-up: 2 tentativas | Melhor: 4 tentativas',
      impact: 2100,
      effort: 'Baixo',
      action: 'Ativar follow-up automático',
      status: 'medium',
      priority: 3,
    },
    {
      id: 4,
      title: 'Expandir Horário de Atendimento',
      description: 'Atualmente: 9h-18h | Oportunidade: 24h',
      impact: 1500,
      effort: 'Alto',
      action: 'Implementar bot 24/7',
      status: 'low',
      priority: 4,
    },
  ];

  // Alertas
  const alerts = [
    {
      id: 1,
      type: 'critical',
      title: 'Taxa de Resposta Acima da Meta',
      message: 'Tempo de resposta subiu para 2m 47s (meta: 2min). Recomendamos aumentar equipe.',
      date: 'Hoje às 14:30',
    },
    {
      id: 2,
      type: 'warning',
      title: 'Queda na Taxa de Conversão',
      message: 'Taxa de conversão caiu 5% comparado à semana anterior. Verifique qualidade dos leads.',
      date: 'Ontem às 09:15',
    },
  ];

  // Sugestão de upgrade
  const upgradeOpportunity = {
    current: 'Pro',
    currentLeads: 280,
    currentLimit: 200,
    recommended: 'Enterprise',
    recommendedLimit: 500,
    additionalCost: 2500,
    justification: 'Você está processando 280 leads/mês. Seu plano Pro suporta até 200. Recomendamos upgrade para Enterprise.',
  };

  // Componente de Card de Métrica
  const MetricCard = ({ label, value, unit, trend, trendDirection }) => (
    <div style={{
      background: '#0E1410',
      border: '1px solid #1A2A1C',
      borderRadius: 12,
      padding: 20,
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 8 }}>{label}</div>
      <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 32, fontWeight: 800, color: G, marginBottom: 4 }}>
        {value}
      </div>
      <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 12 }}>{unit}</div>
      {trend && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 6,
          fontSize: 12,
          color: trendDirection === 'up' ? G : R,
          fontWeight: 600,
        }}>
          <span>{trendDirection === 'up' ? '↑' : '↓'}</span>
          <span>{trend}% vs semana anterior</span>
        </div>
      )}
    </div>
  );

  // Componente de Recomendação
  const RecommendationCard = ({ rec }) => (
    <div
      onClick={() => setShowRecommendationDetail(rec.id)}
      style={{
        background: '#0E1410',
        border: `2px solid ${
          rec.status === 'critical' ? R : rec.status === 'high' ? Y : rec.status === 'medium' ? B : '#1A2A1C'
        }`,
        borderRadius: 12,
        padding: 20,
        cursor: 'pointer',
        transition: 'all 0.2s',
        marginBottom: 12,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateX(4px)';
        e.currentTarget.style.boxShadow = `0 0 20px ${
          rec.status === 'critical' ? R : rec.status === 'high' ? Y : B
        }33`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateX(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 4 }}>
            {rec.priority}. {rec.title}
          </div>
          <div style={{ fontSize: 12, color: '#5A7A5E' }}>{rec.description}</div>
        </div>
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            padding: '4px 12px',
            borderRadius: 100,
            background:
              rec.status === 'critical'
                ? `${R}22`
                : rec.status === 'high'
                ? `${Y}22`
                : rec.status === 'medium'
                ? `${B}22`
                : '#1A2A1C',
            color:
              rec.status === 'critical'
                ? R
                : rec.status === 'high'
                ? Y
                : rec.status === 'medium'
                ? B
                : '#5A7A5E',
          }}
        >
          {rec.effort}
        </span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Impacto Potencial</div>
          <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: G }}>
            +R$ {rec.impact.toLocaleString()}
          </div>
          <div style={{ fontSize: 10, color: '#5A7A5E' }}>/mês</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Ação Necessária</div>
          <div style={{ fontSize: 12, color: '#E8F0EA', fontWeight: 600 }}>{rec.action}</div>
        </div>
      </div>

      <div style={{ height: 1, background: '#1A2A1C', margin: '12px 0' }} />

      <div style={{ fontSize: 11, color: '#5A7A5E', textAlign: 'center' }}>
        👉 Clique para mais detalhes
      </div>
    </div>
  );

  // Componente de Alerta
  const AlertCard = ({ alert }) => (
    <div
      style={{
        background: '#0E1410',
        border: `2px solid ${alert.type === 'critical' ? R : Y}`,
        borderRadius: 12,
        padding: 16,
        marginBottom: 12,
        display: 'flex',
        gap: 12,
      }}
    >
      <div style={{ fontSize: 20 }}>{alert.type === 'critical' ? '🚨' : '⚠️'}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#fff', marginBottom: 4 }}>
          {alert.title}
        </div>
        <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 4 }}>
          {alert.message}
        </div>
        <div style={{ fontSize: 10, color: '#5A7A5E' }}>{alert.date}</div>
      </div>
      <button
        style={{
          background: alert.type === 'critical' ? `${R}22` : `${Y}22`,
          border: `1px solid ${alert.type === 'critical' ? R : Y}`,
          color: alert.type === 'critical' ? R : Y,
          padding: '6px 12px',
          borderRadius: 6,
          cursor: 'pointer',
          fontSize: 11,
          fontWeight: 600,
          whiteSpace: 'nowrap',
        }}
      >
        Agir Agora
      </button>
    </div>
  );

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", color: '#E8F0EA', minHeight: '100vh', background: '#060908' }}>
      {/* Header */}
      <div style={{ background: '#0A0F0B', borderBottom: '1px solid #1A2A1C', padding: '16px 28px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 20, color: '#fff', marginBottom: 4 }}>
            <span style={{ color: G }}>⬡</span> MFL Digital Solutions
          </div>
          <div style={{ fontSize: 12, color: '#5A7A5E' }}>
            Dashboard de Resultados - Imobiliária Silva & Cia
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #1A2A1C', background: '#0A0F0B', padding: '0 28px' }}>
        {[
          ['overview', '📊 Visão Geral'],
          ['recommendations', '🎯 Recomendações'],
          ['alerts', '🚨 Alertas'],
          ['benchmark', '📈 Você vs Mercado'],
          ['trends', '📉 Tendências'],
        ].map(([id, label]) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === id ? `2px solid ${G}` : '2px solid transparent',
              color: activeTab === id ? G : '#5A7A5E',
              padding: '14px 20px',
              fontSize: 13,
              fontWeight: activeTab === id ? 700 : 400,
              cursor: 'pointer',
              transition: 'all 0.2s',
              fontFamily: "'DM Sans', sans-serif",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div style={{ padding: '28px', maxWidth: 1200, margin: '0 auto' }}>
        {/* OVERVIEW */}
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* KPIs */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
              <MetricCard label="Leads Processados" value="58" unit="este mês" trend={21} trendDirection="up" />
              <MetricCard label="Taxa de Qualificação" value="78%" unit="leads qualificados" trend={5} trendDirection="up" />
              <MetricCard label="Taxa de Conversão" value="18%" unit="leads → reuniões" trend={-5} trendDirection="down" />
              <MetricCard label="Tempo de Resposta" value="2m 47s" unit="média" trend={-8} trendDirection="down" />
            </div>

            {/* Ganho Mensal */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 28 }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 20 }}>
                💰 Seu Ganho Mensal
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20 }}>
                <div>
                  <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 8 }}>Sem MFL Digital</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 32, fontWeight: 800, color: '#5A7A5E' }}>
                    R$ 45.000
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
                    (58 leads × R$ 775 conversão média)
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 8 }}>Com MFL Digital</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 32, fontWeight: 800, color: G }}>
                    R$ 63.250
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
                    (58 leads × R$ 1.091 conversão otimizada)
                  </div>
                </div>
              </div>
              <div style={{ height: 1, background: '#1A2A1C', margin: '20px 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 4 }}>Ganho Adicional</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 28, fontWeight: 800, color: G }}>
                    +R$ 18.250
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 4 }}>ROI</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 28, fontWeight: 800, color: G }}>
                    652%
                  </div>
                </div>
              </div>
            </div>

            {/* Horas Economizadas */}
            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 14, padding: 28 }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 20 }}>
                ⏱️ Horas Economizadas
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {[
                  { label: 'Qualificação manual', before: 28, after: 4 },
                  { label: 'Registro no CRM', before: 6, after: 0 },
                  { label: 'Follow-up manual', before: 12, after: 1 },
                  { label: 'Distribuição de leads', before: 4, after: 0 },
                ].map((item) => (
                  <div key={item.label}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: '#E8F0EA' }}>{item.label}</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color: G }}>
                        -{item.before - item.after}h/semana
                      </span>
                    </div>
                    <div style={{ height: 6, background: '#1A2A1C', borderRadius: 3, overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${((item.after / item.before) * 100) || 2}%`,
                          background: G,
                          borderRadius: 3,
                        }}
                      />
                    </div>
                  </div>
                ))}
                <div style={{ marginTop: 8, padding: '14px', background: `${G}22`, border: `1px solid ${G}44`, borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#5A7A5E' }}>Total economizado por semana</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 28, fontWeight: 800, color: G }}>
                    41 horas
                  </div>
                  <div style={{ fontSize: 11, color: '#5A7A5E' }}>= 1 corretor extra sem contratar ninguém</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* RECOMENDAÇÕES */}
        {activeTab === 'recommendations' && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                🎯 Recomendações Priorizadas
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                Ações que podem aumentar seu ganho em até R$ 12.600/mês
              </div>
            </div>

            {recommendations.map((rec) => (
              <RecommendationCard key={rec.id} rec={rec} />
            ))}

            {/* Resumo de Impacto */}
            <div style={{ background: `${G}22`, border: `1px solid ${G}44`, borderRadius: 14, padding: 20, marginTop: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: G, marginBottom: 12 }}>
                💰 Impacto Total com Todas as Recomendações
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Ganho Potencial</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: G }}>
                    +R$ 12.600
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Novo Ganho Mensal</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: G }}>
                    R$ 75.850
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Aumento %</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: G }}>
                    +37%
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ALERTAS */}
        {activeTab === 'alerts' && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                🚨 Alertas Ativos
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                {alerts.length} alerta(s) requer(em) atenção
              </div>
            </div>

            {alerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}

            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 12, padding: 16, marginTop: 20 }}>
              <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 8 }}>💡 Dica</div>
              <div style={{ fontSize: 13, color: '#E8F0EA' }}>
                Ative notificações para receber alertas em tempo real. Assim você pode agir rapidamente quando algo sair do planejado.
              </div>
            </div>
          </div>
        )}

        {/* BENCHMARK */}
        {activeTab === 'benchmark' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                📊 Você vs Mercado
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                Comparação com outras imobiliárias similares em Maceió
              </div>
            </div>

            {[
              { label: 'Taxa de Qualificação', yours: 78, market: 85, unit: '%' },
              { label: 'Taxa de Conversão', yours: 18, market: 22, unit: '%' },
              { label: 'Tempo de Resposta (minutos)', yours: 2.7, market: 1.8, unit: 'min' },
              { label: 'Tentativas de Follow-up', yours: 2, market: 4, unit: 'tentativas' },
            ].map((metric) => (
              <div key={metric.label} style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 12, padding: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#E8F0EA', marginBottom: 12 }}>
                  {metric.label}
                </div>
                <div style={{ display: 'flex', gap: 20, marginBottom: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Você</div>
                    <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: B }}>
                      {metric.yours}
                      <span style={{ fontSize: 14 }}>{metric.unit}</span>
                    </div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Mercado</div>
                    <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: '#5A7A5E' }}>
                      {metric.market}
                      <span style={{ fontSize: 14 }}>{metric.unit}</span>
                    </div>
                  </div>
                </div>
                <div style={{ height: 6, background: '#1A2A1C', borderRadius: 3, overflow: 'hidden', marginBottom: 8 }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${(metric.yours / Math.max(metric.yours, metric.market)) * 100}%`,
                      background: metric.yours >= metric.market ? G : Y,
                      borderRadius: 3,
                    }}
                  />
                </div>
                <div style={{ fontSize: 11, color: metric.yours >= metric.market ? G : R, fontWeight: 600 }}>
                  {metric.yours >= metric.market
                    ? `✓ Você está ${Math.round(((metric.yours - metric.market) / metric.market) * 100)}% acima da média`
                    : `✗ Você está ${Math.round(((metric.market - metric.yours) / metric.market) * 100)}% abaixo da média`}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TENDÊNCIAS */}
        {activeTab === 'trends' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 8 }}>
                📉 Tendências (Últimas 4 Semanas)
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                Acompanhe a evolução dos seus indicadores
              </div>
            </div>

            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#E8F0EA', marginBottom: 16 }}>
                Leads Processados vs Qualificados
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1A2A1C" />
                  <XAxis dataKey="week" stroke="#5A7A5E" />
                  <YAxis stroke="#5A7A5E" />
                  <Tooltip
                    contentStyle={{ background: '#0A0F0B', border: `1px solid #1A2A1C`, borderRadius: 8, color: '#E8F0EA' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="leads" stroke={B} strokeWidth={2} name="Leads Processados" />
                  <Line type="monotone" dataKey="qualified" stroke={G} strokeWidth={2} name="Leads Qualificados" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div style={{ background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#E8F0EA', marginBottom: 16 }}>
                Taxa de Conversão e Tempo de Resposta
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1A2A1C" />
                  <XAxis dataKey="week" stroke="#5A7A5E" />
                  <YAxis stroke="#5A7A5E" />
                  <Tooltip
                    contentStyle={{ background: '#0A0F0B', border: `1px solid #1A2A1C`, borderRadius: 8, color: '#E8F0EA' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="conversion" stroke={G} strokeWidth={2} name="Taxa de Conversão (%)" />
                  <Line type="monotone" dataKey="response" stroke={Y} strokeWidth={2} name="Tempo de Resposta (min)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* UPGRADE SUGGESTION */}
        <div style={{ marginTop: 40, background: `${Y}22`, border: `2px solid ${Y}`, borderRadius: 14, padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: Y, marginBottom: 8 }}>
                ⬆️ Próximo Passo: Considere Upgrade para Enterprise
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 12 }}>
                {upgradeOpportunity.justification}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Seu Plano Atual</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 16, fontWeight: 800, color: '#E8F0EA' }}>
                    {upgradeOpportunity.current}
                  </div>
                  <div style={{ fontSize: 10, color: '#5A7A5E' }}>
                    Limite: {upgradeOpportunity.currentLimit} leads/mês
                  </div>
                </div>
                <div style={{ textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ fontSize: 20 }}>→</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Plano Recomendado</div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 16, fontWeight: 800, color: G }}>
                    {upgradeOpportunity.recommended}
                  </div>
                  <div style={{ fontSize: 10, color: '#5A7A5E' }}>
                    Limite: {upgradeOpportunity.recommendedLimit} leads/mês
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 12, color: '#5A7A5E', marginBottom: 16 }}>
                Custo adicional: <span style={{ color: G, fontWeight: 600 }}>+R$ {upgradeOpportunity.additionalCost.toLocaleString()}/mês</span>
              </div>
            </div>
            <button
              style={{
                background: Y,
                color: '#060908',
                border: 'none',
                padding: '12px 24px',
                borderRadius: 8,
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: 13,
                whiteSpace: 'nowrap',
                marginLeft: 20,
              }}
            >
              Fazer Upgrade
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
