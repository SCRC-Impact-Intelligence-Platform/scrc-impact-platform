import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '../components/common/PageHeader'
import {
  Feedback,
  primaryButton,
  secondaryButton,
  inputClass,
} from '../features/directory/DirectoryUI'
import { researchersApi, resourcesApi } from '../features/directory/api'
import { publicationsApi } from '../features/publications/api'
import { formsApi } from '../features/forms/api'

const PAGE_SIZE = 50

export default function FormsPage() {
  const cache = useQueryClient()
  const [researcherId, setResearcherId] = useState<number | null>(null)
  const [page, setPage] = useState(0)
  const [selections, setSelections] = useState<Record<number, number[]>>({})
  const [activeBatch, setActiveBatch] = useState<number | null>(null)
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [sentNotice, setSentNotice] = useState<string | null>(null)

  const researchers = useQuery({ queryKey: ['researchers'], queryFn: researchersApi.list })
  const resources = useQuery({ queryKey: ['resources'], queryFn: resourcesApi.list })
  const batches = useQuery({ queryKey: ['forms'], queryFn: formsApi.list })
  const publications = useQuery({
    queryKey: ['publications', 'form-selection', researcherId, page],
    queryFn: () =>
      publicationsApi.list({
        researcher_id: researcherId!,
        status: 'PENDING',
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
    enabled: researcherId !== null,
  })
  const create = useMutation({
    mutationFn: formsApi.create,
    onSuccess: async (created) => {
      setSentNotice(null)
      setActiveBatch(created.batch_id)
      const draft = await formsApi.draft(created.batch_id)
      setSubject(draft.subject)
      setBody(draft.body)
      await cache.invalidateQueries({ queryKey: ['forms'] })
    },
  })
  const send = useMutation({
    mutationFn: () => formsApi.send(activeBatch!, subject, body),
    onSuccess: async (result) => {
      setActiveBatch(null)
      setSubject('')
      setBody('')
      setSentNotice(
        `Invitation sent to ${result.recipient}. The form and selected publications are now marked SENT.`,
      )
      await cache.invalidateQueries({ queryKey: ['forms'] })
      await cache.invalidateQueries({ queryKey: ['publications'] })
    },
  })
  const selectedIds = Object.keys(selections).map(Number)
  const selectionsValid =
    selectedIds.length > 0 && selectedIds.every((id) => selections[id].length > 0)
  const selectedResearcher = researchers.data?.find((r) => r.id === researcherId)
  const activeResources = resources.data?.filter((r) => r.is_active) ?? []

  async function openDraft(batchId: number) {
    try {
      setError(null)
      setSentNotice(null)
      const draft = await formsApi.draft(batchId)
      setSubject(draft.subject)
      setBody(draft.body)
      setActiveBatch(batchId)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to load invitation draft')
    }
  }

  return (
    <section className="space-y-6">
      <PageHeader
        title="Verification forms"
        description="Choose a researcher, select pending publications and candidate resources, then prepare an email invitation."
      />
      <div className="panel space-y-5 p-6">
        <h2 className="text-lg font-semibold">Create verification form</h2>
        <label className="block max-w-xl space-y-2 text-sm font-medium">
          <span>Researcher / recipient</span>
          <select
            className={inputClass}
            value={researcherId ?? ''}
            onChange={(event) => {
              setResearcherId(event.target.value ? Number(event.target.value) : null)
              setPage(0)
              setSelections({})
              setActiveBatch(null)
              setSentNotice(null)
            }}
          >
            <option value="">Choose a researcher</option>
            {(researchers.data ?? [])
              .filter((r) => r.is_active)
              .map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} — {r.email}
                </option>
              ))}
          </select>
        </label>
        {selectedResearcher && (
          <p className="text-sm text-slate-500">
            The form will be addressed to {selectedResearcher.email}. Only publications first
            discovered for this researcher are shown.
          </p>
        )}
        {publications.isLoading && <p>Loading publications…</p>}
        {publications.isError && <Feedback message={publications.error.message} />}
        {(publications.data ?? []).map((p) => {
          const selected = selections[p.id] !== undefined
          return (
            <div key={p.id} className="rounded-lg border border-slate-200 p-4">
              <label className="flex gap-3 font-medium text-slate-900">
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={(event) =>
                    setSelections((prev) => {
                      const next = { ...prev }
                      if (event.target.checked) next[p.id] = []
                      else delete next[p.id]
                      return next
                    })
                  }
                />
                <span>
                  {p.title}
                  <span className="mt-1 block text-xs font-normal text-slate-500">
                    PMID {p.pmid} · {p.authors.join(', ')}
                  </span>
                </span>
              </label>
              {selected && (
                <div className="mt-3 flex flex-wrap gap-3 border-t border-slate-100 pt-3">
                  {activeResources.map((r) => (
                    <label key={r.id} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={selections[p.id].includes(r.id)}
                        onChange={(event) =>
                          setSelections((prev) => ({
                            ...prev,
                            [p.id]: event.target.checked
                              ? [...prev[p.id], r.id]
                              : prev[p.id].filter((id) => id !== r.id),
                          }))
                        }
                      />
                      {r.name}
                    </label>
                  ))}
                </div>
              )}
            </div>
          )
        })}
        {researcherId !== null && (
          <div className="flex items-center gap-3">
            <button
              className={secondaryButton}
              disabled={page === 0}
              onClick={() => setPage((n) => Math.max(0, n - 1))}
            >
              Previous
            </button>
            <span className="text-sm text-slate-500">Page {page + 1}</span>
            <button
              className={secondaryButton}
              disabled={(publications.data?.length ?? 0) < PAGE_SIZE}
              onClick={() => setPage((n) => n + 1)}
            >
              Next
            </button>
          </div>
        )}
        <button
          type="button"
          className={primaryButton}
          disabled={!researcherId || !selectionsValid || create.isPending}
          onClick={() => {
            setError(null)
            create.mutate({
              researcher_id: researcherId!,
              items: selectedIds.map((publication_id) => ({
                publication_id,
                resource_ids: selections[publication_id],
              })),
            })
          }}
        >
          Generate Google Form ({selectedIds.length} publications)
        </button>
        <p className="text-xs text-slate-500">
          Each chosen publication requires at least one candidate resource. Form creation uses your
          local Google OAuth credentials.
        </p>
        {create.isError && <Feedback message={create.error.message} />}
        <Feedback message={error} />
      </div>
      {sentNotice && (
        <div
          role="status"
          className="flex items-start justify-between gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800"
        >
          <span>{sentNotice}</span>
          <button
            type="button"
            className="font-semibold underline"
            onClick={() => setSentNotice(null)}
          >
            Dismiss
          </button>
        </div>
      )}
      <div className="panel space-y-4 p-6">
        <h2 className="text-lg font-semibold">Existing forms</h2>
        {batches.isError && <Feedback message={batches.error.message} />}
        {(batches.data ?? []).map((batch) => (
          <div
            className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 py-3"
            key={batch.id}
          >
            <span className="text-sm">
              Batch #{batch.id} · {batch.state} ·{' '}
              {researchers.data?.find((r) => r.id === batch.researcher_id)?.name ?? 'Legacy batch'}
            </span>
            {batch.state === 'READY' && batch.researcher_id && (
              <button className={secondaryButton} onClick={() => void openDraft(batch.id)}>
                Compose invitation
              </button>
            )}
            {batch.responder_url && (
              <a
                href={batch.responder_url}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-blue-700 underline"
              >
                Open Google Form
              </a>
            )}
          </div>
        ))}
      </div>
      {activeBatch !== null && (
        <div className="panel space-y-4 p-6">
          <h2 className="text-lg font-semibold">Invitation for batch #{activeBatch}</h2>
          <label className="block space-y-1 text-sm font-medium">
            Subject
            <input
              className={inputClass}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </label>
          <label className="block space-y-1 text-sm font-medium">
            Message
            <textarea
              className={`${inputClass} min-h-64`}
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </label>
          <div className="flex gap-3">
            <button
              className={secondaryButton}
              onClick={() => void navigator.clipboard.writeText(`Subject: ${subject}\n\n${body}`)}
            >
              Copy draft
            </button>
            <button
              className={secondaryButton}
              disabled={send.isPending}
              onClick={() => setActiveBatch(null)}
            >
              Cancel
            </button>
            <button
              className={primaryButton}
              disabled={send.isPending || send.isSuccess}
              onClick={() => {
                if (
                  window.confirm(
                    'Send this invitation to the researcher email stored in the backend?',
                  )
                )
                  send.mutate()
              }}
            >
              {send.isPending ? 'Sending…' : 'Send invitation'}
            </button>
          </div>
          {send.isError && <Feedback message={send.error.message} />}
        </div>
      )}
    </section>
  )
}
