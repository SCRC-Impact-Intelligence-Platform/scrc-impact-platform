import { navigation } from '../app/navigation'
import { WorkspacePlaceholder } from '../components/common/WorkspacePlaceholder'

export default function ResourcesPage() {
  const item = navigation.find(item => item.path === '/resources')!
  return <WorkspacePlaceholder item={item} />
}
