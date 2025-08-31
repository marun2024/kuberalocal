import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { itemsApi, type Item } from '../api/items'

export const useItems = () => {
  return useQuery({
    queryKey: ['items'],
    queryFn: async () => {
      const response = await itemsApi.getAll()
      return response.data
    },
  })
}

export const useCreateItem = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (item: Item) => {
      const response = await itemsApi.create(item)
      return response.data
    },
    onSuccess: () => {
      // Invalidate and refetch items after successful creation
      queryClient.invalidateQueries({ queryKey: ['items'] })
    },
  })
}