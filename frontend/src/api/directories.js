import api from './index'

export const addDirectory = (data) => api.post('/directories', data)
export const listDirectories = () => api.get('/directories')
export const deleteDirectory = (id) => api.delete(`/directories/${id}`)