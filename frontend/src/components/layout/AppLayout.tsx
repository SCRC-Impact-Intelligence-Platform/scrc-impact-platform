import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { navigation } from '../../app/navigation'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { pathname } = useLocation()
  const active = navigation.find(item => item.path === pathname)

  return (
    <div className="min-h-screen bg-[#f5f8fc] text-slate-900">
      <button type="button" aria-label="Open navigation" onClick={() => setMobileOpen(true)} className="fixed left-4 top-4 z-20 rounded-lg border border-slate-200 bg-white p-2 text-slate-700 shadow-sm lg:hidden">
        <Menu size={22} />
      </button>
      {mobileOpen && <button type="button" aria-label="Close navigation overlay" className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden" onClick={() => setMobileOpen(false)} />}
      <Sidebar mobileOpen={mobileOpen} onNavigate={() => setMobileOpen(false)} />
      <div className="lg:pl-68">
        <header className="topbar">
          <div className="hidden text-sm text-slate-500 lg:block">Research Impact Platform <span className="mx-2 text-slate-300">/</span><span className="text-slate-800">{active?.label ?? 'Page not found'}</span></div>
          <div className="ml-auto flex items-center gap-3"><span className="status-dot"/><span className="text-xs font-medium text-slate-600">UI Preview</span><div className="avatar" aria-label="Admin placeholder">S</div></div>
        </header>
        <main className="mx-auto max-w-7xl px-5 pb-14 pt-10 sm:px-8 lg:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
