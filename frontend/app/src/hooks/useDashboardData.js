/**
 * useDashboardData — busca dados reais da API Flask
 * Retorna dados para o admin e para o cliente logado.
 */
import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';

// ── Admin ──────────────────────────────────────────────────────────────────
export function useAdminDashboard() {
    const [clients, setClients] = useState([]);
    const [overview, setOverview] = useState(null);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [clientsRes, overviewRes] = await Promise.all([
                fetch('/api/clients/', { credentials: 'include' }),
                fetch('/api/dashboard/admin/overview', { credentials: 'include' }),
            ]);

            if (!clientsRes.ok || !overviewRes.ok) {
                throw new Error('Erro ao carregar dados');
            }

            const clientsData = await clientsRes.json();
            const overviewData = await overviewRes.json();

            // Normaliza campos — health vem calculado pelo backend
            const normalized = (clientsData.clients || []).map(c => ({
                id: c.id,
                name: c.name,
                niche: c.niche || 'Geral',
                mrr: c.mrr || 0,
                leads: c.total_leads || 0,
                health: c.health ?? 50,   // calculado via health_score.py
                churnRisk: c.churn_risk ?? 25,
                healthLabel: c.health_label || 'Atenção',
                status: c.status || 'active',
                package: c.package || 'pro',
                username: c.username || '',
                whatsapp_number: c.whatsapp_number || '',
                phone: c.phone || '',
                email: c.email || '',
                since: c.created_at
                    ? new Date(c.created_at).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })
                    : '—',
                // Cor baseada no health calculado (não mais hardcoded)
                color: (c.health ?? 50) >= 80 ? '#00C853'
                    : (c.health ?? 50) >= 60 ? '#FFD600'
                        : '#FF5252',
            }));

            setClients(normalized);
            setOverview(overviewData);
        } catch (err) {
            toast.error('Falha ao carregar dados. Usando dados demo.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    return { clients, overview, loading, reload: load };
}

// ── Run Health Check (admin) ──────────────────────────────────────────────
export async function runHealthCheck() {
    const res = await fetch('/api/dashboard/admin/run-health-check', {
        method: 'POST',
        credentials: 'include',
    });
    return res.json();
}

// ── Health History de um cliente ──────────────────────────────────────────
export function useHealthHistory(clientId) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);

    const load = useCallback(async () => {
        if (!clientId) return;
        setLoading(true);
        try {
            const res = await fetch(
                `/api/dashboard/admin/clients/${clientId}/history?weeks=12`,
                { credentials: 'include' }
            );
            if (res.ok) {
                const d = await res.json();
                setHistory(d.history || []);
            }
        } catch (e) {
            console.error('Histórico de health:', e);
        } finally {
            setLoading(false);
        }
    }, [clientId]);

    useEffect(() => { load(); }, [load]);
    return { history, loading };
}

// ── Cliente ────────────────────────────────────────────────────────────────
export function useClientDashboard(clientId) {
    const [data, setData] = useState(null);
    const [leads, setLeads] = useState([]);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        if (!clientId) return;
        setLoading(true);
        try {
            const [overviewRes, leadsRes] = await Promise.all([
                fetch(`/api/dashboard/client/${clientId}/overview`, { credentials: 'include' }),
                fetch(`/api/leads/?client_id=${clientId}&limit=100`, { credentials: 'include' }),
            ]);
            if (!overviewRes.ok || !leadsRes.ok) throw new Error('Erro ao carregar dados do cliente');

            const overviewData = await overviewRes.json();
            const leadsData = await leadsRes.json();

            setData(overviewData);
            setLeads(leadsData.leads || []);
        } catch (err) {
            toast.error('Falha ao carregar seus dados.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [clientId]);

    useEffect(() => { load(); }, [load]);

    return { data, leads, loading, reload: load };
}
