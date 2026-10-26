import { navigation } from '../app/navigation'
import { WorkspacePlaceholder } from '../components/common/WorkspacePlaceholder'

export default function SettingsPage() {
  const item = navigation.find(item => item.path === '/settings')!
  return <WorkspacePlaceholder item={item} />
}
