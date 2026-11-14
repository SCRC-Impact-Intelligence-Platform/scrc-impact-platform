import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink, FileText } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import type { Criticality } from '../features/attributions/api'
import { Feedback, primaryButton, secondaryButton } from '../features/directory/DirectoryUI'
import { researcherName, researchersApi } from '../features/directory/api'
import { pubmedUrl, type Publication } from '../features/publications/api'
import {
  type AttributedPublication,
  type QuarterlyReport,
  periodLabel,
  recentPeriods,
  reportExportUrl,
  reportsApi,
  type ReportingPeriod,
} from '../features/reports/api'

const PERIOD_COUNT = 8
const keyOf = ({ year, quarter }: ReportingPeriod) => `${year}-Q${quarter}`

/** Verified publications that a report had to leave out, so its totals can be checked. */
function ExcludedNote({ publications, reason }: { publications: Publication[]; reason: string }) {
  if (publications.length === 0) return null
  return (
    <details className="border-b border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-900">
      <summary className="cursor-pointer">
        {publications.length} verified publication{publications.length === 1 ? '' : 's'} {reason}
      </summary>
      <ul className="mt-2 list-disc space-y-1 pl-5">
        {publications.map((p) => (
          <li key={p.id}>
            {p.title} ({p.publication_date ?? 'no date'}, PMID {p.pmid})
          </li>
        ))}
      </ul>
    </details>
  )
}

function SummaryStats({ report }: { report: QuarterlyReport }) {
  const s = report.attribution_summary
  const stats = [
    ['Verified this quarter', report.publications.length],
    ['Attributed this quarter', s.attributed_in_period],
    ['Attributed to grants this quarter', s.grant_attributed_in_period],
    ['Attributed, all time', s.attributed_total],
    ['Attributed to grants, all time', s.grant_attributed_total],
  ] as const
  return (
    <dl className="grid grid-cols-2 gap-px border-b border-slate-200 bg-slate-200 sm:grid-cols-3 lg:grid-cols-5">
      {stats.map(([label, value]) => (
        <div key={label} className="bg-white px-5 py-3">
          <dt className="text-xs text-slate-500">{label}</dt>
          <dd className="text-xl font-bold text-slate-900">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

const criticalityLabel = (c: Criticality) => c.charAt(0) + c.slice(1).toLowerCase()

function AttributedList({ items }: { items: AttributedPublication[] }) {
  return (
    <div className="border-b border-slate-200">
      <h3 className="px-5 pt-4 text-sm font-semibold text-slate-900">
        Attributed publications ({items.length})
      </h3>
      {items.length === 0 ? (
        <p className="px-5 py-3 text-sm text-slate-500">
          No attributed publications in this period.
        </p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.map(({ publication: p, resources }) => (
            <li key={p.id} className="px-5 py-3 text-sm">
              <p className="font-medium text-slate-900">{p.title}</p>
              <p className="mt-1 flex flex-wrap gap-1.5">
                {resources.map((r) => (
                  <span
                    key={r.resource_id}
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      r.resource_type === 'FUNDING'
                        ? 'bg-emerald-50 text-emerald-800'
                        : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {r.resource_name} · {criticalityLabel(r.criticality)}
                  </span>
                ))}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function ReportsPage() {
  // Recomputed each render so a tab left open across a quarter boundary picks up the new quarter.
  const periods = recentPeriods(PERIOD_COUNT)
  const [chosen, setChosen] = useState(keyOf(periods[0]))
  // If the chosen period rolled off the list, fall back to the newest one.
  const selected = periods.some((p) => keyOf(p) === chosen) ? chosen : keyOf(periods[0])
  // The report only runs when "Generate Report" is pressed, not on every select change.
  const [generated, setGenerated] = useState<ReportingPeriod | null>(null)
  const report = useQuery({
    queryKey: ['reports', 'quarterly', generated],
    queryFn: () => reportsApi.quarterly(generated!),
    enabled: generated !== null,
  })
  const researchers = useQuery({ queryKey: ['researchers'], queryFn: researchersApi.list })
  const nameFor = (id: number | null) => researcherName(researchers.data, id)

  return (
    <section className="space-y-6">
      <PageHeader
        title="Report Builder"
        description="Generate a list of verified publications for a reporting period."
      />
      <form
        className="panel flex flex-wrap items-end gap-4 p-5"
        onSubmit={(event) => {
          event.preventDefault()
          // Same period again: refetch so newly verified publications show up.
          if (generated && keyOf(generated) === selected) void report.refetch()
          else setGenerated(periods.find((p) => keyOf(p) === selected)!)
        }}
      >
        <label className="space-y-1 text-sm font-medium text-slate-700">
          <span className="block">Reporting period</span>
          <select
            className="min-w-56 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            value={selected}
            onChange={(e) => setChosen(e.target.value)}
          >
            {periods.map((p) => (
              <option key={keyOf(p)} value={keyOf(p)}>
                {periodLabel(p)}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className={primaryButton} disabled={report.isFetching}>
          Generate Report
        </button>
      </form>

      {generated && (
        <div className="panel overflow-hidden">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 p-5">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Verified publications · {periodLabel(generated)}
              </h2>
              {report.data && (
                <p className="muted mt-1 text-sm">
                  {report.data.publications.length} publication
                  {report.data.publications.length === 1 ? '' : 's'}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <a className={secondaryButton} href={reportExportUrl(generated, 'pdf')} download>
                Export PDF
              </a>
              <a className={secondaryButton} href={reportExportUrl(generated, 'xlsx')} download>
                Export Excel
              </a>
            </div>
          </div>
          {report.data && (
            <>
              <SummaryStats report={report.data} />
              <AttributedList items={report.data.attributed_publications} />
              <h3 className="px-5 pt-4 text-sm font-semibold text-slate-900">
                All verified publications
              </h3>
              <ExcludedNote
                publications={report.data.undated_publications}
                reason={`from ${report.data.year} with no month in the PubMed date couldn't be placed in a quarter.`}
              />
              <ExcludedNote
                publications={report.data.no_date_publications}
                reason="with no readable publication date can't be placed in any report period."
              />
            </>
          )}
          {report.isPending ? (
            <p className="p-6 text-sm text-slate-500">Generating report…</p>
          ) : report.isError ? (
            <div className="space-y-3 p-6">
              <Feedback message={report.error.message} />
              <button className={secondaryButton} onClick={() => void report.refetch()}>
                Retry
              </button>
            </div>
          ) : report.data.publications.length === 0 ? (
            <div className="space-y-2 p-8 text-center">
              <FileText className="mx-auto text-slate-400" />
              <p className="font-medium text-slate-800">No verified publications in this period</p>
            </div>
          ) : (
            <ol className="divide-y divide-slate-100">
              {report.data.publications.map((p, index) => (
                <li key={p.id} className="flex gap-4 px-5 py-4 text-sm">
                  <span className="w-6 shrink-0 text-right text-slate-400">{index + 1}.</span>
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-900">{p.title}</p>
                    <p className="mt-1 text-slate-600">{p.authors.join(', ')}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {p.journal || 'Unknown journal'} · {p.publication_date} ·{' '}
                      {nameFor(p.first_discovered_researcher_id)} ·{' '}
                      <a
                        className="text-blue-700 underline underline-offset-2"
                        href={pubmedUrl(p.pmid)}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        PMID {p.pmid} <ExternalLink size={11} className="inline" />
                      </a>
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </section>
  )
}
