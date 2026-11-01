import { Link } from 'react-router-dom'
import { PageHeader } from '../components/common/PageHeader'

export default function NotFoundPage() {
  return <section className="space-y-6">
    <PageHeader title="Page not found" description="The requested workspace does not exist." eyebrow="404 / Navigation" />
    <div className="panel p-8"><Link to="/dashboard" className="text-sm font-semibold text-blue-700 hover:underline">Return to dashboard</Link></div>
  </section>
}
