import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import logger from '../utils/logger'

interface TenantUser {
  id: number
  email: string
  first_name: string | null
  last_name: string | null
  role: string
  is_owner: boolean
  is_active: boolean
  last_login: string | null
  created_at: string
  updated_at: string
}

interface TenantUserListResponse {
  users: TenantUser[]
  total: number
}

interface CreateTenantUserRequest {
  email: string
  first_name?: string
  last_name?: string
  role?: string
  is_owner?: boolean
  password: string
}

interface UpdateTenantUserRequest {
  first_name?: string
  last_name?: string
  role?: string
  is_active?: boolean
}

// API functions
const fetchTenantUsers = async (): Promise<TenantUserListResponse> => {
  const token = localStorage.getItem('token')
  logger.debug('fetchTenantUsers called', { hasToken: !!token })

  if (!token) {
    throw new Error('No authentication token')
  }

  const response = await fetch('/api/v1/users', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  logger.debug('Tenant users response', { status: response.status, ok: response.ok })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    logger.error('Failed to fetch tenant users', { status: response.status, error: errorData })
    throw new Error(errorData.detail || 'Failed to fetch tenant users')
  }

  const data = await response.json()
  logger.debug('Tenant users fetched successfully', { count: data.total })
  return data
}

const createTenantUser = async (userData: CreateTenantUserRequest): Promise<TenantUser> => {
  const token = localStorage.getItem('token')
  logger.debug('createTenantUser called', { email: userData.email })

  if (!token) {
    throw new Error('No authentication token')
  }

  const response = await fetch('/api/v1/users', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  })

  logger.debug('Create tenant user response', { status: response.status, ok: response.ok })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    logger.error('Failed to create tenant user', { status: response.status, error: errorData })
    throw new Error(errorData.detail || 'Failed to create user')
  }

  const data = await response.json()
  logger.debug('Tenant user created successfully', { userId: data.id })
  return data
}

const updateTenantUser = async (userId: number, userData: UpdateTenantUserRequest): Promise<TenantUser> => {
  const token = localStorage.getItem('token')
  logger.debug('updateTenantUser called', { userId })

  if (!token) {
    throw new Error('No authentication token')
  }

  const response = await fetch(`/api/v1/users/${userId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  })

  logger.debug('Update tenant user response', { status: response.status, ok: response.ok })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    logger.error('Failed to update tenant user', { status: response.status, error: errorData })
    throw new Error(errorData.detail || 'Failed to update user')
  }

  const data = await response.json()
  logger.debug('Tenant user updated successfully', { userId: data.id })
  return data
}

const deleteTenantUser = async (userId: number): Promise<void> => {
  const token = localStorage.getItem('token')
  logger.debug('deleteTenantUser called', { userId })

  if (!token) {
    throw new Error('No authentication token')
  }

  const response = await fetch(`/api/v1/users/${userId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  logger.debug('Delete tenant user response', { status: response.status, ok: response.ok })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    logger.error('Failed to delete tenant user', { status: response.status, error: errorData })
    throw new Error(errorData.detail || 'Failed to delete user')
  }

  logger.debug('Tenant user deleted successfully', { userId })
}

// Custom hooks
export const useTenantUsers = () => {
  const token = localStorage.getItem('token')

  return useQuery({
    queryKey: ['tenantUsers'],
    queryFn: fetchTenantUsers,
    enabled: !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useCreateTenantUser = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createTenantUser,
    onSuccess: () => {
      logger.debug('Create tenant user mutation success, invalidating queries')
      queryClient.invalidateQueries({ queryKey: ['tenantUsers'] })
    },
    onError: (error) => {
      logger.error('Create tenant user mutation failed', { error: error.message })
    },
  })
}

export const useUpdateTenantUser = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, userData }: { userId: number; userData: UpdateTenantUserRequest }) =>
      updateTenantUser(userId, userData),
    onSuccess: () => {
      logger.debug('Update tenant user mutation success, invalidating queries')
      queryClient.invalidateQueries({ queryKey: ['tenantUsers'] })
    },
    onError: (error) => {
      logger.error('Update tenant user mutation failed', { error: error.message })
    },
  })
}

export const useDeleteTenantUser = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteTenantUser,
    onSuccess: () => {
      logger.debug('Delete tenant user mutation success, invalidating queries')
      queryClient.invalidateQueries({ queryKey: ['tenantUsers'] })
    },
    onError: (error) => {
      logger.error('Delete tenant user mutation failed', { error: error.message })
    },
  })
}

export type { TenantUser, TenantUserListResponse, CreateTenantUserRequest, UpdateTenantUserRequest }