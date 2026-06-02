import apiClient from './client'

export interface Tag {
  id?: number
  name: string
  color?: string
  description?: string
  host_count?: number
}

export const tagsApi = {
  getTags: () => apiClient.get('/tags'),
  
  createTag: (data: Tag) => apiClient.post('/tags', data),
  
  updateTag: (id: number, data: Partial<Tag>) => apiClient.put(`/tags/${id}`, data),
  
  deleteTag: (id: number) => apiClient.delete(`/tags/${id}`),
  
  addHostTags: (hostId: number, tagIds: number[]) =>
    apiClient.post(`/tags/hosts/${hostId}`, { tag_ids: tagIds }),
  
  removeHostTag: (hostId: number, tagId: number) =>
    apiClient.delete(`/tags/hosts/${hostId}/${tagId}`),
  
  addPlatformTags: (platformId: number, tagIds: number[]) =>
    apiClient.post(`/tags/platforms/${platformId}`, { tag_ids: tagIds }),
  
  removePlatformTag: (platformId: number, tagId: number) =>
    apiClient.delete(`/tags/platforms/${platformId}/${tagId}`),
  
  getTagHosts: (tagId: number, page?: number, perPage?: number, search?: string) => {
    const params = new URLSearchParams()
    if (page) params.append('page', page.toString())
    if (perPage) params.append('per_page', perPage.toString())
    if (search) params.append('search', search)
    return apiClient.get(`/tags/${tagId}/hosts?${params.toString()}`)
  },
  
  batchRemoveTagHosts: (tagId: number, hostIds: number[]) =>
    apiClient.post(`/tags/${tagId}/hosts/batch-remove`, { host_ids: hostIds }),
}

