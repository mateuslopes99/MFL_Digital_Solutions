/**
 * RiskClientModal — Detalhes de um cliente em risco de churn
 *
 * Props:
 *   client  {object|null}  — objeto do cliente (null = fechado)
 *   onClose {function}     — fechar o modal
 */
import React from 'react';
import { fmt } from '../utils/format.js';

const G = '#00C853';
const R = '#FF5252';
const Y = '#FFD600';
const B = '#2196F3';

// Gera sugestões de ação baseadas no health score
function getActions(client) {
    const actions = [];
    if (client.health < 50) {
        actions.push({
            icon: '📞',
            label: 'Ligar agora',
            description: 'Health crítico — contato imediato necessário.',
            urgency: 'critical',
        });
    }
    if (client.churnRisk >= 50) {
        actions.push({
            icon: '🎁',
            label: 'Oferecer desconto de retenção',
            description: `Risco de perder R$ ${fmt(client.mrr)}/mês. Um desconto de 15% custa menos que o churn.`,
            urgency: 'high',
        });
    }
    actions.push({
        icon: '📋',
        label: 'Agendar call de sucesso',
        description: 'Sessão de 30 min para entender os pontos de atrito.',
        urgency: 'medium',
    });
    actions.push({
        icon: '📊',
        label: 'Enviar relatório de valor',
        description: 'Mostrar ROI acumulado desde o início da parceria.',
        urgency: 'low',
    });
    return actions;
}

const urgencyColors = {
    critical: R,
    high: Y,
    medium: B,
    low: '#3A4A3C',
};

export default function RiskClientModal({ client, onClose }) {
    if (!client) return null;

    const actions = getActions(client);
    const mrrAtRisk = Math.round(client.mrr * (client.churnRisk / 100));
    const healthClr = client.health >= 60 ? Y : R;

    return (
        /* Overlay */
        <div
            onClick={onClose}
            style={{
                position: 'fixed',
                inset: 0,
                zIndex: 1500,
                background: 'rgba(0,0,0,0.80)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backdropFilter: 'blur(6px)',
            }}
        >
            {/* Modal */}
            <div
                onClick={(e) => e.stopPropagation()}
                style={{
                    background: '#0A0F0B',
                    border: `1px solid ${R}44`,
                    borderRadius: 20,
                    width: '100%',
                    maxWidth: 540,
                    maxHeight: '90vh',
                    overflowY: 'auto',
                    boxShadow: `0 32px 100px ${R}20`,
                }}
            >
                {/* ─── Header com gradiente de risco ─── */}
                <div style={{
                    padding: '28px 28px 20px',
                    borderBottom: `1px solid ${R}22`,
                    background: `linear-gradient(135deg, ${R}10 0%, transparent 70%)`,
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                            {/* Avatar */}
                            <div style={{
                                width: 48, height: 48, borderRadius: '50%',
                                background: `${R}22`, border: `2px solid ${R}`,
                                display: 'flex', alignItems: 'center',
                                justifyContent: 'center', fontSize: 22, flexShrink: 0,
                            }}>
                                {client.niche === 'Imobiliária' ? '🏠'
                                    : client.niche?.includes('Estética') ? '💆'
                                        : client.niche?.includes('Consultório') ? '🏥' : '🏢'}
                            </div>
                            <div>
                                <div style={{
                                    fontFamily: "'Syne', sans-serif",
                                    fontSize: 20, fontWeight: 800, color: '#fff', marginBottom: 4,
                                }}>
                                    {client.name}
                                </div>
                                <div style={{ fontSize: 12, color: '#5A7A5E' }}>
                                    {client.niche} · Cliente desde {client.since}
                                </div>
                            </div>
                        </div>

                        {/* Badge de risco + fechar */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{
                                fontSize: 12, fontWeight: 700,
                                padding: '5px 14px', borderRadius: 100,
                                background: `${R}22`, color: R,
                            }}>
                                ⚠️ {client.churnRisk}% risco
                            </span>
                            <button
                                onClick={onClose}
                                style={{
                                    background: 'none', border: 'none',
                                    color: '#5A7A5E', fontSize: 22,
                                    cursor: 'pointer', lineHeight: 1, padding: 4,
                                }}
                            >
                                ✕
                            </button>
                        </div>
                    </div>
                </div>

                <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 20 }}>

                    {/* ─── KPIs ─── */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                        {/* Health */}
                        <div style={{
                            background: '#0E1410', border: `1px solid ${healthClr}44`,
                            borderRadius: 12, padding: 16, textAlign: 'center',
                        }}>
                            <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 8 }}>Health Score</div>
                            <div style={{
                                fontFamily: "'Syne', sans-serif",
                                fontSize: 32, fontWeight: 800, color: healthClr, marginBottom: 8,
                            }}>
                                {client.health}%
                            </div>
                            {/* Barra de health */}
                            <div style={{ height: 4, background: '#1A2A1C', borderRadius: 2, overflow: 'hidden' }}>
                                <div style={{
                                    height: '100%', width: `${client.health}%`,
                                    background: healthClr, borderRadius: 2,
                                    transition: 'width 0.6s ease',
                                }} />
                            </div>
                        </div>

                        {/* MRR */}
                        <div style={{
                            background: '#0E1410', border: '1px solid #1A2A1C',
                            borderRadius: 12, padding: 16, textAlign: 'center',
                        }}>
                            <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 8 }}>MRR</div>
                            <div style={{
                                fontFamily: "'Syne', sans-serif",
                                fontSize: 24, fontWeight: 800, color: G,
                            }}>
                                R$ {fmt(client.mrr)}
                            </div>
                            <div style={{ fontSize: 10, color: '#5A7A5E', marginTop: 6 }}>/mês</div>
                        </div>

                        {/* MRR em risco */}
                        <div style={{
                            background: '#0E1410', border: `1px solid ${R}33`,
                            borderRadius: 12, padding: 16, textAlign: 'center',
                        }}>
                            <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 8 }}>MRR em Risco</div>
                            <div style={{
                                fontFamily: "'Syne', sans-serif",
                                fontSize: 24, fontWeight: 800, color: R,
                            }}>
                                R$ {fmt(mrrAtRisk)}
                            </div>
                            <div style={{ fontSize: 10, color: '#5A7A5E', marginTop: 6 }}>estimado</div>
                        </div>
                    </div>

                    {/* ─── Métricas secundárias ─── */}
                    <div style={{
                        background: '#0E1410', border: '1px solid #1A2A1C',
                        borderRadius: 12, padding: 16,
                        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16,
                    }}>
                        <div>
                            <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Leads / mês</div>
                            <div style={{
                                fontFamily: "'Syne', sans-serif",
                                fontSize: 20, fontWeight: 700, color: B,
                            }}>
                                {client.leads}
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: 11, color: '#5A7A5E', marginBottom: 4 }}>Taxa de Conversão</div>
                            <div style={{
                                fontFamily: "'Syne', sans-serif",
                                fontSize: 20, fontWeight: 700,
                                color: client.conversion >= 15 ? G : Y,
                            }}>
                                {client.conversion}%
                            </div>
                        </div>
                    </div>

                    {/* ─── Ações recomendadas ─── */}
                    <div>
                        <div style={{
                            fontSize: 13, fontWeight: 700, color: '#fff',
                            marginBottom: 12,
                        }}>
                            🎯 Ações Recomendadas
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {actions.map((action, idx) => (
                                <div
                                    key={idx}
                                    style={{
                                        background: '#0E1410',
                                        border: `1px solid ${urgencyColors[action.urgency]}33`,
                                        borderLeft: `3px solid ${urgencyColors[action.urgency]}`,
                                        borderRadius: 10,
                                        padding: '12px 16px',
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        gap: 12,
                                        cursor: 'default',
                                    }}
                                >
                                    <span style={{ fontSize: 18, flexShrink: 0, marginTop: 1 }}>
                                        {action.icon}
                                    </span>
                                    <div>
                                        <div style={{
                                            fontSize: 13, fontWeight: 600,
                                            color: '#E8F0EA', marginBottom: 3,
                                        }}>
                                            {action.label}
                                        </div>
                                        <div style={{ fontSize: 11, color: '#5A7A5E' }}>
                                            {action.description}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* ─── Botão principal de ação ─── */}
                    <button
                        onClick={onClose}
                        style={{
                            width: '100%',
                            padding: '14px',
                            background: R,
                            border: 'none',
                            borderRadius: 12,
                            color: '#fff',
                            fontSize: 14,
                            fontWeight: 700,
                            cursor: 'pointer',
                            fontFamily: "'DM Sans', sans-serif",
                            letterSpacing: 0.3,
                            transition: 'opacity 0.15s',
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.88'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
                    >
                        📞 Fechar e Agendar Contato
                    </button>
                </div>
            </div>
        </div>
    );
}
