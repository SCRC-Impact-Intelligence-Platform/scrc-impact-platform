import { apiRequest } from '../../app/api'

export type Criticality = 'CRITICAL' | 'SIGNIFICANT' | 'MINOR'

export type ResourceImpactSummary = {
  resource_id: number
  resource_name: string
  resource_type: 'EQUIPMENT' | 'FUNDING' | 'SERVICE'
  is_active: boolean
  publication_count: number
  critical_count: number
  significant_count: number
  minor_count: number
}

export type ResourcePublicationAttribution = {
  publication_id: number
  pmid: string
  title: string
  publication_date: string | null
  criticality: Criticality
}

export const attributionsApi = {
  summary: () => apiRequest<ResourceImpactSummary[]>('/attributions/summary'),
  byResource: (resourceId: number) =>
    apiRequest<ResourcePublicationAttribution[]>(`/resources/${resourceId}/attributions`),
}
