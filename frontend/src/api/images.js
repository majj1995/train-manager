import api from './index'

export const listImages = (params) => api.get('/api/images', { params })
export const getImage = (id) => api.get(`/api/images/${id}`)