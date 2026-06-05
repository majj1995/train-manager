import api from './index'

export const addDirectory = (data) => api.post('/api/directories', data)
export const listDirectories = () => api.get('/api/directories')
export const deleteDirectory = (id) => api.delete(`/api/directories/${id}`)