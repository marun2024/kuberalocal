import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export interface UpdateTenantSettingsRequest {
  display_name?: string
  logo_url?: string
}

export interface TenantSettingsResponse {
  id: number
  display_name: string | null
  logo_url: string | null
  theme_settings: object
  notification_settings: object
  custom_metadata: object
  created_at: string
  updated_at: string
}

// Fetch tenant settings
const fetchTenantSettings = async (): Promise<TenantSettingsResponse> => {
  const token = localStorage.getItem('token')
  
  if (!token) {
    throw new Error('No authentication token')
  }

  const response = await fetch('/api/v1/tenants/settings', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    }
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch tenant settings')
  }

  return response.json()
}

export const useTenantSettings = () => {
  return useQuery({
    queryKey: ['tenant', 'settings'],
    queryFn: fetchTenantSettings,
  })
}

// Update tenant settings
const updateTenantSettings = async (data: UpdateTenantSettingsRequest): Promise<TenantSettingsResponse> => {
  const token = localStorage.getItem('token')
  
  if (!token) {
    throw new Error('No authentication token')
  }

  const response = await fetch('/api/v1/tenants/settings', {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update tenant settings')
  }

  return response.json()
}

export const useUpdateTenantSettings = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: updateTenantSettings,
    onSuccess: () => {
      // Invalidate and refetch tenant settings
      queryClient.invalidateQueries({ queryKey: ['tenant', 'settings'] })
      // Invalidate and refetch user data since tenant info changed
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
    },
  })
}