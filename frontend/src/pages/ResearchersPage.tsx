import { navigation } from '../app/navigation'
import { WorkspacePlaceholder } from '../components/common/WorkspacePlaceholder'

export default function ResearchersPage() {
  const item = navigation.find(item => item.path === '/researchers')!
  return <WorkspacePlaceholder item={item} />
}
