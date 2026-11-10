import { apiRequest } from '../../app/api'

export type PublicationStatus =
  'PENDING' | 'SENT' | 'CONFIRMED' | 'REJECTED' | 'UNSURE' | 'NEEDS_REVIEW' | 'DISMISSED'
export type ResourceAttribution = {
  resource_id: number
  resource_name: string
  criticality: 'CRITICAL' | 'SIGNIFICANT' | 'MINOR'
}

export type PublicationConfidence = 'HIGH' | 'LOW'

export type Publication = {
  id: number
  pmid: string
  title: string
  authors: string[]
  journal: string | null
  publication_date: string | null
  doi: string | null
  abstract: string | null
  first_discovered_researcher_id: number | null
  first_discovered_by_orcid: string | null
  discovered_at: string
  status: PublicationStatus
}

export type PublicationFilters = {
  status?: PublicationStatus
  researcher_id?: number
  confidence?: PublicationConfidence
  limit: number
  offset: number
}

export const publicationsApi = {
  list: ({ status, confidence, researcher_id, limit, offset }: PublicationFilters) => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
    if (status) params.set('status', status)
    if (confidence) params.set('confidence', confidence)
    if (researcher_id) params.set('researcher_id', String(researcher_id))
    return apiRequest<Publication[]>(`/publications?${params.toString()}`)
  },
  get: (id: number) => apiRequest<Publication>(`/publications/${id}`),
  attributions: (id: number) =>
    apiRequest<ResourceAttribution[]>(`/publications/${id}/attributions`),
}
