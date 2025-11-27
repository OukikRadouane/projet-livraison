import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  CssBaseline,
  Container,
  Tabs,
  Tab,
  Box,
  AppBar,
  Toolbar,
  Typography,
  ThemeProvider,
  Button,
  Stack,
  Chip,
} from '@mui/material'
import { useEffect, useState } from 'react'
import CourierDashboardPage from './pages/CourierDashboardPage'
import theme from './theme'
import { AuthGatewayDialog } from './components/AuthDialogs'
import CustomerOrderPage from './pages/CustomerOrderPage'
// import CourierDashboardPage from './pages/CourierDashboardPage'
import type { UserProfile } from './components/AuthDialogs'

const qc = new QueryClient()

function App() {
  const [tab, setTab] = useState(0)
  const [authGatewayOpen, setAuthGatewayOpen] = useState(false)
  const [authToken, setAuthToken] = useState<string | null>(null)
  const [authUser, setAuthUser] = useState<UserProfile | null>(null)

  // Restore auth from localStorage on first load
  useEffect(() => {
    try {
      const saved = localStorage.getItem('pl.auth')
      if (saved) {
        const parsed = JSON.parse(saved) as { token: string; user: UserProfile }
        if (parsed?.token && parsed?.user) {
          setAuthToken(parsed.token)
          setAuthUser(parsed.user)
        }
      }
    } catch {}
  }, [])

  // Persist auth to localStorage when it changes
  useEffect(() => {
    try {
      if (authToken && authUser) {
        localStorage.setItem('pl.auth', JSON.stringify({ token: authToken, user: authUser }))
      } else {
        localStorage.removeItem('pl.auth')
      }
    } catch {}
  }, [authToken, authUser])

  const handleLogout = () => {
    setAuthToken(null)
    setAuthUser(null)
  }

  return (
    <QueryClientProvider client={qc}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 45%, #0f766e 100%)',
            color: 'common.white',
          }}
        >
          <AppBar position="static" color="transparent" elevation={0} sx={{ backdropFilter: 'blur(6px)' }}>
            <Toolbar sx={{ alignItems: 'center', gap: 3 }}>
              <Box>
                <Typography variant="h5" fontWeight={600}>
                  Projet Livraison
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.7 }}>
                  Commandez. Livrez. Simplement.
                </Typography>
              </Box>
              <Box sx={{ flexGrow: 1 }} />
              <Stack direction="row" spacing={2} alignItems="center">
                {authUser && (
                  <Chip
                    label={`${authUser.first_name && authUser.last_name ? `${authUser.first_name} ${authUser.last_name}` : authUser.email} · ${authUser.role === 'COURIER' ? 'Livreur' : 'Client'}`}
                    color="secondary"
                    variant="outlined"
                  />
                )}
                {!authUser ? (
                  <>
                    <Button color="inherit" onClick={() => setAuthGatewayOpen(true)}>
                      S'inscrire / Se connecter
                    </Button>
                  </>
                ) : (
                  <Button color="inherit" onClick={handleLogout}>
                    Déconnexion
                  </Button>
                )}
              </Stack>
            </Toolbar>
          </AppBar>
          <Container maxWidth="md" sx={{ py: 6 }}>
            <Box
              sx={{
                bgcolor: 'rgba(15, 23, 42, 0.75)',
                borderRadius: 4,
                boxShadow: '0 30px 80px rgba(15, 23, 42, 0.35)',
                backdropFilter: 'blur(14px)',
                px: { xs: 3, md: 6 },
                py: { xs: 4, md: 6 },
              }}
            >
              <Tabs
                value={tab}
                onChange={(_, v) => setTab(v)}
                textColor="inherit"
                indicatorColor="secondary"
                variant="fullWidth"
              >
                <Tab label="Espace client" sx={{ fontWeight: 600 }} />
                {authUser?.role === 'COURIER' && (
                  <Tab label="Espace livreur" sx={{ fontWeight: 600 }} />
                )}
              </Tabs>
              <Box sx={{ mt: 4 }}>
                {tab === 0 && (
                  <CustomerOrderPage
                    token={authToken}
                    user={authUser}
                    onRequireAuth={() => setAuthGatewayOpen(true)}
                  />
                )}
                {authUser?.role === 'COURIER' && tab === 1 && (
                  <CourierDashboardPage
                    token={authToken}
                    user={authUser}
                    onLogout={handleLogout}
                  />
                )}
              </Box>
            </Box>
          </Container>
          <AuthGatewayDialog
            open={authGatewayOpen}
            onClose={() => setAuthGatewayOpen(false)}
            onLoginSuccess={({ token, user }) => {
              setAuthToken(token)
              setAuthUser(user)
              setAuthGatewayOpen(false)
            }}
          />
        </Box>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
