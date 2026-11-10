import { apiRequest } from '../../app/api'

export type FormBatch = {
  id: number
  researcher_id: number | null
  invitation_to: string | null
  invitation_sent_at: string | null
  google_form_id: string | null
  responder_url: string | null
  state: 'CREATING' | 'READY' | 'SENT' | 'COMPLETED' | 'FAILED'
  created_at: string
}
export type FormCreated = {
  batch_id: number
  google_form_id: string
  responder_url: string
  state: string
}
export type InvitationDraft = { to: string; subject: string; body: string }

export const formsApi = {
  list: () => apiRequest<FormBatch[]>('/forms'),
  create: (payload: {
    researcher_id: number
    items: { publication_id: number; resource_ids: number[] }[]
  }) => apiRequest<FormCreated>('/forms', { method: 'POST', body: JSON.stringify(payload) }),
  draft: (id: number) => apiRequest<InvitationDraft>(`/forms/${id}/invitation-draft`),
  send: (id: number, subject: string, body: string) =>
    apiRequest<{ state: string; recipient: string }>(`/forms/${id}/send-invitation`, {
      method: 'POST',
      body: JSON.stringify({ subject, body }),
    }),
}
