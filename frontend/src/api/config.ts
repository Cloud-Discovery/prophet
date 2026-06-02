import apiClient from './client'

export interface ConcurrentConfig {
  scan_concurrent: number
  collect_concurrent: number
}

export const configApi = {
  getConcurrentConfig: () => apiClient.get<ConcurrentConfig>('/config/concurrent'),
  
  updateConcurrentConfig: (data: ConcurrentConfig) =>
    apiClient.put('/config/concurrent', data),
}

