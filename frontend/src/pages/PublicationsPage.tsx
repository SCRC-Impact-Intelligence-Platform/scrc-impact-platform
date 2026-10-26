import { navigation } from '../app/navigation'
import { WorkspacePlaceholder } from '../components/common/WorkspacePlaceholder'

export default function PublicationsPage() {
  const item = navigation.find(item => item.path === '/publications')!
  return <WorkspacePlaceholder item={item} />
}
