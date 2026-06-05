import api from './index'

export const importImages = (directory, recursive = true) => api.post('/images/import', { directory, recursive })
export const listImages = (params) => api.get('/images', { params })
export const getImage = (id) => api.get(`/images/${id}`)