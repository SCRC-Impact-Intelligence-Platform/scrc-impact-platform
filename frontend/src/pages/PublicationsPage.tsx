import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, BookOpen, ExternalLink, RefreshCw, Search, X } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Feedback, secondaryButton } from '../features/directory/DirectoryUI'
import { publicationsApi, type Publication, type PublicationStatus } from '../features/publications/api'

const PAGE_SIZE = 20
const statuses: PublicationStatus[] = ['PENDING', 'SENT', 'CONFIRMED', 'REJECTED', 'DISMISSED']

function StatusPill({ status }: { status: PublicationStatus }) {
  const colors: Record<PublicationStatus, string> = {
    PENDING: 'bg-amber-50 text-amber-800',
    SENT: 'bg-blue-50 text-blue-800',
    CONFIRMED: 'bg-emerald-50 text-emerald-800',
    REJECTED: 'bg-rose-50 text-rose-800',
    DISMISSED: 'bg-slate-100 text-slate-700',
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${colors[status]}`}>{status}</span>
}

function PublicationDetails({ publication, onClose }: { publication: Publication; onClose: () => void }) {
  return <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/50" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}>
    <section role="dialog" aria-modal="true" aria-labelledby="publication-dialog-title" className="flex h-full w-full max-w-2xl flex-col overflow-hidden bg-white shadow-2xl">
      <header className="flex items-start justify-between gap-4 border-b border-slate-200 p-6">
        <div className="space-y-2"><StatusPill status={publication.status}/><h2 id="publication-dialog-title" className="text-xl font-bold leading-snug text-slate-900">{publication.title}</h2></div>
        <button type="button" aria-label="Close details" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100" onClick={onClose}><X size={20}/></button>
      </header>
      <div className="space-y-6 overflow-y-auto p-6 text-sm text-slate-700">
        <dl className="grid gap-4 sm:grid-cols-2">
          <div><dt className="font-semibold text-slate-900">PMID</dt><dd className="mt-1"><a className="text-blue-700 underline underline-offset-2" href={`https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(publication.pmid)}/`} target="_blank" rel="noopener noreferrer">{publication.pmid} <ExternalLink size={12} className="inline"/></a></dd></div>
          <div><dt className="font-semibold text-slate-900">Publication date</dt><dd className="mt-1">{publication.publication_date || 'Not available'}</dd></div>
          <div><dt className="font-semibold text-slate-900">Journal</dt><dd className="mt-1">{publication.journal || 'Not available'}</dd></div>
          <div><dt className="font-semibold text-slate-900">DOI</dt><dd className="mt-1 break-all">{publication.doi ? <a className="text-blue-700 underline underline-offset-2" href={`https://doi.org/${encodeURIComponent(publication.doi)}`} target="_blank" rel="noopener noreferrer">{publication.doi} <ExternalLink size={12} className="inline"/></a> : 'Not available'}</dd></div>
          <div><dt className="font-semibold text-slate-900">Discovered via ORCID</dt><dd className="mt-1 font-mono text-xs">{publication.first_discovered_by_orcid}</dd></div>
          <div><dt className="font-semibold text-slate-900">Discovered at</dt><dd className="mt-1">{new Date(publication.discovered_at).toLocaleString()}</dd></div>
        </dl>
        <div><h3 className="mb-2 font-semibold text-slate-900">Authors</h3><p className="leading-relaxed">{publication.authors.length ? publication.authors.join(', ') : 'Not available'}</p></div>
        <div><h3 className="mb-2 font-semibold text-slate-900">Abstract</h3><p className="whitespace-pre-line leading-7">{publication.abstract || 'No abstract available from PubMed.'}</p></div>
      </div>
    </section>
  </div>
}

export default function PublicationsPage() {
  const [status, setStatus] = useState<PublicationStatus | ''>('PENDING')
  const [page, setPage] = useState(0)
  const [searchInput, setSearchInput] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const filters = { status: status || undefined, limit: PAGE_SIZE, offset: page * PAGE_SIZE }
  const query = useQuery({ queryKey: ['publications', filters], queryFn: () => publicationsApi.list(filters) })
  const detail = useQuery({ queryKey: ['publication', selectedId], queryFn: () => publicationsApi.get(selectedId!), enabled: selectedId !== null })
  // Client-side search is only applied to the current page: no backend search endpoint exists yet.
  const term = searchInput.trim().toLocaleLowerCase()
  const visible = (query.data ?? []).filter(p => !term || [p.title, p.pmid, p.doi ?? '', p.journal ?? '', p.authors.join(' ')].some(value => value.toLocaleLowerCase().includes(term)))
  const canGoNext = (query.data?.length ?? 0) === PAGE_SIZE

  return <section className="space-y-6">
    <PageHeader title="Publications" description="Review discovered PubMed publications and inspect their metadata." aside={<button type="button" className={secondaryButton} disabled={query.isFetching} onClick={() => void query.refetch()}><RefreshCw size={15} className="mr-2"/> Refresh</button>}/>
    <div className="panel overflow-hidden">
      <div className="flex flex-wrap items-end gap-4 border-b border-slate-200 p-5">
        <label className="space-y-1 text-sm font-medium text-slate-700"><span className="block">Status</span><select className="min-w-44 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" value={status} onChange={e => { setStatus(e.target.value as PublicationStatus | ''); setPage(0) }}><option value="">All statuses</option>{statuses.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
        <label className="min-w-64 flex-1 space-y-1 text-sm font-medium text-slate-700"><span className="block">Search this page</span><div className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3"><Search size={16} className="text-slate-400"/><input aria-label="Search current page" className="w-full py-2 text-sm font-normal outline-none" value={searchInput} onChange={e => setSearchInput(e.target.value)} placeholder="Title, PMID, DOI, author…"/></div></label>
      </div>
      {query.isPending ? <p className="p-6 text-sm text-slate-500">Loading publications…</p> : query.isError ? <div className="space-y-3 p-6"><Feedback message={query.error.message}/><button className={secondaryButton} onClick={() => void query.refetch()}>Retry</button></div> : query.data.length === 0 ? <div className="space-y-2 p-8 text-center"><BookOpen className="mx-auto text-slate-400"/><p className="font-medium text-slate-800">No publications found</p><p className="text-sm text-slate-500">Try another status, or run PubMed Discovery from the backend CLI.</p></div> : <>
        {term && <p className="border-b border-slate-100 px-5 py-3 text-xs text-slate-500">Search filters only the {query.data.length} records loaded on this page.</p>}
        <div className="overflow-x-auto"><table className="w-full min-w-[800px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500"><tr><th className="px-5 py-4">Publication</th><th className="px-5 py-4">Journal / Date</th><th className="px-5 py-4">Status</th><th className="px-5 py-4 text-right">Details</th></tr></thead><tbody className="divide-y divide-slate-100">{visible.map(p => <tr key={p.id} className="hover:bg-slate-50"><td className="max-w-xl px-5 py-4"><p className="font-semibold text-slate-900">{p.title}</p><p className="mt-1 text-xs text-slate-500">PMID {p.pmid}{p.doi ? ` · DOI ${p.doi}` : ''}</p><p className="mt-1 line-clamp-1 text-xs text-slate-500">{p.authors.join(', ')}</p></td><td className="px-5 py-4 text-slate-600"><p>{p.journal || 'Unknown journal'}</p><p className="mt-1 text-xs">{p.publication_date || 'No date'}</p></td><td className="px-5 py-4"><StatusPill status={p.status}/></td><td className="px-5 py-4 text-right"><button type="button" className={secondaryButton} onClick={() => setSelectedId(p.id)}>View details</button></td></tr>)}</tbody></table></div>
        {visible.length === 0 && <p className="p-6 text-sm text-slate-500">No matches on this page.</p>}
      </>}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4"><p className="text-sm text-slate-500">Page {page + 1} · {query.data?.length ?? 0} loaded {query.isFetching && !query.isPending ? '· Updating…' : ''}</p><div className="flex gap-2"><button type="button" className={secondaryButton} disabled={page === 0 || query.isPending || query.isError} onClick={() => setPage(p => Math.max(0, p - 1))}><ArrowLeft size={15} className="mr-2"/> Previous</button><button type="button" className={secondaryButton} disabled={!canGoNext || query.isFetching} onClick={() => setPage(p => p + 1)}>Next <ArrowRight size={15} className="ml-2"/></button></div></div>
    </div>
    {selectedId !== null && <div>{detail.isPending ? <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50"><div role="status" className="rounded-xl bg-white p-6">Loading publication details… <button className="ml-3 text-blue-700" onClick={() => setSelectedId(null)}>Close</button></div></div> : detail.isError ? <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50"><div className="rounded-xl bg-white p-6"><Feedback message={detail.error.message}/><button className={`${secondaryButton} mt-3`} onClick={() => setSelectedId(null)}>Close</button></div></div> : <PublicationDetails publication={detail.data} onClose={() => setSelectedId(null)}/>}</div>}
  </section>
}
