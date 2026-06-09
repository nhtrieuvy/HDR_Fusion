import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { ArtifactPage } from './pages/ArtifactPage'
import { DashboardPage } from './pages/DashboardPage'
import { ExportPage } from './pages/ExportPage'
import { HistoryPage } from './pages/HistoryPage'
import { JobDetailPage } from './pages/JobDetailPage'
import { NewHDRJobPage } from './pages/NewHDRJobPage'
import { PreviewPage } from './pages/PreviewPage'
import { ProcessingPage } from './pages/ProcessingPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'
import { UploadPage } from './pages/UploadPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'upload', element: <UploadPage /> },
      { path: 'processing', element: <ProcessingPage /> },
      { path: 'preview', element: <PreviewPage /> },
      { path: 'export', element: <ExportPage /> },
      { path: 'history', element: <HistoryPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'projects', element: <ProjectsPage /> },
      { path: 'projects/:projectId', element: <ProjectDetailPage /> },
      { path: 'jobs/new', element: <NewHDRJobPage /> },
      { path: 'jobs/:jobId', element: <JobDetailPage /> },
      { path: 'artifacts', element: <ArtifactPage /> },
      { path: 'artifacts/:artifactId', element: <ArtifactPage /> },
    ],
  },
])
