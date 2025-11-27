import { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  Tab,
  Tabs,
  Typography,
  Alert,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
} from '@mui/material'
import axios from 'axios'
import OptimizedRouteMap from '../components/OptimizedRouteMap'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import RouteIcon from '@mui/icons-material/Route'

interface UserProfile {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: 'COURIER' | 'CUSTOMER'
}

interface CourierOptimizationPageProps {
  token: string | null
  user: UserProfile | null
  onLogout: () => void
}

interface OptimizedRoute {
  id: number
  total_distance: number
  total_time: number
  total_profit: number
  is_active: boolean
  created_at: string
  stops: any[]
}

const API_BASE = 'http://localhost:8000/api'

export default function CourierOptimizationPage({ token, user, onLogout }: CourierOptimizationPageProps) {
  const [tab, setTab] = useState(0)
  const [routes, setRoutes] = useState<OptimizedRoute[]>([])
  const [selectedRoute, setSelectedRoute] = useState<OptimizedRoute | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [confirmDialog, setConfirmDialog] = useState<{ open: boolean; type: 'activate' | 'deactivate'; route: OptimizedRoute | null }>({
    open: false,
    type: 'activate',
    route: null,
  })

  if (!token || !user || user.role !== 'COURIER') {
    return (
      <Alert severity="error">
        Vous devez être connecté en tant que livreur pour accéder à cette page.
        <Button size="small" onClick={onLogout} sx={{ ml: 2 }}>
          Retour
        </Button>
      </Alert>
    )
  }

  // Charger la liste des routes existantes
  const loadRoutes = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(`${API_BASE}/logistics/optimized-routes/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setRoutes(response.data.results || response.data)
    } catch (err: any) {
      setError(`Erreur lors du chargement des routes: ${err.response?.data?.error || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Calculer une nouvelle route optimisée
  const calculateRoute = async () => {
    try {
      setLoading(true)
      setError(null)
      setSuccess(null)
      const response = await axios.post(`${API_BASE}/logistics/optimized-routes/calculate_route/`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const newRoute = response.data
      setRoutes([newRoute, ...routes])
      setSelectedRoute(newRoute)
      setSuccess('Route calculée avec succès ! Cliquez sur "Activer" pour démarrer.')
      setTab(1) // Aller à l'onglet des routes
    } catch (err: any) {
      setError(`Erreur lors du calcul: ${err.response?.data?.error || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Activer une route
  const activateRoute = async (route: OptimizedRoute) => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.post(`${API_BASE}/logistics/optimized-routes/${route.id}/activate_route/`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const updatedRoute = response.data.route
      setRoutes(routes.map((r) => (r.id === route.id ? updatedRoute : r)))
      setSelectedRoute(updatedRoute)
      setSuccess(`Route #${route.id} activée! Les clients ont été notifiés.`)
      setConfirmDialog({ open: false, type: 'activate', route: null })
    } catch (err: any) {
      setError(`Erreur lors de l'activation: ${err.response?.data?.error || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Désactiver une route
  const deactivateRoute = async (route: OptimizedRoute) => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.post(`${API_BASE}/logistics/optimized-routes/${route.id}/deactivate_route/`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const updatedRoute = response.data.route || response.data
      setRoutes(routes.map((r) => (r.id === route.id ? updatedRoute : r)))
      setSelectedRoute(null)
      setSuccess(`Route #${route.id} désactivée.`)
      setConfirmDialog({ open: false, type: 'deactivate', route: null })
    } catch (err: any) {
      setError(`Erreur lors de la désactivation: ${err.response?.data?.error || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Stack spacing={3}>
      {/* En-tête avec infos du livreur */}
      <Paper sx={{ p: 3, bgcolor: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(8px)' }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Optimisation de Tournée
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.7, mt: 0.5 }}>
              Bienvenue, {user.first_name || user.username}! Capacité: 10 kg
            </Typography>
          </Box>
          <RouteIcon sx={{ fontSize: 48, opacity: 0.5 }} />
        </Stack>
      </Paper>

      {/* Messages d'erreur/succès */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Onglets */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} textColor="inherit">
          <Tab label="Calculer une route" sx={{ fontWeight: 600 }} />
          <Tab label="Mes routes" sx={{ fontWeight: 600 }} />
        </Tabs>
      </Box>

      {/* Onglet 1: Calculer une route */}
      {tab === 0 && (
        <Stack spacing={3}>
          <Paper sx={{ p: 4, bgcolor: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(8px)', textAlign: 'center' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Calculer l'itinéraire optimal
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.7, mb: 3 }}>
              Le système va analyser toutes les commandes en attente, les regrouper par proximité, chercher les magasins les
              plus proches, et calculer l'ordre de visite optimal pour minimiser la distance et maximiser vos gains.
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={calculateRoute}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <RouteIcon />}
              sx={{ px: 4, py: 1.5 }}
            >
              {loading ? 'Calcul en cours...' : 'Calculer la route optimale'}
            </Button>
          </Paper>

          {selectedRoute && (
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Route calculée
              </Typography>
              <OptimizedRouteMap route={selectedRoute} />
            </Box>
          )}
        </Stack>
      )}

      {/* Onglet 2: Mes routes */}
      {tab === 1 && (
        <Stack spacing={3}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Mes routes ({routes.length})
            </Typography>
            <Button variant="outlined" size="small" onClick={loadRoutes} disabled={loading}>
              Rafraîchir
            </Button>
          </Box>

          {loading && routes.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          ) : routes.length === 0 ? (
            <Alert severity="info">Aucune route calculée. Commencez par en calculer une.</Alert>
          ) : (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
              {routes.map((route) => (
                <Card
                  key={route.id}
                  sx={{
                    cursor: 'pointer',
                    bgcolor: 'rgba(255,255,255,0.05)',
                    backdropFilter: 'blur(8px)',
                    border: selectedRoute?.id === route.id ? '2px solid #4ECDC4' : '1px solid rgba(255,255,255,0.1)',
                    transition: 'all 0.3s',
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.08)',
                      transform: 'translateY(-2px)',
                    },
                  }}
                  onClick={() => setSelectedRoute(route)}
                >
                  <CardContent>
                    <Stack spacing={2}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                        <Box>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            Route #{route.id}
                          </Typography>
                          <Typography variant="caption" sx={{ opacity: 0.7 }}>
                            {new Date(route.created_at).toLocaleString('fr-FR')}
                          </Typography>
                        </Box>
                        <Chip
                          label={route.is_active ? '🟢 Actif' : '🔴 Inactif'}
                          size="small"
                          color={route.is_active ? 'success' : 'default'}
                        />
                      </Box>

                      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                        <Chip
                          icon={<TrendingDownIcon />}
                          label={`${route.total_distance.toFixed(1)} km`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={`${Math.round(route.total_time)} min`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          icon={<TrendingUpIcon />}
                          label={`${route.total_profit.toFixed(2)} DH`}
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                        <Chip label={`${route.stops.length} arrêts`} size="small" variant="outlined" />
                      </Stack>

                      <Stack direction="row" spacing={1}>
                        {!route.is_active ? (
                          <Button
                            variant="contained"
                            size="small"
                            fullWidth
                            onClick={(e) => {
                              e.stopPropagation()
                              setConfirmDialog({ open: true, type: 'activate', route })
                            }}
                          >
                            Activer
                          </Button>
                        ) : (
                          <Button
                            variant="contained"
                            color="error"
                            size="small"
                            fullWidth
                            onClick={(e) => {
                              e.stopPropagation()
                              setConfirmDialog({ open: true, type: 'deactivate', route })
                            }}
                          >
                            Désactiver
                          </Button>
                        )}
                      </Stack>
                    </Stack>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}

          {selectedRoute && (
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Détail de la route sélectionnée
              </Typography>
              <OptimizedRouteMap route={selectedRoute} />
            </Box>
          )}
        </Stack>
      )}

      {/* Dialog de confirmation */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}>
        <DialogTitle>
          {confirmDialog.type === 'activate'
            ? 'Activer la route'
            : 'Désactiver la route'}
        </DialogTitle>
        <DialogContent>
          <Typography>
            {confirmDialog.type === 'activate'
              ? `Êtes-vous sûr de vouloir activer la route #${confirmDialog.route?.id}? Les commandes seront assignées et les clients seront notifiés.`
              : `Êtes-vous sûr de vouloir désactiver la route #${confirmDialog.route?.id}? Les commandes non livrées repasseront en PENDING.`}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>Annuler</Button>
          <Button
            variant="contained"
            color={confirmDialog.type === 'activate' ? 'success' : 'error'}
            onClick={() => {
              if (confirmDialog.route) {
                if (confirmDialog.type === 'activate') {
                  activateRoute(confirmDialog.route)
                } else {
                  deactivateRoute(confirmDialog.route)
                }
              }
            }}
            disabled={loading}
          >
            {confirmDialog.type === 'activate' ? 'Activer' : 'Désactiver'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}
