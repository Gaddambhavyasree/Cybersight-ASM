import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import DashboardLayout from './components/layout/DashboardLayout'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import VerifyEmailPage from './pages/auth/VerifyEmailPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import ProfilePage from './pages/dashboard/ProfilePage'
import ProjectsPage from './pages/projects/ProjectsPage'
import ScansPage from './pages/scans/ScansPage'
import AssetsPage from './pages/assets/AssetsPage'
import PortsPage from './pages/discovery/PortsPage'
import TechnologiesPage from './pages/discovery/TechnologiesPage'
import DnsIntelligencePage from './pages/intelligence/DnsIntelligencePage'
import SslAnalysisPage from './pages/intelligence/SslAnalysisPage'
import WebCrawlingPage from './pages/intelligence/WebCrawlingPage'
import VulnerabilitiesPage from './pages/intelligence/VulnerabilitiesPage'
import ThreatIntelPage from './pages/intelligence/ThreatIntelPage'
import RiskAssessmentPage from './pages/analysis/RiskAssessmentPage'
import HistoryPage from './pages/analysis/HistoryPage'
import ReportsPage from './pages/analysis/ReportsPage'
import NotificationsPage from './pages/system/NotificationsPage'
import SettingsPage from './pages/system/SettingsPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import NotFoundPage from './pages/errors/NotFoundPage'
import ForbiddenPage from './pages/errors/ForbiddenPage'

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<PublicRoute><ForgotPasswordPage /></PublicRoute>} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="scans" element={<ScansPage />} />
        <Route path="assets" element={<AssetsPage />} />
        <Route path="ports" element={<PortsPage />} />
        <Route path="technologies" element={<TechnologiesPage />} />
        <Route path="dns" element={<DnsIntelligencePage />} />
        <Route path="ssl" element={<SslAnalysisPage />} />
        <Route path="web-crawling" element={<WebCrawlingPage />} />
        <Route path="vulnerabilities" element={<VulnerabilitiesPage />} />
        <Route path="threat-intel" element={<ThreatIntelPage />} />
        <Route path="risk" element={<RiskAssessmentPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route
          path="admin/users"
          element={
            <ProtectedRoute adminOnly>
              <AdminUsersPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/forbidden" element={<ForbiddenPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
