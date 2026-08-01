import api from './api'

const dnsApi = {
  list: (params = {}) => { const q = new URLSearchParams(); Object.entries(params).forEach(([k, v]) => v !== undefined && v !== '' && q.set(k, v)); return api.get(`/api/dns-records?${q.toString()}`) },
  stats: () => api.get('/api/dns-records/stats'),
  get: (id) => api.get(`/api/dns-records/${id}`),
}
export default dnsApi
