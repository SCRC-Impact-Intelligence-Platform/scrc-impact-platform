import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, RefreshCw } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { secondaryButton } from '../features/directory/DirectoryUI'
import {
  attributionsApi,
  type Criticality,
  type ResourceImpactSummary,
} from '../features/attributions/api'

const levels: {
  key: Criticality
  field: 'critical_count' | 'significant_count' | 'minor_count'
  label: string
  bar: string
  tag: string
}[] = [
  {
    key: 'CRITICAL',
    field: 'critical_count',
    label: 'Critical',
    bar: 'bg-rose-500',
    tag: 'bg-rose-50 text-rose-700',
  },
  {
    key: 'SIGNIFICANT',
    field: 'significant_count',
    label: 'Significant',
    bar: 'bg-amber-500',
    tag: 'bg-amber-50 text-amber-700',
  },
  {
    key: 'MINOR',
    field: 'minor_count',
    label: 'Minor',
    bar: 'bg-sky-500',
    tag: 'bg-sky-50 text-sky-700',
  },
]

function Distribution({ resource }: { resource: ResourceImpactSummary }) {
  return (
    <div className="space-y-2">
      <div
        className="flex h-3 overflow-hidden rounded-full bg-slate-100"
        aria-label={`${resource.resource_name}: ${resource.publication_count} attributions`}
      >
        {resource.publication_count > 0 &&
          levels.map(({ key, field, bar }) => (
            <div
              key={key}
              className={bar}
              style={{ width: `${(resource[field] / resource.publication_count) * 100}%` }}
              title={`${key}: ${resource[field]}`}
            />
          ))}
      </div>
      <p className="text-xs text-slate-500">
        Critical {resource.critical_count} · Significant {resource.significant_count} · Minor{' '}
        {resource.minor_count}
      </p>
    </div>
  )
}

export default function AttributionsPage() {
  const [chosenId, setChosenId] = useState<number | null>(null)
  const summary = useQuery({
    queryKey: ['attributions', 'summary'],
    queryFn: attributionsApi.summary,
  })
  const resources = summary.data ?? []
  const selected = resources.find((item) => item.resource_id === chosenId) ?? resources[0]
  const detail = useQuery({
    queryKey: ['attributions', 'resource', selected?.resource_id],
    queryFn: () => attributionsApi.byResource(selected!.resource_id),
    enabled: selected !== undefined,
  })
  const totalPairs = resources.reduce((total, resource) => total + resource.publication_count, 0)
  const attributedResources = resources.filter((resource) => resource.publication_count > 0).length

  return (
    <section className="space-y-6">
      <PageHeader
        title="Attributions"
        description="Confirmed publications attributed to each resource, grouped by criticality."
        aside={
          <button
            type="button"
            className={secondaryButton}
            disabled={summary.isFetching || detail.isFetching}
            onClick={() => {
              void summary.refetch()
              if (selected) void detail.refetch()
            }}
          >
            <RefreshCw size={15} className="mr-2 inline" /> Refresh
          </button>
        }
      />

      {summary.isPending ? (
        <div className="panel p-6 text-sm text-slate-500">Loading resource impact…</div>
      ) : summary.isError ? (
        <div role="alert" className="panel space-y-3 p-6 text-sm text-red-700">
          <p>Unable to load attributions: {summary.error.message}</p>
          <button type="button" className={secondaryButton} onClick={() => void summary.refetch()}>
            Retry
          </button>
        </div>
      ) : resources.length === 0 ? (
        <div className="panel p-8 text-sm text-slate-600">
          No resources found. Add resources on the Resources page to begin tracking impact.
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { label: 'Resources tracked', value: resources.length },
              { label: 'Resources with impact', value: attributedResources },
              { label: 'Confirmed resource–publication pairs', value: totalPairs },
            ].map((metric) => (
              <div key={metric.label} className="panel p-5">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  {metric.label}
                </p>
                <p className="mt-3 text-3xl font-bold text-slate-900">{metric.value}</p>
              </div>
            ))}
          </div>
          <div className="panel space-y-5 p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
                <BarChart3 size={19} /> Impact by resource
              </h2>
              <span className="text-xs text-slate-500">
                Select a resource to view its publications
              </span>
            </div>
            <div className="space-y-3">
              {resources.map((resource) => (
                <button
                  key={resource.resource_id}
                  type="button"
                  aria-pressed={selected?.resource_id === resource.resource_id}
                  onClick={() => setChosenId(resource.resource_id)}
                  className={`w-full rounded-xl border p-4 text-left transition-colors ${selected?.resource_id === resource.resource_id ? 'border-blue-500 bg-blue-50/50' : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'}`}
                >
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <span className="font-semibold text-slate-900">{resource.resource_name}</span>
                      <span className="ml-2 text-xs text-slate-500">{resource.resource_type}</span>
                      {!resource.is_active && (
                        <span className="ml-2 text-xs text-amber-700">Inactive</span>
                      )}
                    </div>
                    <span className="text-sm font-medium text-slate-700">
                      {resource.publication_count}{' '}
                      {resource.publication_count === 1 ? 'publication' : 'publications'}
                    </span>
                  </div>
                  <Distribution resource={resource} />
                </button>
              ))}
            </div>
            <p className="text-xs text-slate-500">
              A publication attributed to multiple resources is counted once for each resource.
              Other (not listed) is not counted.
            </p>
          </div>
          {selected && (
            <div className="panel overflow-hidden">
              <div className="border-b border-slate-200 p-5 sm:p-6">
                <h2 className="text-lg font-semibold text-slate-900">
                  Publications — {selected.resource_name}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {selected.publication_count} confirmed attribution
                  {selected.publication_count === 1 ? '' : 's'}
                </p>
              </div>
              {detail.isPending ? (
                <p className="p-6 text-sm text-slate-500">Loading publications…</p>
              ) : detail.isError ? (
                <div className="space-y-3 p-6 text-sm text-red-700" role="alert">
                  <p>Unable to load publications: {detail.error.message}</p>
                  <button className={secondaryButton} onClick={() => void detail.refetch()}>
                    Retry
                  </button>
                </div>
              ) : detail.data.length === 0 ? (
                <p className="p-6 text-sm text-slate-500">
                  No confirmed publications for this resource yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[600px] text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-5 py-4">Publication</th>
                        <th className="px-5 py-4">Publication date</th>
                        <th className="px-5 py-4">Criticality</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {detail.data.map((item) => {
                        const style =
                          levels.find((level) => level.key === item.criticality)?.tag ??
                          'bg-slate-100 text-slate-700'
                        return (
                          <tr key={item.publication_id}>
                            <td className="px-5 py-4">
                              <a
                                className="font-medium text-blue-700 hover:underline"
                                href={`https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(item.pmid)}/`}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {item.title}
                              </a>
                              <div className="mt-1 text-xs text-slate-500">PMID {item.pmid}</div>
                            </td>
                            <td className="px-5 py-4 text-slate-600">
                              {item.publication_date ?? '—'}
                            </td>
                            <td className="px-5 py-4">
                              <span
                                className={`rounded-full px-3 py-1 text-xs font-semibold ${style}`}
                              >
                                {item.criticality}
                              </span>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </section>
  )
}
