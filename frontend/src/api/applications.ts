import apiClient from './client'

export interface Application {
  id?: number
  name: string
  description?: string
}

export interface HostRelationship {
  id?: number
  from_host_id: number
  to_host_id: number
  relationship_type: string
  description?: string
}

export interface ApplicationGraphNode {
  id: string | number
  label: string
  type?: string
  x?: number
  y?: number
  color?: string
  icon?: string
  status?: string
  bindingHostId?: number
  data?: Record<string, any>
}

export interface ApplicationGraphEdge {
  id?: string | number
  source: string | number
  target: string | number
  label?: string
  relationshipType?: string
  description?: string
  data?: Record<string, any>
}

export const applicationsApi = {
  getApplications: () => apiClient.get('/applications'),
  
  createApplication: (data: Application) => apiClient.post('/applications', data),
  
  getApplication: (id: number) => apiClient.get(`/applications/${id}`),
  
  updateApplication: (id: number, data: Partial<Application>) =>
    apiClient.put(`/applications/${id}`, data),
  
  deleteApplication: (id: number) => apiClient.delete(`/applications/${id}`),
  
  addHosts: (id: number, hostIds: number[], relationshipType?: string) =>
    apiClient.post(`/applications/${id}/hosts`, {
      host_ids: hostIds,
      relationship_type: relationshipType || 'member',
    }),
  
  removeHost: (id: number, hostId: number) =>
    apiClient.delete(`/applications/${id}/hosts/${hostId}`),

  getRelationships: (id: number) =>
    apiClient.get(`/applications/${id}/relationships`),
  
  getGraph: (id: number) => apiClient.get(`/applications/${id}/graph`),
  
  createRelationship: (id: number, data: HostRelationship) =>
    apiClient.post(`/applications/${id}/relationships`, data),

  updateRelationship: (id: number, relationshipId: number, data: Partial<HostRelationship>) =>
    apiClient.put(`/applications/${id}/relationships/${relationshipId}`, data),

  deleteRelationship: (id: number, relationshipId: number) =>
    apiClient.delete(`/applications/${id}/relationships/${relationshipId}`),

  saveGraph: (id: number, payload: { nodes: ApplicationGraphNode[]; edges: ApplicationGraphEdge[]; resourceNodes: ApplicationGraphNode[]; metadata?: Record<string, any> }) =>
    apiClient.put(`/applications/${id}/graph`, payload),

  exportGraph: (id: number) =>
    apiClient.get<Blob, Blob>(`/applications/${id}/graph/export`, {
      responseType: 'blob'
    }),
}

