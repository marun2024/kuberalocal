import { useState } from 'react'
import DashboardLayout from './DashboardLayout'
import VendorDashboardContent from './VendorDashboardContent'
import ContractDashboard from './ContractDashboard'
import TenantSettings from './TenantSettings'

export default function Dashboard() {
  const [currentView, setCurrentView] = useState('vendors')

  const renderContent = () => {
    switch (currentView) {
      case 'vendors':
        return <ContractDashboard />
      case 'tenant-settings':
        return <TenantSettings />
      default:
        return <ContractDashboard />
    }
  }

  return (
    <DashboardLayout 
      currentView={currentView} 
      onViewChange={setCurrentView}
    >
      {renderContent()}
    </DashboardLayout>
  )
}