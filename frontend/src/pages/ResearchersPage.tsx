import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { researchersApi, type Researcher } from '../features/directory/api'
import {
  Dialog,
  Feedback,
  StatusBadge,
  inputClass,
  primaryButton,
  secondaryButton,
} from '../features/directory/DirectoryUI'

const key = ['researchers'] as const
const blank = { name: '', orcid: '', email: '', is_active: true }
type Draft = typeof blank

export default function ResearchersPage() {
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: key, queryFn: researchersApi.list })
  const [editing, setEditing] = useState<Researcher | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [deleting, setDeleting] = useState<Researcher | null>(null)
  const [error, setError] = useState<string | null>(null)
  const save = useMutation({
    mutationFn: (value: Draft) =>
      editing
        ? researchersApi.update(editing.id, {
            name: value.name.trim(),
            email: value.email.trim(),
            orcid: value.orcid.trim() || null,
            is_active: value.is_active,
          })
        : researchersApi.create({
            name: value.name.trim(),
            orcid: value.orcid.trim() || null,
            email: value.email.trim(),
          }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: key })
      setDraft(null)
      setEditing(null)
    },
    onError: (reason: Error) => setError(reason.message),
  })
  const remove = useMutation({
    mutationFn: (id: number) => researchersApi.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: key })
      setDeleting(null)
    },
    onError: (reason: Error) => setError(reason.message),
  })
  const startCreate = () => {
    setEditing(null)
    setDraft({ ...blank })
    setError(null)
  }
  const startEdit = (item: Researcher) => {
    setEditing(item)
    setDraft({
      name: item.name,
      orcid: item.orcid ?? '',
      email: item.email,
      is_active: item.is_active,
    })
    setError(null)
  }
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (draft) {
      setError(null)
      save.mutate(draft)
    }
  }
  return (
    <section className="space-y-6">
      <PageHeader
        title="Researchers"
        description="Manage researchers included in publication discovery."
        aside={
          <button type="button" className={primaryButton} onClick={startCreate}>
            <Plus size={17} className="mr-2" />
            Add researcher
          </button>
        }
      />
      <div className="panel overflow-hidden">
        {query.isPending ? (
          <p className="p-6 text-sm text-slate-500">Loading researchers…</p>
        ) : query.isError ? (
          <div className="space-y-3 p-6">
            <Feedback message={query.error.message} />
            <button className={secondaryButton} onClick={() => void query.refetch()}>
              Retry
            </button>
          </div>
        ) : query.data.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">No researchers yet. Add one to begin.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-5 py-4">Name</th>
                  <th className="px-5 py-4">ORCID</th>
                  <th className="px-5 py-4">Email</th>
                  <th className="px-5 py-4">Status</th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {query.data.map((item) => (
                  <tr key={item.id}>
                    <td className="px-5 py-4 font-medium text-slate-900">{item.name}</td>
                    <td className="px-5 py-4 font-mono text-xs text-slate-600">
                      {item.orcid ?? 'Not provided'}
                    </td>
                    <td className="px-5 py-4 text-slate-600">{item.email}</td>
                    <td className="px-5 py-4">
                      <StatusBadge active={item.is_active} />
                    </td>
                    <td className="px-5 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          aria-label={`Edit ${item.name}`}
                          className={secondaryButton}
                          onClick={() => startEdit(item)}
                        >
                          <Pencil size={15} />
                        </button>
                        <button
                          aria-label={`Delete ${item.name}`}
                          className="rounded-lg border border-red-200 px-3 py-2 text-red-700 hover:bg-red-50"
                          onClick={() => {
                            setDeleting(item)
                            setError(null)
                          }}
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {draft && (
        <Dialog
          title={editing ? 'Edit researcher' : 'Add researcher'}
          onClose={() => {
            if (!save.isPending) setDraft(null)
          }}
        >
          <form className="space-y-4" onSubmit={submit}>
            <label className="block space-y-1 text-sm font-medium">
              Name
              <input
                required
                maxLength={255}
                className={inputClass}
                value={draft.name}
                onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              />
            </label>
            <label className="block space-y-1 text-sm font-medium">
              ORCID
              <input
                placeholder="0000-0000-0000-0000"
                pattern="[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9X]{4}"
                className={inputClass}
                value={draft.orcid}
                onChange={(e) => setDraft({ ...draft, orcid: e.target.value })}
              />
              <span className="block text-xs font-normal text-slate-500">
                Optional. Without an ORCID, discovery searches PubMed by author name (lower
                confidence).
              </span>
            </label>
            <label className="block space-y-1 text-sm font-medium">
              Email
              <input
                required
                type="email"
                maxLength={320}
                autoComplete="email"
                className={inputClass}
                value={draft.email}
                onChange={(e) => setDraft({ ...draft, email: e.target.value })}
              />
            </label>
            {editing && (
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={draft.is_active}
                  onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })}
                />
                Active for discovery
              </label>
            )}
            <Feedback message={error} />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                className={secondaryButton}
                disabled={save.isPending}
                onClick={() => setDraft(null)}
              >
                Cancel
              </button>
              <button className={primaryButton} disabled={save.isPending}>
                {save.isPending ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </Dialog>
      )}
      {deleting && (
        <Dialog
          title="Delete researcher?"
          onClose={() => {
            if (!remove.isPending) setDeleting(null)
          }}
        >
          <p className="mb-5 text-sm text-slate-600">
            Delete <strong>{deleting.name}</strong>? This action removes the researcher record.
            Consider marking inactive instead if they should be preserved.
          </p>
          <Feedback message={error} />
          <div className="mt-5 flex justify-end gap-2">
            <button
              className={secondaryButton}
              onClick={() => setDeleting(null)}
              disabled={remove.isPending}
            >
              Cancel
            </button>
            <button
              className="rounded-lg bg-red-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              disabled={remove.isPending}
              onClick={() => {
                setError(null)
                remove.mutate(deleting.id)
              }}
            >
              {remove.isPending ? 'Deleting…' : 'Delete'}
            </button>
          </div>
        </Dialog>
      )}
    </section>
  )
}
