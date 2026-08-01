import api from './api'
const sslApi = { list: (params = {}) => { const q = new URLSearchParams(); Object.entries(params).forEach(([k, v]) => v !== undefined && v !== '' && q.set(k, v)); return api.get(`/api/ssl-analysis?${q}`) }, stats: () => api.get('/api/ssl-analysis/stats'), get: (id) => api.get(`/api/ssl-analysis/${id}`) }
export default sslApi
