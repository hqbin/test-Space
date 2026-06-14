import { ThemeProvider, CssBaseline } from '@mui/material'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { theme } from './theme'
import { MainLayout } from '@components/Layout/MainLayout'
import { ErrorBoundary } from '@components/common/ErrorBoundary'
import { NotificationProvider } from '@components/common/Notification'
import { LocalAgentDetector } from '@components/LocalAgentDetector'
import { DashboardPage } from './pages/DashboardPage'
import { ScreenPage } from './pages/ScreenPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <NotificationProvider>
          <LocalAgentDetector>
            <BrowserRouter
              basename="/adb-tool"
              future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true,
              }}
            >
              <MainLayout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/screen" element={<ScreenPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </MainLayout>
            </BrowserRouter>
          </LocalAgentDetector>
        </NotificationProvider>
      </ErrorBoundary>
    </ThemeProvider>
  )
}

export default App
