import { useState } from 'react'
import { useContracts } from '../hooks/useContracts'
import { useAuth } from '../hooks/useAuth'

export default function ContractDashboard() {
  const { data: contracts = [], isLoading: loading, error } = useContracts()
  const { user } = useAuth()
  const [selectedContract, setSelectedContract] = useState<string | null>(null)

  const navigateToContract = (contractId: string) => {
    setSelectedContract(contractId)
    // Future: Navigate to Contract-specific view
    console.log(`Navigating to Contract: ${contractId}`)
  }

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Contract Directory
        </h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Browse and manage your contract relationships
        </p>
        <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded">
          Schema: tenant_{user?.tenant_subdomain} • Role: {user?.role} {user?.is_owner && '(Owner)'}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error loading contracts
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {error instanceof Error ? error.message : 'Failed to fetch contracts'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={`skeleton-${n}`} className="animate-pulse">
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="p-6">
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Contracts Grid */}
      {!loading && contracts.length > 0 && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {contracts.map((contract) => (
            <div
              key={contract.id}
              className={`bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow cursor-pointer ${
                selectedContract === contract.id ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => navigateToContract(contract.id)}
            >
              <div className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                      <span className="text-white font-semibold text-lg">
                        {contract.title.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      {contract.title}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {contract.reference_number}
                    </p>
                  </div>
                </div>
                {contract.title && (
                  <div className="mt-2">
                    <a
                      href={contract.title}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      🌐 Visit Website
                    </a>
                  </div>
                )}
                <div className="mt-4 flex justify-between items-center">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    contract.title !== 'active' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                  }`}>
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      navigateToContract(contract.id)
                    }}
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium text-sm"
                  >
                    View Details →
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && contracts.length === 0 && !error && (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
            No Contracts found
          </h3>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            Get started by adding your first Contract.
          </p>
          <div className="mt-6">
            <button
              type="button"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Add Contract
            </button>
          </div>
        </div>
      )}
    </div>
  )
}