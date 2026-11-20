import { apiRequest } from '../../app/api'

export type Researcher = {
  id: number
  name: string
  orcid: string | null
  email: string
  is_active: boolean
}
export type ResourceType = 'EQUIPMENT' | 'FUNDING' | 'SERVICE'
export type Resource = { id: number; name: string; type: ResourceType; is_active: boolean }
export type ResearcherCreate = { name: string; orcid: string | null; email: string }
export type ResearcherUpdate = {
  name?: string
  email?: string
  orcid?: string | null
  is_active?: boolean
}
export type ResourceCreate = { name: string; type: ResourceType }
export type ResourceUpdate = { name?: string; type?: ResourceType; is_active?: boolean }

/** Display name for a researcher id, with fallbacks for unknown or unattributed records. */
export function researcherName(researchers: Researcher[] | undefined, id: number | null): string {
  if (id === null) return 'Unknown (historical)'
  return researchers?.find((r) => r.id === id)?.name ?? `Researcher #${id}`
}

const mutation = <T>(method: string, path: string, body?: object) =>
  apiRequest<T>(path, { method, ...(body ? { body: JSON.stringify(body) } : {}) })

export const researchersApi = {
  list: () => apiRequest<Researcher[]>('/researchers'),
  create: (payload: ResearcherCreate) => mutation<Researcher>('POST', '/researchers', payload),
  update: (id: number, payload: ResearcherUpdate) =>
    mutation<Researcher>('PATCH', `/researchers/${id}`, payload),
  remove: (id: number) => mutation<void>('DELETE', `/researchers/${id}`),
}

export const resourcesApi = {
  list: () => apiRequest<Resource[]>('/resources'),
  create: (payload: ResourceCreate) => mutation<Resource>('POST', '/resources', payload),
  update: (id: number, payload: ResourceUpdate) =>
    mutation<Resource>('PATCH', `/resources/${id}`, payload),
  remove: (id: number) => mutation<void>('DELETE', `/resources/${id}`),
}
