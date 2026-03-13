/**
 * Utilitários de formatação compartilhados entre os dashboards.
 */

/** Formata número com separador de milhar: 9450 → "9.450" */
export const fmt = (n) =>
    typeof n === 'number' ? n.toLocaleString('pt-BR') : (n ?? '—');

/** Formata moeda BRL: 9450 → "R$ 9.450" */
export const fmtBRL = (n) =>
    typeof n === 'number'
        ? `R$ ${n.toLocaleString('pt-BR')}`
        : '—';

/** Formata percentual: 85.5 → "85,5%" */
export const fmtPct = (n) =>
    typeof n === 'number' ? `${n.toLocaleString('pt-BR')}%` : '—';

/** Retorna cor semântica baseada no health score */
export const healthColor = (score) => {
    if (score >= 80) return '#00C853';
    if (score >= 60) return '#FFD600';
    return '#FF5252';
};

/** Retorna label de status */
export const statusLabel = (status) =>
    ({ active: 'Ativo', warning: 'Atenção', churned: 'Churn' }[status] ?? status);
