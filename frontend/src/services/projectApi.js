import api from './api'

const projectApi = {
  list: (params = {}) => {
    const query = new URLSearchParams()
    if (params.page) query.set('page', params.page)
    if (params.per_page) query.set('per_page', params.per_page)
    if (params.search) query.set('search', params.search)
    if (params.status) query.set('status', params.status)
    return api.get(`/api/projects?${query.toString()}`)
  },

  get: (id) => api.get(`/api/projects/${id}`),

  create: (data) => api.post('/api/projects', data),

  update: (id, data) => api.put(`/api/projects/${id}`, data),

  delete: (id) => api.delete(`/api/projects/${id}`),
}

export default projectApi
