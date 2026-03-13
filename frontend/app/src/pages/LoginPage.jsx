import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.jsx';

export default function LoginPage() {
    const [role, setRole] = useState('client');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login, user } = useAuth();
    const navigate = useNavigate();

    // Navega assim que o user for atualizado no contexto (resolve timing do setState)
    useEffect(() => {
        if (user) {
            navigate(user.role === 'admin' ? '/admin' : '/cliente', { replace: true });
        }
    }, [user, navigate]);

    const G = '#00C853';

    async function handleSubmit(e) {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await login(username, password, role);
        setLoading(false);

        if (!result.success) {
            setError(result.error || 'Credenciais inválidas');
        }
        // navegação é feita pelo useEffect acima quando user state atualizar
    }

    return (
        <div style={{
            minHeight: '100vh',
            background: '#080C0A',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: "'DM Sans', sans-serif",
            color: '#E8F0EA',
        }}>
            {/* Glow de fundo */}
            <div style={{
                position: 'fixed',
                top: '20%',
                left: '50%',
                transform: 'translateX(-50%)',
                width: 500,
                height: 300,
                background: 'radial-gradient(ellipse, rgba(0,200,83,0.08), transparent)',
                pointerEvents: 'none',
                zIndex: 0,
            }} />

            <div style={{
                position: 'relative',
                zIndex: 1,
                background: '#0E1410',
                border: '1px solid #1A2A1C',
                borderRadius: 16,
                padding: '40px',
                width: '100%',
                maxWidth: 400,
                boxShadow: '0 24px 60px rgba(0,0,0,0.6)',
            }}>
                {/* Logo */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: 32,
                }}>
                    <img
                        src="/mfl_logo_primary.png"
                        alt="MFL Digital Solutions"
                        style={{ height: 200, objectFit: 'contain' }}
                    />
                </div>

                <form onSubmit={handleSubmit}>
                    {/* Tipo de Acesso */}
                    <div style={{ marginBottom: 20 }}>
                        <label style={{ display: 'block', fontSize: 12, color: '#5A7A5E', marginBottom: 8 }}>
                            Tipo de Acesso
                        </label>
                        <div style={{ display: 'flex', gap: 8 }}>
                            {[
                                { value: 'client', label: '👤 Cliente' },
                                { value: 'admin', label: '⚡ Admin' },
                            ].map(({ value, label }) => (
                                <button
                                    key={value}
                                    type="button"
                                    onClick={() => setRole(value)}
                                    style={{
                                        flex: 1,
                                        padding: '10px',
                                        borderRadius: 8,
                                        border: `1px solid ${role === value ? G : '#1A2A1C'}`,
                                        background: role === value ? `${G}15` : '#1A2A1C',
                                        color: role === value ? G : '#5A7A5E',
                                        fontWeight: 600,
                                        fontSize: 13,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        fontFamily: "'DM Sans', sans-serif",
                                    }}
                                >
                                    {label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Usuário */}
                    <div style={{ marginBottom: 16 }}>
                        <label style={{ display: 'block', fontSize: 12, color: '#5A7A5E', marginBottom: 8 }}>
                            Usuário
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            placeholder={role === 'admin' ? 'admin' : 'seu_usuario'}
                            required
                            style={{
                                width: '100%',
                                background: '#1A2A1C',
                                border: '1px solid #2A3A2C',
                                color: '#E8F0EA',
                                padding: '12px 16px',
                                borderRadius: 8,
                                fontSize: 14,
                                outline: 'none',
                                fontFamily: "'DM Sans', sans-serif",
                                boxSizing: 'border-box',
                            }}
                            onFocus={e => e.target.style.borderColor = G}
                            onBlur={e => e.target.style.borderColor = '#2A3A2C'}
                        />
                    </div>

                    {/* Senha */}
                    <div style={{ marginBottom: 24 }}>
                        <label style={{ display: 'block', fontSize: 12, color: '#5A7A5E', marginBottom: 8 }}>
                            Senha
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            style={{
                                width: '100%',
                                background: '#1A2A1C',
                                border: '1px solid #2A3A2C',
                                color: '#E8F0EA',
                                padding: '12px 16px',
                                borderRadius: 8,
                                fontSize: 14,
                                outline: 'none',
                                fontFamily: "'DM Sans', sans-serif",
                                boxSizing: 'border-box',
                            }}
                            onFocus={e => e.target.style.borderColor = G}
                            onBlur={e => e.target.style.borderColor = '#2A3A2C'}
                        />
                    </div>

                    {/* Erro */}
                    {error && (
                        <div style={{
                            background: 'rgba(255,61,0,0.1)',
                            border: '1px solid rgba(255,61,0,0.3)',
                            borderRadius: 8,
                            padding: '10px 14px',
                            fontSize: 13,
                            color: '#FF5252',
                            marginBottom: 16,
                        }}>
                            ⚠️ {error}
                        </div>
                    )}

                    {/* Botão */}
                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            width: '100%',
                            padding: '14px',
                            background: loading ? '#1A2A1C' : G,
                            color: loading ? '#5A7A5E' : '#060908',
                            border: 'none',
                            borderRadius: 8,
                            fontFamily: "'Syne', sans-serif",
                            fontWeight: 700,
                            fontSize: 15,
                            cursor: loading ? 'not-allowed' : 'pointer',
                            transition: 'all 0.2s',
                        }}
                    >
                        {loading ? 'Autenticando...' : 'Entrar →'}
                    </button>
                </form>

                <p style={{ textAlign: 'center', fontSize: 11, color: '#2A3A2C', marginTop: 24 }}>
                    MFL Digital Solutions · Painel Seguro
                </p>
            </div>
        </div>
    );
}
