import api from './api'
const notificationApi = {
  list: (params = {}) => api.get('/api/notifications', { params }),
  unread: () => api.get('/api/notifications/unread-count'),
  read: (id) => api.patch(`/api/notifications/${id}/read`),
  readAll: () => api.patch('/api/notifications/read-all'),
  remove: (id) => api.delete(`/api/notifications/${id}`),
  deleteRead: () => api.delete('/api/notifications/read'),
}
export default notificationApi
