/**
 * ConfirmDialog — Modal de confirmação reutilizável
 * Substitui window.confirm() com UX consistente ao tema MFL.
 *
 * Props:
 *   isOpen    {boolean}   — controla visibilidade
 *   title     {string}    — título do modal
 *   message   {string}    — corpo da confirmação
 *   onConfirm {function}  — callback ao confirmar
 *   onCancel  {function}  — callback ao cancelar
 *   variant   {'danger'|'warning'}  — cor do botão de ação (default: 'danger')
 *   confirmLabel {string} — texto do botão de confirmação
 */
import React from 'react';

const G = '#00C853';
const R = '#FF5252';
const Y = '#FFD600';

export default function ConfirmDialog({
    isOpen,
    title = 'Confirmar ação',
    message = 'Tem certeza?',
    onConfirm,
    onCancel,
    variant = 'danger',
    confirmLabel = 'Confirmar',
}) {
    if (!isOpen) return null;

    const accentColor = variant === 'warning' ? Y : R;

    return (
        /* Overlay */
        <div
            onClick={onCancel}
            style={{
                position: 'fixed',
                inset: 0,
                zIndex: 2000,
                background: 'rgba(0,0,0,0.75)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backdropFilter: 'blur(4px)',
                animation: 'fadeIn 0.15s ease',
            }}
        >
            {/* Caixa do modal */}
            <div
                onClick={(e) => e.stopPropagation()}
                style={{
                    background: '#0A0F0B',
                    border: `1px solid ${accentColor}44`,
                    borderRadius: 18,
                    padding: 32,
                    width: '100%',
                    maxWidth: 420,
                    boxShadow: `0 24px 80px ${accentColor}18`,
                    animation: 'slideUp 0.2s ease',
                }}
            >
                {/* Ícone */}
                <div style={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    background: `${accentColor}18`,
                    border: `2px solid ${accentColor}44`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 22,
                    marginBottom: 20,
                }}>
                    {variant === 'warning' ? '⚠️' : '🗑️'}
                </div>

                {/* Título */}
                <div style={{
                    fontFamily: "'Syne', sans-serif",
                    fontSize: 18,
                    fontWeight: 800,
                    color: '#fff',
                    marginBottom: 10,
                }}>
                    {title}
                </div>

                {/* Mensagem */}
                <div style={{
                    fontSize: 14,
                    color: '#5A7A5E',
                    lineHeight: 1.6,
                    marginBottom: 28,
                }}>
                    {message}
                </div>

                {/* Botões */}
                <div style={{ display: 'flex', gap: 12 }}>
                    {/* Cancelar */}
                    <button
                        onClick={onCancel}
                        style={{
                            flex: 1,
                            padding: '12px',
                            background: 'transparent',
                            border: '1px solid #1A2A1C',
                            borderRadius: 10,
                            color: '#5A7A5E',
                            fontSize: 14,
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontFamily: "'DM Sans', sans-serif",
                            transition: 'border-color 0.15s, color 0.15s',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = '#2A3A2C';
                            e.currentTarget.style.color = '#E8F0EA';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = '#1A2A1C';
                            e.currentTarget.style.color = '#5A7A5E';
                        }}
                    >
                        Cancelar
                    </button>

                    {/* Confirmar */}
                    <button
                        onClick={onConfirm}
                        style={{
                            flex: 2,
                            padding: '12px',
                            background: accentColor,
                            border: 'none',
                            borderRadius: 10,
                            color: '#060908',
                            fontSize: 14,
                            fontWeight: 700,
                            cursor: 'pointer',
                            fontFamily: "'DM Sans', sans-serif",
                            transition: 'opacity 0.15s, transform 0.1s',
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.88'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
                        onMouseDown={(e) => { e.currentTarget.style.transform = 'scale(0.98)'; }}
                        onMouseUp={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
                    >
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}
