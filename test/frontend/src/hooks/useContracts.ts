import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contractsApi, type Contract } from '../api/contracts'

export const useContracts = () => {
  return useQuery({
    queryKey: ['contracts'],
    queryFn: contractsApi.getAll,
  })
}

export const useVendor = (id: string) => {
  return useQuery({
    queryKey: ['contracts', id],
    queryFn: () => contractsApi.getById(id),
    enabled: !!id,
  })
}

export const useCreateVendor = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: contractsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
    },
  })
}

export const useUpdateVendor = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, ...vendor }: { id: string } & Partial<Omit<Contract, 'id' | 'created_at' | 'updated_at'>>) =>
      contractsApi.update(id, vendor),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
    },
  })
}

export const useDeleteVendor = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: contractsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
    },
  })
}