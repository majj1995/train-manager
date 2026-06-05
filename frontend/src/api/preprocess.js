import api from './index'

export const listScripts = () => api.get('/preprocess/scripts')
export const createScript = (data) => api.post('/preprocess/scripts', data)
export const deleteScript = (id) => api.delete(`/preprocess/scripts/${id}`)
export const listTasks = () => api.get('/preprocess/tasks')
export const createTask = (data) => api.post('/preprocess/tasks', data)
export const getTask = (id) => api.get(`/preprocess/tasks/${id}`)
export const getTaskResults = (taskId, params) => api.get(`/preprocess/tasks/${taskId}/results`, { params })
export const updateResult = (id, data) => api.put(`/preprocess/results/${id}`, data)
export const confirmResults = (data) => api.post('/preprocess/results/confirm', data)