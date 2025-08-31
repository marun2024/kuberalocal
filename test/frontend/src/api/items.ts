import apiClient from './client'

export interface Item {
  id: number
  name: string
  description?: string
  price: number
}

export const itemsApi = {
  getAll: () => apiClient.get<Item[]>('/items'),
  getById: (id: number) => apiClient.get<Item>(`/items/${id}`),
  create: (item: Item) => apiClient.post<Item>('/items/', item),
}
