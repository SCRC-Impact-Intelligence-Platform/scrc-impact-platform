import type { ReactNode } from 'react'

type Props = { title: string; description: string; eyebrow?: string; aside?: ReactNode }

export function PageHeader({ title, description, eyebrow = 'SCRC Impact Intelligence', aside }: Props) {
  return <div className="flex flex-wrap items-start justify-between gap-4">
    <div><div className="eyebrow">{eyebrow}</div><h1 className="page-title">{title}</h1><p className="muted mt-2">{description}</p></div>
    {aside}
  </div>
}
