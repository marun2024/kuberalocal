import apiClient from './client'

export interface Contract {
  id: string
  title: string
  reference_number: string
  created_at: string
  updated_at: string
}

export const contractsApi = {
  getAll: async (): Promise<Contract[]> => {
    const response = await apiClient.get('/contracts')
    return response.data
  },

  getById: async (id: string): Promise<Contract> => {
    const response = await apiClient.get(`/contracts/${id}`)
    return response.data
  },

  create: async (contract: Omit<Contract, 'id' | 'created_at' | 'updated_at'>): Promise<Contract> => {
    const response = await apiClient.post('/contracts', contract)
    return response.data
  },

  update: async (id: string, contract: Partial<Omit<Contract, 'id' | 'created_at' | 'updated_at'>>): Promise<Contract> => {
    const response = await apiClient.put(`/contracts/${id}`, contract)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/contracts/${id}`)
  }
}