import { Link, useLocation } from 'react-router-dom'
import { Home, Settings, ArrowLeftRight, Info, Sparkles } from 'lucide-react'

const Layout = ({ children }) => {
  const location = useLocation()

  const navItems = [
    { path: '/', icon: Home, label: '📝 Rédaction CSV' },
    { path: '/images', icon: Sparkles, label: '🖼️ Images AI' },
    { path: '/info', icon: Info, label: 'Infos' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <ArrowLeftRight className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Shopify 2 Etsy</h1>
              <p className="text-xs text-gray-500">CSV Converter</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive(item.path)
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* Settings at bottom */}
        <div className="p-4 border-t border-gray-200">
          <Link
            to="/settings"
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              isActive('/settings')
                ? 'bg-blue-50 text-blue-600'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <Settings className="w-5 h-5" />
            <span className="font-medium">Paramètres</span>
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}

export default Layout
