import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

export default function LeadModal({ isOpen, onClose, lead, onStatusChange }) {
    const [conversations, setConversations] = useState([]);
    const [loadingConv, setLoadingConv] = useState(false);
    const [status, setStatus] = useState(lead?.status || 'new');
    const [updating, setUpdating] = useState(false);

    useEffect(() => {
        if (isOpen && lead) {
            setStatus(lead.status || 'new');
            fetchConversations(lead.id);
        }
    }, [isOpen, lead]);

    const fetchConversations = async (leadId) => {
        setLoadingConv(true);
        try {
            const res = await fetch(`/api/leads/${leadId}/conversations`, { credentials: 'include' });
            const data = await res.json();
            setConversations(data.conversations || []);
        } catch {
            toast.error('Erro ao carregar histórico da conversa');
        } finally {
            setLoadingConv(false);
        }
    };

    const handleStatusChange = async (e) => {
        const newStatus = e.target.value;
        setStatus(newStatus);
        setUpdating(true);
        try {
            const res = await fetch(`/api/leads/${lead.id}/status`, {
                method: 'PATCH',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus }),
            });
            if (res.ok) {
                toast.success('Status atualizado com sucesso!');
                if (onStatusChange) onStatusChange(lead.id, newStatus);
            } else {
                toast.error('Erro ao atualizar status');
            }
        } catch {
            toast.error('Erro de conexão');
        } finally {
            setUpdating(false);
        }
    };

    if (!isOpen || !lead) return null;

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 9999, padding: 20
        }}>
            <div style={{
                background: '#0A0F0B', border: '1px solid #1A2A1C', borderRadius: 16,
                width: '100%', maxWidth: 700, maxHeight: '90vh',
                display: 'flex', flexDirection: 'column', overflow: 'hidden'
            }}>
                {/* Header Modal */}
                <div style={{ padding: '20px 24px', borderBottom: '1px solid #1A2A1C', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div style={{ fontSize: 18, fontWeight: 700, color: '#E8F0EA', fontFamily: "'Syne', sans-serif" }}>
                            Detalhes do Lead
                        </div>
                        <div style={{ fontSize: 13, color: '#5A7A5E', marginTop: 4 }}>Visualizando informações e histórico</div>
                    </div>
                    <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#5A7A5E', fontSize: 24, cursor: 'pointer' }}>
                        &times;
                    </button>
                </div>

                {/* Content */}
                <div style={{ padding: 24, overflowY: 'auto', flex: 1 }}>
                    {/* Card Principal do Lead */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                        {/* Infos Básico */}
                        <div style={{ background: '#0E1410', padding: 20, borderRadius: 12, border: '1px solid #1A2A1C' }}>
                            <div style={{ fontSize: 11, color: '#5A7A5E', textTransform: 'uppercase', marginBottom: 12 }}>Informações do Lead</div>
                            <div style={{ marginBottom: 12 }}>
                                <span style={{ color: '#5A7A5E', fontSize: 12, display: 'block' }}>Nome / Contato</span>
                                <span style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>{lead.name || lead.phone}</span>
                            </div>
                            <div style={{ marginBottom: 12 }}>
                                <span style={{ color: '#5A7A5E', fontSize: 12, display: 'block' }}>Classificação IA</span>
                                <span style={{
                                    fontSize: 12, padding: '2px 8px', borderRadius: 12, fontWeight: 600, textTransform: 'capitalize',
                                    background: lead.classification === 'hot' ? '#00C85322' : lead.classification === 'warm' ? '#FFD60022' : '#FF525222',
                                    color: lead.classification === 'hot' ? '#00C853' : lead.classification === 'warm' ? '#FFD600' : '#FF5252'
                                }}>
                                    {lead.classification || 'cold'}
                                </span>
                            </div>
                            <div>
                                <span style={{ color: '#5A7A5E', fontSize: 12, display: 'block' }}>Categoria</span>
                                <span style={{ fontSize: 14, color: '#E8F0EA', textTransform: 'capitalize' }}>{lead.category || 'Não definido'}</span>
                            </div>
                        </div>

                        {/* Controle de Status */}
                        <div style={{ background: '#0E1410', padding: 20, borderRadius: 12, border: '1px solid #1A2A1C' }}>
                            <div style={{ fontSize: 11, color: '#5A7A5E', textTransform: 'uppercase', marginBottom: 12 }}>Andamento do Lead</div>
                            <label style={{ color: '#5A7A5E', fontSize: 12, display: 'block', marginBottom: 8 }}>Mover para Fila:</label>
                            <select
                                value={status}
                                onChange={handleStatusChange}
                                disabled={updating}
                                style={{
                                    width: '100%', padding: '12px', borderRadius: 8, border: '1px solid #1A2A1C',
                                    background: '#060908', color: '#fff', fontSize: 14, outline: 'none', cursor: 'pointer'
                                }}
                            >
                                <option value="new">🆕 Novo (Não contatado)</option>
                                <option value="contacted">📞 Em contato (Andamento)</option>
                                <option value="converted">✅ Convertido (Fechou negócio)</option>
                                <option value="lost">❌ Perdido (Desistiu)</option>
                            </select>
                            <div style={{ marginTop: 12, fontSize: 11, color: '#5A7A5E' }}>
                                Atualizar esse status muda a conversão e o health score.
                            </div>
                        </div>
                    </div>

                    {/* Histórico da Conversa */}
                    <div style={{ marginTop: 24 }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 16 }}>💬 Histórico de Conversa</div>
                        <div style={{
                            background: '#0E1410', border: '1px solid #1A2A1C', borderRadius: 12,
                            padding: 20, minHeight: 150, maxHeight: 400, overflowY: 'auto',
                            display: 'flex', flexDirection: 'column', gap: 12
                        }}>
                            {loadingConv ? (
                                <div style={{ color: '#5A7A5E', textAlign: 'center', padding: 20, fontSize: 13 }}>Carregando histórico...</div>
                            ) : conversations.length === 0 ? (
                                <div style={{ color: '#5A7A5E', textAlign: 'center', padding: 20, fontSize: 13 }}>Não há histórico de conversa gravado.</div>
                            ) : (
                                conversations.map((msg, i) => {
                                    const isInbound = msg.direction === 'inbound';
                                    return (
                                        <div key={i} style={{
                                            display: 'flex', flexDirection: 'column',
                                            alignItems: isInbound ? 'flex-start' : 'flex-end'
                                        }}>
                                            <div style={{
                                                maxWidth: '80%', padding: '10px 14px', borderRadius: 12, fontSize: 13, lineHeight: '1.4',
                                                background: isInbound ? '#1A2A1C' : '#00C853',
                                                color: isInbound ? '#E8F0EA' : '#060908',
                                                borderBottomLeftRadius: isInbound ? 2 : 12,
                                                borderBottomRightRadius: isInbound ? 12 : 2
                                            }}>
                                                {msg.message}
                                            </div>
                                            <div style={{ fontSize: 10, color: '#5A7A5E', marginTop: 4 }}>
                                                {new Date(msg.created_at).toLocaleString('pt-BR')}
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div style={{ padding: '16px 24px', borderTop: '1px solid #1A2A1C', background: '#0E1410', textAlign: 'right' }}>
                    <button onClick={onClose} style={{
                        background: 'transparent', color: '#fff', padding: '10px 20px', borderRadius: 8,
                        border: '1px solid #1A2A1C', cursor: 'pointer', fontWeight: 600, fontSize: 13
                    }}>
                        Fechar
                    </button>
                </div>
            </div>
        </div>
    );
}
