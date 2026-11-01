import { navigation } from '../app/navigation'
import { WorkspacePlaceholder } from '../components/common/WorkspacePlaceholder'

export default function FormsPage() {
  const item = navigation.find(item => item.path === '/forms')!
  return <WorkspacePlaceholder item={item} />
}
