import apiClient from './client'

export interface Vendor {
  id: string
  name: string
  email: string
  phone?: string
  website?: string
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
}

export const vendorsApi = {
  getAll: async (): Promise<Vendor[]> => {
    const response = await apiClient.get('/vendors')
    return response.data
  },

  getById: async (id: string): Promise<Vendor> => {
    const response = await apiClient.get(`/vendors/${id}`)
    return response.data
  },

  create: async (vendor: Omit<Vendor, 'id' | 'created_at' | 'updated_at'>): Promise<Vendor> => {
    const response = await apiClient.post('/vendors', vendor)
    return response.data
  },

  update: async (id: string, vendor: Partial<Omit<Vendor, 'id' | 'created_at' | 'updated_at'>>): Promise<Vendor> => {
    const response = await apiClient.put(`/vendors/${id}`, vendor)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/vendors/${id}`)
  }
}