import api from './api'
const settingsApi = { global: () => api.get('/api/settings/global'), saveGlobal: settings => api.put('/api/settings/global', { settings }), user: () => api.get('/api/settings/user'), saveUser: settings => api.put('/api/settings/user', { settings }), test: provider => api.post('/api/settings/integrations/test', { provider }) }
export default settingsApi
