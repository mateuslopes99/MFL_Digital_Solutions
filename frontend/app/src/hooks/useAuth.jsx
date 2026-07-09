/**
 * useAuth — hook de autenticação MFL
 * Consulta /api/auth/me e expõe o usuário atual + funções de login/logout
 */
import { useState, useEffect, createContext, useContext } from 'react';

const AuthContext = createContext(null);
import API_BASE from '../utils/api';

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Verifica sessão ao montar
    useEffect(() => {
        const token = localStorage.getItem('mfl_token');
        if (!token) {
            setUser(null);
            setLoading(false);
            return;
        }

        fetch(`${API_BASE}/api/auth/me`, { 
            headers: { 'Authorization': `Bearer ${token}` }
        })
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                setUser(data?.authenticated ? data : null);
                setLoading(false);
            })
            .catch(() => {
                setUser(null);
                setLoading(false);
            });
    }, []);

    async function login(username, password, role) {
        try {
            const res = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, role }),
            });
            const data = await res.json();
            if (res.ok && data.success) {
                if (data.token) {
                    localStorage.setItem('mfl_token', data.token);
                }
                setUser({ ...data, authenticated: true });
                return { success: true, role: data.role };
            }
            return { success: false, error: data.error || 'Credenciais inválidas' };
        } catch (e) {
            return { success: false, error: 'Servidor offline. Inicie o Flask.' };
        }
    }

    async function logout() {
        await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST' });
        localStorage.removeItem('mfl_token');
        setUser(null);
    }

    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
