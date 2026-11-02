import { apiRequest } from '../../app/api'

export type PublicationStatus = 'PENDING' | 'SENT' | 'CONFIRMED' | 'REJECTED' | 'DISMISSED'

export type Publication = {
  id: number
  pmid: string
  title: string
  authors: string[]
  journal: string | null
  publication_date: string | null
  doi: string | null
  abstract: string | null
  first_discovered_by_orcid: string
  discovered_at: string
  status: PublicationStatus
}

export type PublicationFilters = {
  status?: PublicationStatus
  limit: number
  offset: number
}

export const publicationsApi = {
  list: ({ status, limit, offset }: PublicationFilters) => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
    if (status) params.set('status', status)
    return apiRequest<Publication[]>(`/publications?${params.toString()}`)
  },
  get: (id: number) => apiRequest<Publication>(`/publications/${id}`),
}
