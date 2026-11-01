import { NavLink } from 'react-router-dom'
import { FlaskConical, X } from 'lucide-react'
import { navigation } from '../../app/navigation'

type Props = { mobileOpen: boolean; onNavigate: () => void }

export function Sidebar({ mobileOpen, onNavigate }: Props) {
  return (
    <aside className={`sidebar fixed inset-y-0 left-0 z-40 w-68 transform transition-transform lg:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex items-center justify-between px-6 py-7">
        <div className="flex items-center gap-3"><div className="brand-mark">UCI</div><div className="leading-tight"><div className="text-sm font-semibold tracking-wide text-white">SCRC</div><div className="text-[11px] text-blue-200">Impact Intelligence</div></div></div>
        <button type="button" className="text-white lg:hidden" aria-label="Close navigation" onClick={onNavigate}><X size={20}/></button>
      </div>
      <div className="px-4"><div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.19em] text-blue-200/70">Workspace</div>
        <nav aria-label="Main navigation" className="space-y-1">
          {navigation.map(item => <NavLink key={item.path} to={item.path} end onClick={onNavigate} className={({ isActive }) => `nav-item ${isActive ? 'nav-active' : ''}`}><item.icon size={17} strokeWidth={1.9}/>{item.label}</NavLink>)}
        </nav>
      </div>
      <div className="absolute bottom-0 inset-x-0 border-t border-white/15 px-6 py-5"><div className="flex gap-2 items-center text-xs text-blue-100"><FlaskConical size={16}/> UC Irvine · SCRC</div><p className="mt-2 text-[11px] text-blue-200/70">Frontend scaffold · no live data</p></div>
    </aside>
  )
}
