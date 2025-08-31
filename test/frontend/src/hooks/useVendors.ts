import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { vendorsApi, type Vendor } from '../api/vendors'

export const useVendors = () => {
  return useQuery({
    queryKey: ['vendors'],
    queryFn: vendorsApi.getAll,
  })
}

export const useVendor = (id: string) => {
  return useQuery({
    queryKey: ['vendors', id],
    queryFn: () => vendorsApi.getById(id),
    enabled: !!id,
  })
}

export const useCreateVendor = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: vendorsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] })
    },
  })
}

export const useUpdateVendor = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, ...vendor }: { id: string } & Partial<Omit<Vendor, 'id' | 'created_at' | 'updated_at'>>) =>
      vendorsApi.update(id, vendor),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] })
    },
  })
}

export const useDeleteVendor = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: vendorsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] })
    },
  })
}