import apiClient from './client'

export interface Platform {
  id?: number
  name: string
  type: string
  host: string
  port?: number
  username: string
  password?: string
  region?: string
  extra_config?: Record<string, any>
  tags?: Array<{ id: number; name: string; color?: string; description?: string }>
  statistics?: {
    esxi_count?: number
    vm_count?: number
    total_hosts?: number
    total_cpu_cores?: number
    total_memory_gb?: number
    total_storage_gb?: number
  }
}

export const platformsApi = {
  getPlatforms: () => apiClient.get('/platforms'),
  
  createPlatform: (data: Platform) => apiClient.post('/platforms', data),
  
  getPlatform: (id: number) => apiClient.get(`/platforms/${id}`),
  
  updatePlatform: (id: number, data: Partial<Platform>) =>
    apiClient.put(`/platforms/${id}`, data),
  
  deletePlatform: (id: number) => apiClient.delete(`/platforms/${id}`),
  
  testPlatform: (id: number) => apiClient.post(`/platforms/${id}/test`),
  
  syncPlatform: (id: number) => apiClient.post(`/platforms/${id}/sync`),
}

