import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { 
  useTenantUsers, 
  useCreateTenantUser, 
  useUpdateTenantUser, 
  useDeleteTenantUser,
  TenantUser,
  CreateTenantUserRequest,
  UpdateTenantUserRequest
} from '../hooks/useTenantUsers'
import { useTenantSettings, useUpdateTenantSettings, UpdateTenantSettingsRequest } from '../hooks/useTenant'

export default function TenantSettings() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('overview')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [showEditUser, setShowEditUser] = useState<TenantUser | null>(null)
  const [showDeleteUser, setShowDeleteUser] = useState<TenantUser | null>(null)
  
  // User management hooks
  const { data: usersData, isLoading: usersLoading, error: usersError } = useTenantUsers()
  const createUserMutation = useCreateTenantUser()
  const updateUserMutation = useUpdateTenantUser()
  const deleteUserMutation = useDeleteTenantUser()
  
  // Tenant management hooks
  const { data: tenantSettings } = useTenantSettings()
  const updateTenantMutation = useUpdateTenantSettings()
  
  // Form state
  const [createUserForm, setCreateUserForm] = useState<CreateTenantUserRequest>({
    email: '',
    first_name: '',
    last_name: '',
    role: 'member',
    is_owner: false,
    password: ''
  })
  
  const [editUserForm, setEditUserForm] = useState<UpdateTenantUserRequest>({})
  
  // Tenant form state - initialize with tenant settings when available
  const [tenantForm, setTenantForm] = useState({
    display_name: tenantSettings?.display_name || user?.tenant_name || ''
  })

  // Update form when tenant settings are loaded
  useEffect(() => {
    if (tenantSettings) {
      setTenantForm({
        display_name: tenantSettings.display_name || user?.tenant_name || ''
      })
    }
  }, [tenantSettings, user?.tenant_name])

  const tabs = [
    { id: 'overview', name: 'Overview', icon: '🏢' },
    { id: 'users', name: 'Users', icon: '👥' },
    { id: 'danger', name: 'Danger Zone', icon: '⚠️' }
  ]

  const handleUpdateTenant = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const updateData: UpdateTenantSettingsRequest = {}
      
      // Only include changed fields
      if (tenantForm.display_name !== user?.tenant_name) {
        updateData.display_name = tenantForm.display_name
      }
      
      // Only update if there are changes
      if (Object.keys(updateData).length > 0) {
        await updateTenantMutation.mutateAsync(updateData)
      }
    } catch (error) {
      console.error('Failed to update tenant settings:', error)
    }
  }

  const handleDeleteTenant = async () => {
    // TODO: Implement tenant deletion
    console.log('Deleting tenant...')
    alert('Tenant deletion would be implemented here')
    setShowDeleteConfirm(false)
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createUserMutation.mutateAsync(createUserForm)
      setShowCreateUser(false)
      setCreateUserForm({
        email: '',
        first_name: '',
        last_name: '',
        role: 'member',
        is_owner: false,
        password: ''
      })
    } catch (error) {
      console.error('Failed to create user:', error)
    }
  }

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!showEditUser) return
    
    try {
      await updateUserMutation.mutateAsync({
        userId: showEditUser.id,
        userData: editUserForm
      })
      setShowEditUser(null)
      setEditUserForm({})
    } catch (error) {
      console.error('Failed to update user:', error)
    }
  }

  const handleDeleteUser = async () => {
    if (!showDeleteUser) return
    
    try {
      await deleteUserMutation.mutateAsync(showDeleteUser.id)
      setShowDeleteUser(null)
    } catch (error) {
      console.error('Failed to delete user:', error)
    }
  }

  const openEditUser = (userToEdit: TenantUser) => {
    setShowEditUser(userToEdit)
    setEditUserForm({
      first_name: userToEdit.first_name || '',
      last_name: userToEdit.last_name || '',
      role: userToEdit.role,
      is_active: userToEdit.is_active
    })
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <form onSubmit={handleUpdateTenant} className="space-y-6">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">
              Tenant Information
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Display Name
                </label>
                <input
                  type="text"
                  value={tenantForm.display_name}
                  onChange={(e) => setTenantForm({ ...tenantForm, display_name: e.target.value })}
                  placeholder={user?.tenant_name}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Custom display name for your organization. Leave empty to use default: "{user?.tenant_name}"
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Subdomain
                </label>
                <div className="flex">
                  <input
                    type="text"
                    value={user?.tenant_subdomain}
                    readOnly
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md shadow-sm bg-gray-50 text-gray-500 dark:bg-gray-600 dark:border-gray-600 dark:text-gray-400"
                  />
                  <span className="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 bg-gray-50 text-gray-500 text-sm rounded-r-md dark:bg-gray-600 dark:border-gray-600 dark:text-gray-400">
                    .localhost
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Technical subdomain (read-only, contact support to change)
                </p>
              </div>
            </div>
            
            <div className="flex justify-end">
              <button 
                type="submit"
                disabled={updateTenantMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {updateTenantMutation.isPending ? 'Updating...' : 'Update Tenant'}
              </button>
            </div>
          </form>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                Tenant Users
              </h2>
              <button 
                onClick={() => setShowCreateUser(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Add User
              </button>
            </div>
            
            {/* Error State */}
            {usersError && (
              <div className="mb-6 rounded-md bg-red-50 p-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Error loading users
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      {usersError instanceof Error ? usersError.message : 'Failed to fetch users'}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Loading State */}
            {usersLoading && (
              <div className="animate-pulse">
                <div className="bg-white dark:bg-gray-700 shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200 dark:divide-gray-600">
                    {[1, 2, 3].map((n) => (
                      <li key={n} className="px-6 py-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10 bg-gray-300 rounded-full"></div>
                            <div className="ml-4 space-y-2">
                              <div className="h-4 bg-gray-300 rounded w-32"></div>
                              <div className="h-3 bg-gray-300 rounded w-48"></div>
                            </div>
                          </div>
                          <div className="h-6 bg-gray-300 rounded w-16"></div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            
            {/* Users List */}
            {!usersLoading && usersData && (
              <div className="bg-white dark:bg-gray-700 shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200 dark:divide-gray-600">
                  {usersData.users.map((tenantUser) => (
                    <li key={tenantUser.id} className="px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                              <span className="text-sm font-medium text-white">
                                {tenantUser.first_name?.charAt(0) || '?'}{tenantUser.last_name?.charAt(0) || ''}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {tenantUser.first_name} {tenantUser.last_name}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {tenantUser.email}
                            </div>
                            {tenantUser.last_login && (
                              <div className="text-xs text-gray-400">
                                Last login: {new Date(tenantUser.last_login).toLocaleDateString()}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            tenantUser.is_owner 
                              ? 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-100' 
                              : tenantUser.is_active
                              ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                          }`}>
                            {tenantUser.is_owner ? 'Owner' : tenantUser.role}
                          </span>
                          {!tenantUser.is_active && (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100">
                              Inactive
                            </span>
                          )}
                          <div className="relative">
                            <button 
                              onClick={() => openEditUser(tenantUser)}
                              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 mr-2"
                              disabled={tenantUser.id === user?.user_id}
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            {!tenantUser.is_owner && tenantUser.id !== user?.user_id && (
                              <button 
                                onClick={() => setShowDeleteUser(tenantUser)}
                                className="text-red-400 hover:text-red-600"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Empty State */}
            {!usersLoading && usersData && usersData.users.length === 0 && (
              <div className="text-center py-12">
                <div className="mx-auto h-12 w-12 text-gray-400">
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                </div>
                <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                  No users found
                </h3>
                <p className="mt-2 text-gray-500 dark:text-gray-400">
                  Get started by adding your first tenant user.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Danger Zone Tab */}
        {activeTab === 'danger' && (
          <div className="space-y-6">
            <h2 className="text-lg font-medium text-red-600 dark:text-red-400">
              Danger Zone
            </h2>
            
            <div className="border border-red-200 rounded-lg p-6 bg-red-50 dark:bg-red-900/20 dark:border-red-800">
              <h3 className="text-lg font-medium text-red-900 dark:text-red-100 mb-2">
                Delete Tenant
              </h3>
              <p className="text-sm text-red-700 dark:text-red-200 mb-4">
                Permanently delete this tenant and all associated data. This action cannot be undone.
                All users, vendors, and other data will be permanently deleted.
              </p>
              
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-4 mb-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                      Warning
                    </h3>
                    <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
                      <p>
                        This will permanently delete the tenant "{user?.tenant_name}" and all associated data.
                        This action is irreversible.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                Delete Tenant
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900">
                <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mt-4">
                Delete Tenant
              </h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Are you absolutely sure you want to delete the tenant "{user?.tenant_name}"? 
                  This action cannot be undone and will permanently delete all data.
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleDeleteTenant}
                  className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Yes, Delete Tenant
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="mt-3 px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <form onSubmit={handleCreateUser}>
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Create New User
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Email *
                    </label>
                    <input
                      type="email"
                      required
                      value={createUserForm.email}
                      onChange={(e) => setCreateUserForm({ ...createUserForm, email: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        First Name
                      </label>
                      <input
                        type="text"
                        value={createUserForm.first_name}
                        onChange={(e) => setCreateUserForm({ ...createUserForm, first_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Last Name
                      </label>
                      <input
                        type="text"
                        value={createUserForm.last_name}
                        onChange={(e) => setCreateUserForm({ ...createUserForm, last_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Role
                    </label>
                    <select
                      value={createUserForm.role}
                      onChange={(e) => setCreateUserForm({ ...createUserForm, role: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    >
                      <option value="member">Member</option>
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="editor">Editor</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Password *
                    </label>
                    <input
                      type="password"
                      required
                      value={createUserForm.password}
                      onChange={(e) => setCreateUserForm({ ...createUserForm, password: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    />
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_owner"
                      checked={createUserForm.is_owner}
                      onChange={(e) => setCreateUserForm({ ...createUserForm, is_owner: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_owner" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                      Tenant Owner
                    </label>
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateUser(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createUserMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {createUserMutation.isPending ? 'Creating...' : 'Create User'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <form onSubmit={handleUpdateUser}>
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Edit User: {showEditUser.email}
                </h3>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        First Name
                      </label>
                      <input
                        type="text"
                        value={editUserForm.first_name || ''}
                        onChange={(e) => setEditUserForm({ ...editUserForm, first_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Last Name
                      </label>
                      <input
                        type="text"
                        value={editUserForm.last_name || ''}
                        onChange={(e) => setEditUserForm({ ...editUserForm, last_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Role
                    </label>
                    <select
                      value={editUserForm.role || ''}
                      onChange={(e) => setEditUserForm({ ...editUserForm, role: e.target.value })}
                      disabled={showEditUser.id === user?.user_id}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white disabled:opacity-50"
                    >
                      <option value="member">Member</option>
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="editor">Editor</option>
                    </select>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active"
                      checked={editUserForm.is_active ?? true}
                      onChange={(e) => setEditUserForm({ ...editUserForm, is_active: e.target.checked })}
                      disabled={showEditUser.id === user?.user_id}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                      Active User
                    </label>
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowEditUser(null)}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={updateUserMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {updateUserMutation.isPending ? 'Updating...' : 'Update User'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete User Modal */}
      {showDeleteUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900">
                <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mt-4">
                Delete User
              </h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Are you sure you want to delete "{showDeleteUser.email}"? 
                  This action cannot be undone.
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleDeleteUser}
                  disabled={deleteUserMutation.isPending}
                  className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
                >
                  {deleteUserMutation.isPending ? 'Deleting...' : 'Yes, Delete User'}
                </button>
                <button
                  onClick={() => setShowDeleteUser(null)}
                  className="mt-3 px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}