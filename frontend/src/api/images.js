import api from './index'

export const listImages = (params) => api.get('/api/images', { params })
export const getImage = (id) => api.get(`/api/images/${id}`)
export const deleteImagesByIds = (imageIds) => api.post('/api/images/delete-by-ids', { image_ids: imageIds })
export const deleteImagesByPath = (pathPrefix) => api.post('/api/images/delete-by-path', { path_prefix: pathPrefix })