import { Activity, ArrowUpRight, BookOpen, ClipboardList, ShieldCheck } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'

export default function DashboardPage() {
  return <section className="space-y-7">
    <PageHeader eyebrow="Overview / Research Impact" title="Impact Dashboard" description="A central workspace for publication discovery and verification." aside={<span className="tag">Preview layout</span>}/>
    <div className="grid gap-4 md:grid-cols-3">
      {[{label:'Publication Discovery',detail:'Connect to the discovery workflow',icon:BookOpen},{label:'Verification Forms',detail:'Manage pending attribution reviews',icon:ClipboardList},{label:'Confirmed Impact',detail:'Explore verified resource usage',icon:Activity}].map(({label,detail,icon:Icon}) => <div key={label} className="panel p-6"><div className="mb-6 inline-flex rounded-xl bg-blue-50 p-3 text-blue-700"><Icon size={21}/></div><div className="font-semibold text-slate-900">{label}</div><div className="muted mt-2 text-sm">{detail}</div><div className="mt-5 flex items-center gap-1 text-xs font-medium text-blue-700">Coming later <ArrowUpRight size={14}/></div></div>)}
    </div>
    <div className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
      <div className="panel p-6 sm:p-8"><div className="eyebrow">Suggested workflow</div><h2 className="mt-2 text-lg font-semibold">From discovery to attribution</h2><div className="mt-7 grid gap-4 sm:grid-cols-3">{['Discover publications','Send verification forms','Review confirmed usage'].map((step,index) => <div key={step} className="rounded-xl border border-slate-200 bg-slate-50/80 p-4"><div className="text-xs font-bold tracking-widest text-blue-600">STEP {String(index+1).padStart(2,'0')}</div><div className="mt-3 text-sm font-medium text-slate-800">{step}</div></div>)}</div></div>
      <div className="panel p-6 sm:p-8"><div className="eyebrow">Build status</div><h2 className="mt-2 text-lg font-semibold">Frontend foundation</h2><div className="mt-5 space-y-3">{['React + TypeScript','Tailwind CSS','React Query provider','Vite / Nginx proxy routing'].map(x => <div key={x} className="flex items-center gap-2 text-sm text-slate-700"><ShieldCheck size={17} className="text-emerald-600"/>{x}</div>)}</div><div className="mt-6 text-xs text-slate-500">Backend connections are intentionally disabled.</div></div>
    </div>
  </section>
}
