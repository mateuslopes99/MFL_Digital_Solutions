/**
 * ClientModal — Modal de Criar / Editar Cliente
 * Conecta com POST /api/clients/ e PUT /api/clients/:id
 */
import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

const G = '#00C853';
const R = '#FF5252';

const NICHES = ['Imobiliária', 'Consultório', 'Estética', 'E-commerce', 'Advocacia', 'Educação', 'Restaurante', 'Outro'];
const PLANS = [
    { key: 'starter', label: 'Starter — R$ 790/mês' },
    { key: 'basico', label: 'Básico — R$ 1.490/mês' },
    { key: 'pro', label: 'Pro — R$ 2.790/mês' },
    { key: 'enterprise', label: 'Enterprise — R$ 5.490/mês' },
];

const EMPTY = {
    name: '', niche: 'Imobiliária', phone: '', email: '',
    package: 'pro', username: '', whatsapp_number: '',
};

export default function ClientModal({ isOpen, onClose, onSaved, editClient = null }) {
    const isEdit = !!editClient;
    const [form, setForm] = useState(EMPTY);
    const [loading, setLoading] = useState(false);

    // Preenche o formulário ao abrir no modo edição
    useEffect(() => {
        if (isOpen) {
            setForm(editClient
                ? {
                    name: editClient.name || '',
                    niche: editClient.niche || 'Imobiliária',
                    phone: editClient.phone || '',
                    email: editClient.email || '',
                    package: editClient.package || 'pro',
                    username: editClient.username || '',
                    whatsapp_number: editClient.whatsapp_number || '',
                }
                : EMPTY
            );
        }
    }, [isOpen, editClient]);

    if (!isOpen) return null;

    const set = (key) => (e) => setForm(f => ({ ...f, [key]: e.target.value }));

    // Auto-gera username a partir do nome (apenas criação)
    const handleNameBlur = () => {
        if (!isEdit && !form.username && form.name) {
            const slug = form.name.toLowerCase()
                .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                .replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '');
            setForm(f => ({ ...f, username: slug }));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!form.name.trim()) return toast.error('Nome é obrigatório');
        if (!form.username.trim()) return toast.error('Username é obrigatório');

        setLoading(true);
        try {
            const url = isEdit ? `/api/clients/${editClient.id}` : '/api/clients/';
            const method = isEdit ? 'PUT' : 'POST';

            const res = await fetch(url, {
                method,
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            });
            const data = await res.json();

            if (!res.ok) {
                toast.error(data.error || 'Erro ao salvar cliente');
                return;
            }

            if (!isEdit && data.password) {
                toast.success(
                    `✅ Cliente criado!\nLogin: ${data.username}\nSenha: ${data.password}`,
                    { duration: 8000 }
                );
            } else {
                toast.success(isEdit ? 'Cliente atualizado!' : 'Cliente criado!');
            }

            onSaved?.();
            onClose();
        } catch (err) {
            toast.error('Erro de conexão');
        } finally {
            setLoading(false);
        }
    };

    // ── Estilos ──────────────────────────────────────────────────────────────────
    const fieldStyle = {
        width: '100%', background: '#0E1410', border: '1px solid #1A2A1C',
        borderRadius: 8, padding: '10px 14px', color: '#E8F0EA',
        fontSize: 14, fontFamily: "'DM Sans', sans-serif", boxSizing: 'border-box',
        outline: 'none',
    };
    const labelStyle = { fontSize: 12, color: '#5A7A5E', marginBottom: 6, display: 'block', fontWeight: 600 };

    return (
        // Overlay
        <div
            onClick={onClose}
            style={{
                position: 'fixed', inset: 0, zIndex: 1000,
                background: 'rgba(0,0,0,0.75)', display: 'flex',
                alignItems: 'center', justifyContent: 'center',
                backdropFilter: 'blur(4px)',
            }}
        >
            {/* Modal */}
            <div
                onClick={e => e.stopPropagation()}
                style={{
                    background: '#0A0F0B', border: '1px solid #1A2A1C',
                    borderRadius: 18, padding: 32, width: '100%', maxWidth: 520,
                    maxHeight: '90vh', overflowY: 'auto',
                    boxShadow: '0 24px 80px rgba(0,200,83,0.08)',
                }}
            >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
                    <div>
                        <div style={{ fontFamily: "'Syne', sans-serif", fontSize: 20, fontWeight: 800, color: '#fff' }}>
                            {isEdit ? '✏️ Editar Cliente' : '➕ Novo Cliente'}
                        </div>
                        <div style={{ fontSize: 12, color: '#5A7A5E', marginTop: 4 }}>
                            {isEdit ? 'Atualize os dados do cliente' : 'Será criado com senha padrão temporária'}
                        </div>
                    </div>
                    <button onClick={onClose} style={{
                        background: 'none', border: 'none', color: '#5A7A5E',
                        fontSize: 22, cursor: 'pointer', lineHeight: 1,
                    }}>✕</button>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

                    {/* Nome */}
                    <div>
                        <label style={labelStyle}>Nome da empresa *</label>
                        <input
                            style={fieldStyle} value={form.name} required
                            onChange={set('name')} onBlur={handleNameBlur}
                            placeholder="Ex: Silva & Cia Imóveis"
                        />
                    </div>

                    {/* Nicho + Plano */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <div>
                            <label style={labelStyle}>Nicho</label>
                            <select style={fieldStyle} value={form.niche} onChange={set('niche')}>
                                {NICHES.map(n => <option key={n} value={n}>{n}</option>)}
                            </select>
                        </div>
                        <div>
                            <label style={labelStyle}>Plano</label>
                            <select style={fieldStyle} value={form.package} onChange={set('package')}>
                                {PLANS.map(p => <option key={p.key} value={p.key}>{p.label}</option>)}
                            </select>
                        </div>
                    </div>

                    {/* Telefone + Email */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <div>
                            <label style={labelStyle}>Telefone</label>
                            <input
                                style={fieldStyle} value={form.phone}
                                onChange={set('phone')} placeholder="(82) 99999-9999"
                            />
                        </div>
                        <div>
                            <label style={labelStyle}>E-mail</label>
                            <input
                                style={fieldStyle} type="email" value={form.email}
                                onChange={set('email')} placeholder="email@empresa.com"
                            />
                        </div>
                    </div>

                    {/* Username */}
                    <div>
                        <label style={labelStyle}>Username para login *</label>
                        <input
                            style={fieldStyle} value={form.username} required
                            onChange={set('username')} placeholder="silva_cia"
                            disabled={isEdit}
                        />
                        {!isEdit && (
                            <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
                                Gerado automaticamente. Senha padrão: <strong style={{ color: G }}>mfl2026</strong>
                            </div>
                        )}
                    </div>

                    {/* WhatsApp Number (Twilio) */}
                    <div>
                        <label style={labelStyle}>Número WhatsApp Twilio</label>
                        <input
                            style={fieldStyle} value={form.whatsapp_number}
                            onChange={set('whatsapp_number')} placeholder="whatsapp:+5582999999999"
                        />
                        <div style={{ fontSize: 11, color: '#5A7A5E', marginTop: 4 }}>
                            Número do Twilio associado a este cliente (para receber leads)
                        </div>
                    </div>

                    {/* Botões */}
                    <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                        <button
                            type="button" onClick={onClose}
                            style={{
                                flex: 1, padding: '12px', background: 'transparent',
                                border: '1px solid #1A2A1C', borderRadius: 10, color: '#5A7A5E',
                                fontSize: 14, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif",
                            }}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit" disabled={loading}
                            style={{
                                flex: 2, padding: '12px', background: G, border: 'none',
                                borderRadius: 10, color: '#060908', fontSize: 14, fontWeight: 700,
                                cursor: loading ? 'not-allowed' : 'pointer',
                                fontFamily: "'DM Sans', sans-serif",
                                opacity: loading ? 0.7 : 1, transition: 'opacity 0.2s',
                            }}
                        >
                            {loading ? 'Salvando...' : isEdit ? 'Salvar Alterações' : 'Criar Cliente'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
