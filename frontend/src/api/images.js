import api from './index'

export const importImages = (directory, recursive = true) => api.post('/api/images/import', { directory, recursive })
export const listImages = (params) => api.get('/api/images', { params })
export const getImage = (id) => api.get(`/api/images/${id}`)