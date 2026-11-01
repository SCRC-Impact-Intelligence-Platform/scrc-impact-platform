import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { resourcesApi, type Resource, type ResourceType } from '../features/directory/api'
import { Dialog, Feedback, StatusBadge, inputClass, primaryButton, secondaryButton } from '../features/directory/DirectoryUI'

const key = ['resources'] as const
const blank = { name: '', type: 'EQUIPMENT' as ResourceType, is_active: true }
type Draft = typeof blank
const types: ResourceType[] = ['EQUIPMENT', 'FUNDING', 'SERVICE']

export default function ResourcesPage() {
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: key, queryFn: resourcesApi.list })
  const [editing, setEditing] = useState<Resource | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [deleting, setDeleting] = useState<Resource | null>(null)
  const [error, setError] = useState<string | null>(null)
  const save = useMutation({
    mutationFn: (value: Draft) => editing
      ? resourcesApi.update(editing.id, { name: value.name.trim(), type: value.type, is_active: value.is_active })
      : resourcesApi.create({ name: value.name.trim(), type: value.type }),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: key }); setDraft(null); setEditing(null) },
    onError: (reason: Error) => setError(reason.message),
  })
  const remove = useMutation({
    mutationFn: (id: number) => resourcesApi.remove(id),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: key }); setDeleting(null) },
    onError: (reason: Error) => setError(reason.message),
  })
  const startCreate = () => { setEditing(null); setDraft({ ...blank }); setError(null) }
  const startEdit = (item: Resource) => { setEditing(item); setDraft({ name: item.name, type: item.type, is_active: item.is_active }); setError(null) }
  const submit = (event: FormEvent) => { event.preventDefault(); if (draft) { setError(null); save.mutate(draft) } }
  return <section className="space-y-6">
    <PageHeader title="Resources" description="Manage equipment, funding, and services available for attribution." aside={<button type="button" className={primaryButton} onClick={startCreate}><Plus size={17} className="mr-2"/>Add resource</button>}/>
    <div className="panel overflow-hidden">
      {query.isPending ? <p className="p-6 text-sm text-slate-500">Loading resources…</p> : query.isError ? <div className="space-y-3 p-6"><Feedback message={query.error.message}/><button className={secondaryButton} onClick={() => void query.refetch()}>Retry</button></div> : query.data.length === 0 ? <p className="p-6 text-sm text-slate-500">No resources yet. Add one to begin.</p> :
      <div className="overflow-x-auto"><table className="w-full min-w-[600px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500"><tr><th className="px-5 py-4">Name</th><th className="px-5 py-4">Type</th><th className="px-5 py-4">Status</th><th className="px-5 py-4 text-right">Actions</th></tr></thead><tbody className="divide-y divide-slate-100">{query.data.map(item => <tr key={item.id}><td className="px-5 py-4 font-medium text-slate-900">{item.name}</td><td className="px-5 py-4 text-slate-600">{item.type}</td><td className="px-5 py-4"><StatusBadge active={item.is_active}/></td><td className="px-5 py-4 text-right"><div className="flex justify-end gap-2"><button aria-label={`Edit ${item.name}`} className={secondaryButton} onClick={() => startEdit(item)}><Pencil size={15}/></button><button aria-label={`Delete ${item.name}`} className="rounded-lg border border-red-200 px-3 py-2 text-red-700 hover:bg-red-50" onClick={() => { setDeleting(item); setError(null) }}><Trash2 size={15}/></button></div></td></tr>)}</tbody></table></div>}
    </div>
    {draft && <Dialog title={editing ? 'Edit resource' : 'Add resource'} onClose={() => { if (!save.isPending) setDraft(null) }}><form className="space-y-4" onSubmit={submit}><label className="block space-y-1 text-sm font-medium">Name<input required maxLength={255} className={inputClass} value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })}/></label><label className="block space-y-1 text-sm font-medium">Type<select className={inputClass} value={draft.type} onChange={e => setDraft({ ...draft, type: e.target.value as ResourceType })}>{types.map(type => <option key={type} value={type}>{type}</option>)}</select></label>{editing && <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={draft.is_active} onChange={e => setDraft({ ...draft, is_active: e.target.checked })}/>Active</label>}<Feedback message={error}/><div className="flex justify-end gap-2"><button type="button" className={secondaryButton} disabled={save.isPending} onClick={() => setDraft(null)}>Cancel</button><button className={primaryButton} disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save'}</button></div></form></Dialog>}
    {deleting && <Dialog title="Delete resource?" onClose={() => { if (!remove.isPending) setDeleting(null) }}><p className="mb-5 text-sm text-slate-600">Delete <strong>{deleting.name}</strong>? Existing publication attributions may reference this resource. Consider making it inactive instead.</p><Feedback message={error}/><div className="mt-5 flex justify-end gap-2"><button className={secondaryButton} onClick={() => setDeleting(null)} disabled={remove.isPending}>Cancel</button><button className="rounded-lg bg-red-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={remove.isPending} onClick={() => { setError(null); remove.mutate(deleting.id) }}>{remove.isPending ? 'Deleting…' : 'Delete'}</button></div></Dialog>}
  </section>
}
