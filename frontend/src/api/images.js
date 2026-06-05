import http from './index'

export const importImages = (data) => http.post('/api/images/import', data)
export const listImages = (params) => http.get('/api/images', { params })
export const getImage = (id) => http.get(`/api/images/${id}`)