import { navigation } from '../app/navigation'
import { WorkspacePlaceholder } from '../components/common/WorkspacePlaceholder'

export default function AttributionsPage() {
  const item = navigation.find(item => item.path === '/attributions')!
  return <WorkspacePlaceholder item={item} />
}
