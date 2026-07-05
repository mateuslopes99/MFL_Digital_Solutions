// Configuração central da API
// Em produção usa a URL do Render; em dev usa localhost
const API_BASE = import.meta.env.VITE_API_URL || 'https://mfl-backend.onrender.com';

export default API_BASE;
