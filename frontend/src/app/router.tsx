import { createBrowserRouter, Navigate } from 'react-router-dom'
import App from '../App'
import DashboardPage from '../pages/DashboardPage'
import ResearchersPage from '../pages/ResearchersPage'
import PublicationsPage from '../pages/PublicationsPage'
import FormsPage from '../pages/FormsPage'
import ResourcesPage from '../pages/ResourcesPage'
import AttributionsPage from '../pages/AttributionsPage'
import SettingsPage from '../pages/SettingsPage'
import NotFoundPage from '../pages/NotFoundPage'

// Layout route: children render inside <Outlet /> in AppLayout.
// Add new pages here; keep feature UI outside the route configuration.
export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'researchers', element: <ResearchersPage /> },
      { path: 'publications', element: <PublicationsPage /> },
      { path: 'forms', element: <FormsPage /> },
      { path: 'resources', element: <ResourcesPage /> },
      { path: 'attributions', element: <AttributionsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
