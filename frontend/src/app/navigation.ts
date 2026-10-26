import { BookOpen, ClipboardList, Database, FileCheck2, LayoutDashboard, Settings2, Users } from 'lucide-react'
import type { ComponentType } from 'react'

type IconComponent = ComponentType<{ size?: number; strokeWidth?: number; className?: string }>

export type NavigationItem = { path: string; label: string; description: string; icon: IconComponent }

export const navigation: NavigationItem[] = [
  { path: '/dashboard', label: 'Dashboard', description: 'Research impact at a glance', icon: LayoutDashboard },
  { path: '/researchers', label: 'Researchers', description: 'Faculty and ORCID directory', icon: Users },
  { path: '/publications', label: 'Publications', description: 'Discovered publications and review queue', icon: BookOpen },
  { path: '/forms', label: 'Verification Forms', description: 'Form batches and researcher invitations', icon: ClipboardList },
  { path: '/resources', label: 'Resources', description: 'Equipment, funding, and services', icon: Database },
  { path: '/attributions', label: 'Attributions', description: 'Confirmed publication-resource relationships', icon: FileCheck2 },
  { path: '/settings', label: 'Settings', description: 'Integrations and administration', icon: Settings2 },
]
