import api from './api'
const webApi={list:(p={})=>{const q=new URLSearchParams();Object.entries(p).forEach(([k,v])=>v!==''&&v!=null&&q.set(k,v));return api.get(`/api/web-assets?${q}`)},stats:()=>api.get('/api/web-assets/stats'),get:id=>api.get(`/api/web-assets/${id}`)}
export default webApi
