import { ShieldCheck } from 'lucide-react'
import { PageHeader } from './PageHeader'
import type { NavigationItem } from '../../app/navigation'

type Props = { item: NavigationItem }

export function WorkspacePlaceholder({ item }: Props) {
  const Icon = item.icon
  return <section className="space-y-6">
    <PageHeader title={item.label} description={item.description} aside={<span className="tag">UI scaffold</span>}/>
    <div className="panel p-8 sm:p-12"><div className="grid items-center gap-7 md:grid-cols-[auto_1fr]">
      <div className="placeholder-icon"><Icon size={30} strokeWidth={1.7}/></div>
      <div><h2 className="text-xl font-semibold text-slate-900">{item.label} workspace</h2><p className="muted mt-2 max-w-2xl">This page is intentionally left as a presentation shell. Forms, tables, mutations, and backend requests will be implemented after the interaction flow is agreed upon.</p><span className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-blue-700"><ShieldCheck size={16}/> No API calls or mock records</span></div>
    </div></div>
  </section>
}
