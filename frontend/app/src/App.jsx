import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './hooks/useAuth.jsx';
import LoginPage from './pages/LoginPage';
import AdminDashboardOtimizado from './pages/DashboardAdmin';
import ClientDashboardOtimizado from './pages/DashboardCliente';

// ── Rota protegida — redireciona para /login se não autenticado ──────────────
function ProtectedRoute({ children, requiredRole }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#080C0A',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#00C853',
        fontFamily: "'DM Sans', sans-serif",
        fontSize: 16,
        gap: 12,
      }}>
        <div style={{
          width: 8, height: 8,
          background: '#00C853',
          borderRadius: '50%',
          animation: 'pulse 1.5s infinite',
        }} />
        Carregando...
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  if (requiredRole === 'admin' && user.role !== 'admin') {
    return <Navigate to="/cliente" replace />;
  }

  return children;
}

// ── Redireciona a raiz conforme a role ───────────────────────────────────────
function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === 'admin' ? '/admin' : '/cliente'} replace />;
}

// ── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0E1410',
            color: '#E8F0EA',
            border: '1px solid #1A2A1C',
            fontFamily: "'DM Sans', sans-serif",
            fontSize: 14,
          },
          success: { iconTheme: { primary: '#00C853', secondary: '#060908' } },
          error: { iconTheme: { primary: '#FF5252', secondary: '#060908' } },
        }}
      />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<RootRedirect />} />

          <Route
            path="/admin"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminDashboardOtimizado />
              </ProtectedRoute>
            }
          />

          <Route
            path="/cliente"
            element={
              <ProtectedRoute requiredRole="client">
                <ClientDashboardOtimizado />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
