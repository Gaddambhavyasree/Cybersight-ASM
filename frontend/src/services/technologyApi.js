import api from './api'
const technologyApi = { list: (params = {}) => { const q = new URLSearchParams(); Object.entries(params).forEach(([k, v]) => v !== undefined && v !== '' && q.set(k, v)); return api.get(`/api/technologies?${q.toString()}`) }, stats: () => api.get('/api/technologies/stats') }
export default technologyApi
