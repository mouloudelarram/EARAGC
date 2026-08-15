import { NavLink, useLocation } from 'react-router-dom'
import {
  MessageSquare,
  FileText,
  BarChart2,
  Building2,
  Activity,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../services/api'

interface LayoutProps {
  children: React.ReactNode
}

const navItems = [
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/documents', icon: FileText, label: 'Documents' },
  { to: '/evaluation', icon: BarChart2, label: 'Evaluation' },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [apiStatus, setApiStatus] = useState<'checking' | 'ok' | 'error'>('checking')

  useEffect(() => {
    api.health()
      .then(() => setApiStatus('ok'))
      .catch(() => setApiStatus('error'))
  }, [])

  const currentPage = navItems.find(item => location.pathname.startsWith(item.to))?.label ?? 'Home'

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* ── Sidebar ── */}
      <aside className="w-64 bg-gray-900 flex flex-col flex-shrink-0">
        {/* Logo */}
        <div className="p-5 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-white font-semibold text-sm leading-tight">Enterprise</p>
              <p className="text-gray-400 text-xs">Architecture Copilot</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Status indicator */}
        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center gap-2 text-xs">
            <Activity className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-gray-500">API Status</span>
            <span className={`ml-auto flex items-center gap-1 font-medium ${
              apiStatus === 'ok' ? 'text-green-400' :
              apiStatus === 'error' ? 'text-red-400' :
              'text-yellow-400'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                apiStatus === 'ok' ? 'bg-green-400' :
                apiStatus === 'error' ? 'bg-red-400' :
                'bg-yellow-400 animate-pulse'
              }`} />
              {apiStatus === 'ok' ? 'Online' : apiStatus === 'error' ? 'Offline' : 'Checking...'}
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
          <h1 className="text-lg font-semibold text-gray-900">{currentPage}</h1>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

