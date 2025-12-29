import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  FormControlLabel,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Stack,
  Switch,
  Tooltip,
  Typography,
} from '@mui/material'
import TextField from '@mui/material/TextField'
import IconButton from '@mui/material/IconButton'
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded'
import DirectionsBikeRoundedIcon from '@mui/icons-material/DirectionsBikeRounded'
import LoginRoundedIcon from '@mui/icons-material/LoginRounded'
import AccessTimeRoundedIcon from '@mui/icons-material/AccessTimeRounded'
import PaidRoundedIcon from '@mui/icons-material/PaidRounded'
import axios from 'axios'
import RouteOptimizationDetails from '../components/RouteOptimizationDetails'
import OptimizedRouteDisplay from '../components/OptimizedRouteDisplay'
import type { UserProfile } from '../components/AuthDialogs'
import 'leaflet/dist/leaflet.css'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap, Polyline } from 'react-leaflet'
import L from 'leaflet'
import type { LatLngExpression } from 'leaflet'

interface Order {
  id: number
  status: string
  customer_phone: string
  delivery_price_offer: string
  courier: number | null
  total_weight_kg: number
  delivered_at: string | null
  location_lat: number
  location_lng: number
}

interface OrderItemDetail {
  item_id: number
  name: string
  weight_per_unit_kg: number
  quantity: number
}

interface OrderDetail extends Order {
  items: OrderItemDetail[]
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

interface Props {
  token: string | null
  user: UserProfile | null
  onLogout: () => void
}

export default function CourierDashboardPage({ token, user, onLogout }: Props) {
  const qc = useQueryClient()
  const [availability, setAvailability] = useState(true)
  const [acceptError, setAcceptError] = useState<string | null>(null)
  const [cancelError, setCancelError] = useState<string | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [geoLoading, setGeoLoading] = useState(false)
  const [geoError, setGeoError] = useState<string | null>(null)
  const [myPos, setMyPos] = useState<{ lat: number; lng: number } | null>(null)
  const [routeCoords, setRouteCoords] = useState<Array<[number, number]> | null>(null)
  const [routeLoading, setRouteLoading] = useState(false)
  const [routeError, setRouteError] = useState<string | null>(null)
  const [fitTrigger, setFitTrigger] = useState(0)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [optCapacityKm, setOptCapacityKm] = useState<number>(10)
  const [optSuggested, setOptSuggested] = useState<number[] | null>(null)
  const [optimizationResult, setOptimizationResult] = useState<any>(null)
  const [details, setDetails] = useState<Record<number, OrderDetail | null>>({})
  const [optimizedRoute, setOptimizedRoute] = useState<Array<[number, number]> | null>(null)

  const toggleExpanded = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const loadDetails = async (id: number) => {
    try {
      if (!token) return
      const response = await axios.get(`${API_BASE}/orders/${id}/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setDetails((d) => ({ ...d, [id]: response.data as OrderDetail }))
    } catch (e) {
      setDetails((d) => ({ ...d, [id]: null }))
    }
  }

  const { data: orders, isFetching } = useQuery<Order[]>({
    queryKey: ['pendingOrders', token],
    queryFn: async () => {
      if (!token) {
        return []
      }
      const response = await axios.get(`${API_BASE}/orders/pending/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    enabled: !!token && availability && user?.role === 'COURIER',
    refetchInterval: 8000,
  })

  const { data: activeOrders, isFetching: isFetchingActive } = useQuery<Order[]>({
    queryKey: ['activeOrders', token],
    queryFn: async () => {
      if (!token) {
        return []
      }
      const response = await axios.get(`${API_BASE}/orders/courier/active/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    enabled: !!token && user?.role === 'COURIER',
    refetchInterval: 8000,
  })

  const acceptMutation = useMutation({
    mutationFn: async (id: number) => {
      if (!token) {
        throw new Error('Non authentifié')
      }
      return (
        await axios.post(
          `${API_BASE}/orders/${id}/accept/`,
          {},
          { headers: { Authorization: `Bearer ${token}` } },
        )
      ).data
    },
    onSuccess: () => {
      setAcceptError(null)
      qc.invalidateQueries({ queryKey: ['pendingOrders', token] })
      qc.invalidateQueries({ queryKey: ['activeOrders', token] })
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || 'Échec de l’acceptation de la commande.'
        : 'Échec de l’acceptation de la commande.'
      setAcceptError(message)
    },
  })

  const cancelMutation = useMutation({
    mutationFn: async (id: number) => {
      if (!token) {
        throw new Error('Non authentifié')
      }
      return (
        await axios.post(
          `${API_BASE}/orders/${id}/cancel/`,
          {},
          { headers: { Authorization: `Bearer ${token}` } },
        )
      ).data
    },
    onSuccess: () => {
      setCancelError(null)
      qc.invalidateQueries({ queryKey: ['pendingOrders', token] })
      qc.invalidateQueries({ queryKey: ['activeOrders', token] })
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || "Impossible d'annuler la commande."
        : "Impossible d'annuler la commande."
      setCancelError(message)
    },
  })

  const statusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: 'PICKED_UP' | 'DELIVERED' }) => {
      if (!token) {
        throw new Error('Non authentifié')
      }
      return (
        await axios.patch(
          `${API_BASE}/orders/${id}/status/`,
          { status },
          { headers: { Authorization: `Bearer ${token}` } },
        )
      ).data
    },
    onSuccess: () => {
      setStatusError(null)
      qc.invalidateQueries({ queryKey: ['pendingOrders', token] })
      qc.invalidateQueries({ queryKey: ['activeOrders', token] })
      qc.invalidateQueries({ queryKey: ['completedOrders', token] })
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || "Impossible de mettre à jour le statut."
        : "Impossible de mettre à jour le statut."
      setStatusError(message)
    },
  })

  const { data: completedOrders, isFetching: isFetchingCompleted } = useQuery<Order[]>({
    queryKey: ['completedOrders', token],
    queryFn: async () => {
      if (!token) {
        return []
      }
      const response = await axios.get(`${API_BASE}/orders/courier/completed/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return response.data
    },
    enabled: !!token && user?.role === 'COURIER',
    refetchInterval: 12000,
  })

  const [showHistory, setShowHistory] = useState(false)
  const [historyDate, setHistoryDate] = useState<string>('')

  const todaysCompleted = useMemo(() => {
    if (!completedOrders) return []
    const today = new Date()
    const y = today.getFullYear()
    const m = today.getMonth()
    const d = today.getDate()
    return completedOrders.filter((o) => {
      if (!o.delivered_at) return false
      const dt = new Date(o.delivered_at)
      return dt.getFullYear() === y && dt.getMonth() === m && dt.getDate() === d
    })
  }, [completedOrders])

  const deleteAllHistory = async () => {
    if (!token) return
    await axios.delete(`${API_BASE}/orders/courier/completed/delete/all/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    qc.invalidateQueries({ queryKey: ['completedOrders', token] })
  }

  const deleteOneHistory = async (id: number) => {
    if (!token) return
    await axios.delete(`${API_BASE}/orders/courier/completed/delete/${id}/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    qc.invalidateQueries({ queryKey: ['completedOrders', token] })
  }

  const deleteByDateHistory = async () => {
    if (!token || !historyDate) return
    await axios.delete(`${API_BASE}/orders/courier/completed/delete/by-date/`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { date: historyDate },
    })
    qc.invalidateQueries({ queryKey: ['completedOrders', token] })
  }

  const totalPotential = useMemo(() => {
    if (!orders) return 0
    return orders.reduce((acc, order) => acc + parseFloat(order.delivery_price_offer || '0'), 0)
  }, [orders])

  const activeWeight = useMemo(() => {
    if (!activeOrders) return 0
    return activeOrders.reduce((acc, order) => acc + (order.total_weight_kg || 0), 0)
  }, [activeOrders])

  const capacity = user?.capacity_kg ?? 0

  const remainingCapacity = Math.max(capacity - activeWeight, 0)

  const completedTotal = useMemo(() => {
    if (!completedOrders) return 0
    return completedOrders.reduce((acc, order) => acc + parseFloat(order.delivery_price_offer || '0'), 0)
  }, [completedOrders])

  const handleUseMyLocation = () => {
    if (!navigator?.geolocation) {
      setGeoError("La géolocalisation n'est pas disponible sur ce navigateur.")
      return
    }
    setGeoLoading(true)
    setGeoError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setMyPos({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setGeoLoading(false)
      },
      (err) => {
        const messages: Record<number, string> = {
          1: "Permission refusée pour la géolocalisation.",
          2: 'Position indisponible pour le moment.',
          3: 'Délai dépassé lors de la géolocalisation.',
        }
        setGeoError(messages[err.code] || 'Impossible de récupérer votre position.')
        setGeoLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  const requestRoute = async (dest: { lat: number; lng: number }) => {
    if (!myPos) {
      setRouteError("Activez d'abord votre position pour tracer un itinéraire.")
      return
    }
    try {
      setRouteLoading(true)
      setRouteError(null)
      // OSRM public demo server (best effort, non garanti pour la prod)
      const url = `https://router.project-osrm.org/route/v1/driving/${myPos.lng},${myPos.lat};${dest.lng},${dest.lat}?overview=full&geometries=geojson`
      const { data } = await axios.get(url)
      const coords: Array<[number, number]> = data?.routes?.[0]?.geometry?.coordinates?.map(
        (c: [number, number]) => [c[1], c[0]],
      )
      if (!coords || !coords.length) throw new Error('Route introuvable')
      setRouteCoords(coords)
    } catch (e) {
      setRouteCoords(null)
      setRouteError("Impossible de récupérer l'itinéraire.")
    } finally {
      setRouteLoading(false)
    }
  }

  if (!user) {
    return (
      <Alert severity="info">
        Connectez-vous via les boutons "Inscription" ou "Connexion" pour accéder au tableau livreur.
      </Alert>
    )
  }

  if (user.role !== 'COURIER') {
    return (
      <Alert severity="warning">
        Votre compte est de type client. Passez en mode livreur pour visualiser les commandes disponibles.
      </Alert>
    )
  }

  const preferredName = user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.email

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" fontWeight={600} gutterBottom>
          Tableau livreur
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.75 }}>
          Activez votre disponibilité et acceptez les courses prioritaires selon votre capacité.
        </Typography>
      </Box>

      {/* Carte des commandes */}
      <Card className="glass-panel">
        <CardHeader title="Carte des commandes" subheader="Visualisez les commandes en attente et vos courses en cours" />
        <CardContent>
          <Stack spacing={1} sx={{ mb: 1 }}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
              <Button variant="contained" size="small" onClick={handleUseMyLocation} disabled={geoLoading}>
                {geoLoading ? 'Localisation…' : 'Centrer sur ma position'}
              </Button>
              <Stack direction="row" spacing={1} alignItems="center">
                <TextField
                  label="Distance max (km)"
                  type="number"
                  size="small"
                  value={optCapacityKm}
                  onChange={(e) => setOptCapacityKm(Number(e.target.value) || 0)}
                />
                <Button
                  variant="contained"
                  size="small"
                  onClick={async () => {
                    console.log('Optimiser clicked')
                    if (!navigator.geolocation) {
                      alert("La géolocalisation n'est pas disponible")
                      return
                    }
                    navigator.geolocation.getCurrentPosition(async (pos) => {
                      const lat = pos.coords.latitude
                      const lng = pos.coords.longitude
                      console.log('Position:', lat, lng)
                      try {
                        console.log('Sending request to optimize...')
                        const res = await axios.post(
                          `${API_BASE}/orders/courier/optimize/`,
                          { courier: { lat, lng }, capacity_km: optCapacityKm },
                          token ? { headers: { Authorization: `Bearer ${token}` } } : undefined,
                        )
                        console.log('Optimize response:', res.data)
                        setOptSuggested(res.data?.selected_order_ids || [])
                        setOptimizationResult(res.data)
                        
                        // Set optimized route coordinates
                        if (res.data?.full_route_coordinates) {
                          setOptimizedRoute(res.data.full_route_coordinates)
                        }
                        
                        const details = [
                          `Algorithme: ${res.data?.algorithm || 'Realistic Delivery Optimizer'}`,
                          `Commandes sélectionnées: ${res.data?.count || 0}`,
                          `Profit total: ${res.data?.total_profit?.toFixed(2) || 0}€`,
                          `Distance totale: ${res.data?.total_distance_km?.toFixed(2) || 0}km`,
                          `Poids total: ${res.data?.total_weight_kg?.toFixed(2) || 0}kg`,
                          `Durée estimée: ${res.data?.estimated_duration_min || 0} min`
                        ].join('\n')
                        
                        if (res.data?.count > 0) {
                          alert(`Optimisation réussie!\n\n${details}`)
                        } else {
                          alert(`Aucune commande sélectionnée.\n\nVérifiez:\n- Qu'il y a des commandes en attente\n- Votre position GPS\n- Les contraintes de distance`)
                        }
                      } catch (err) {
                        console.error('Optimize error:', err)
                        const errorMsg = axios.isAxiosError(err) 
                          ? err.response?.data?.detail || err.message 
                          : 'Erreur inconnue'
                        alert(`Échec de l'optimisation: ${errorMsg}`)
                      }
                    }, (err) => {
                      console.error('Geolocation error:', err)
                      alert("Impossible d'obtenir votre position")
                    })
                  }}
                >Optimiser</Button>
              </Stack>
              {routeCoords && (
                <Button variant="outlined" size="small" color="info" onClick={() => setRouteCoords(null)} disabled={routeLoading}>
                  Effacer l'itinéraire
                </Button>
              )}
              <Button variant="outlined" size="small" onClick={() => setFitTrigger((n) => n + 1)}>
                Ajuster la carte aux commandes
              </Button>
              {geoError && <Alert severity="warning" sx={{ py: 0.5 }}>{geoError}</Alert>}
              {routeError && <Alert severity="error" sx={{ py: 0.5 }}>{routeError}</Alert>}
            </Stack>
          </Stack>
          <Box sx={{ height: 400, borderRadius: 2, overflow: 'hidden' }}>
            <OrdersMap
              pending={orders || []}
              active={activeOrders || []}
              myPos={myPos}
              route={routeCoords}
              optimizedRoute={optimizedRoute}
              onRequestRoute={requestRoute}
              fitTrigger={fitTrigger}
            />
          </Box>
          <RouteOptimizationDetails 
            result={optimizationResult} 
            onClose={() => setOptimizationResult(null)} 
          />
          {optimizationResult?.route_details && (
            <OptimizedRouteDisplay
              routeDetails={optimizationResult.route_details}
              totalDistance={optimizationResult.total_distance || 0}
              totalProfit={optimizationResult.total_profit || 0}
              onClose={() => {
                setOptimizationResult(null)
                setOptimizedRoute(null)
              }}
            />
          )}
          <Typography variant="caption" sx={{ opacity: 0.7 }}>
            • 🟠 Commandes en attente • 🟢 Commandes acceptées • 🔴 Itinéraire optimisé<br/>
            • 🚀 Départ • 🏪 Récupération • 🏠 Livraison • 🏁 Fin • ➡️ Direction
          </Typography>
        </CardContent>
      </Card>

      <Card className="glass-panel">
        <CardHeader
          avatar={<Avatar sx={{ bgcolor: 'primary.main' }}><DirectionsBikeRoundedIcon /></Avatar>}
          title={`Bonjour ${preferredName}`}
          subheader="Restez disponible pour recevoir les nouvelles commandes."
          action={
            <Tooltip title="Se déconnecter">
              <Button variant="outlined" color="inherit" onClick={onLogout} startIcon={<LoginRoundedIcon />}>
                Déconnexion
              </Button>
            </Tooltip>
          }
        />
        <CardContent>
          <Stack spacing={3}>
            <FormControlLabel
              control={<Switch checked={availability} onChange={(e) => setAvailability(e.target.checked)} />}
              label={availability ? 'Disponible pour les affectations' : 'En pause'}
            />
            <Divider light sx={{ borderColor: 'rgba(148, 163, 184, 0.35)' }}>
              <Chip
                icon={<PaidRoundedIcon />}
                label={`Gain potentiel : ${totalPotential.toFixed(2)} €`}
                color="secondary"
                variant="outlined"
              />
            </Divider>
            <Alert severity={remainingCapacity > 0 ? 'info' : 'warning'}>
              Charge actuelle : {activeWeight.toFixed(2)} kg / {capacity.toFixed(2)} kg —
              capacité restante {remainingCapacity.toFixed(2)} kg.
            </Alert>
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Commandes en attente
              </Typography>
              {acceptError && <Alert severity="error">{acceptError}</Alert>}
              {statusError && <Alert severity="error">{statusError}</Alert>}
              {!orders?.length && !isFetching && (
                <Alert severity="info" icon={<AccessTimeRoundedIcon fontSize="inherit" />}>
                  Aucune course pour le moment. Restez en ligne, nous vous avertissons dès qu'une commande arrive.
                </Alert>
              )}
              {isFetching && <Typography sx={{ opacity: 0.6 }}>Mise à jour en cours…</Typography>}
              {!!orders?.length && (
                <List>
                  {orders.map((order) => {
                    const wouldExceed = order.total_weight_kg + activeWeight > capacity
                    const tooltipLabel = wouldExceed
                      ? 'Capacité maximale atteinte (10 kg). Libérez de la place avant d’accepter.'
                      : 'Accepter la course'
                    return (
                      <ListItem
                        key={order.id}
                        sx={{
                          mb: 1,
                          borderRadius: 3,
                          bgcolor: 'background.paper',
                          boxShadow: '0 12px 32px rgba(15,23,42,0.25)',
                        }}
                        secondaryAction={
                          <Tooltip title={tooltipLabel}>
                            <span>
                              <Button
                                variant="contained"
                                size="small"
                                onClick={() => acceptMutation.mutate(order.id)}
                                disabled={acceptMutation.isPending || wouldExceed}
                              >
                                {acceptMutation.isPending ? '...' : 'Accepter'}
                              </Button>
                            </span>
                          </Tooltip>
                        }
                      >
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'secondary.main' }}>#{order.id}</Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Stack direction="row" alignItems="center" spacing={1}>
                              <Typography component="span">Client: {order.customer_phone}</Typography>
                              <IconButton
                                size="small"
                                onClick={() => {
                                  toggleExpanded(order.id)
                                  if (!details[order.id]) {
                                    loadDetails(order.id)
                                  }
                                }}
                                aria-label="Voir les détails de la commande"
                                sx={{
                                  transition: 'transform 0.2s',
                                  transform: expanded.has(order.id) ? 'rotate(90deg)' : 'rotate(0deg)',
                                }}
                              >
                                <ChevronRightRoundedIcon fontSize="small" />
                              </IconButton>
                              {optSuggested && optSuggested.includes(order.id) && (
                                <Chip label="Priorité" color="primary" size="small" />
                              )}
                            </Stack>
                          }
                          secondary={`Poids estimé ${order.total_weight_kg.toFixed(2)} kg · Offre ${order.delivery_price_offer} €`}
                        />
                        {expanded.has(order.id) && (
                          <Box sx={{ mt: 1, px: 1, py: 1, bgcolor: 'rgba(148,163,184,0.08)', borderRadius: 2 }}>
                            <Typography variant="body2">
                              • Statut: {order.status}
                            </Typography>
                            <Typography variant="body2">
                              • Position: lat {order.location_lat.toFixed(5)}, lng {order.location_lng.toFixed(5)}
                            </Typography>
                            <Typography variant="body2">
                              • Prix livraison proposé: {order.delivery_price_offer} €
                            </Typography>
                            <Divider sx={{ my: 1 }} />
                            <Typography variant="subtitle2" gutterBottom>
                              Produits demandés
                            </Typography>
                            {!details[order.id] && (
                              <Typography variant="body2" sx={{ opacity: 0.7 }}>Chargement des produits…</Typography>
                            )}
                            {details[order.id]?.items?.length ? (
                              <List dense>
                                {details[order.id]!.items.map((it) => (
                                  <ListItem key={`${order.id}-item-${it.item_id}`} sx={{ py: 0 }}>
                                    <ListItemText
                                      primary={`${it.quantity} × ${it.name}`}
                                      secondary={`Poids unitaire ${it.weight_per_unit_kg.toFixed(2)} kg`}
                                    />
                                  </ListItem>
                                ))}
                              </List>
                            ) : details[order.id] ? (
                              <Typography variant="body2" sx={{ opacity: 0.7 }}>Aucun produit listé.</Typography>
                            ) : null}
                            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                              <Button size="small" variant="text" onClick={() => requestRoute({ lat: order.location_lat, lng: order.location_lng })}>
                                Itinéraire
                              </Button>
                              <Button size="small" variant="text" color="inherit" onClick={() => toggleExpanded(order.id)}>
                                Fermer
                              </Button>
                            </Stack>
                          </Box>
                        )}
                      </ListItem>
                    )
                  })}
                </List>
              )}
            </Box>
            <Divider light sx={{ borderColor: 'rgba(148, 163, 184, 0.35)' }}>
              <Chip label="Commandes acceptées" color="primary" variant="outlined" />
            </Divider>
            <Box>
              {cancelError && <Alert severity="error">{cancelError}</Alert>}
              {isFetchingActive && <Typography sx={{ opacity: 0.6 }}>Actualisation des commandes…</Typography>}
              {!activeOrders?.length && !isFetchingActive && (
                <Alert severity="info">Vous n'avez aucune commande en cours.</Alert>
              )}
              {!!activeOrders?.length && (
                <List>
                  {activeOrders.map((order) => (
                    <ListItem
                      key={`active-${order.id}`}
                      sx={{
                        mb: 1,
                        borderRadius: 3,
                        bgcolor: 'rgba(30, 41, 59, 0.65)',
                        boxShadow: '0 12px 32px rgba(15,23,42,0.25)',
                      }}
                      secondaryAction={
                        <Stack direction="row" spacing={1}>
                          {order.status === 'ASSIGNED' && (
                            <Tooltip title="Marquer la commande comme récupérée">
                              <span>
                                <Button
                                  variant="outlined"
                                  size="small"
                                  color="info"
                                  onClick={() => statusMutation.mutate({ id: order.id, status: 'PICKED_UP' })}
                                  disabled={statusMutation.isPending}
                                >
                                  {statusMutation.isPending ? '...' : 'Ramassée'}
                                </Button>
                              </span>
                            </Tooltip>
                          )}
                          <Tooltip title="Marquer la commande comme livrée">
                            <span>
                              <Button
                                variant="outlined"
                                size="small"
                                color="success"
                                onClick={() => statusMutation.mutate({ id: order.id, status: 'DELIVERED' })}
                                disabled={statusMutation.isPending}
                              >
                                {statusMutation.isPending ? '...' : 'Livrée'}
                              </Button>
                            </span>
                          </Tooltip>
                          <Tooltip title="Annuler cette commande">
                            <span>
                              <Button
                                variant="outlined"
                                size="small"
                                color="warning"
                                onClick={() => cancelMutation.mutate(order.id)}
                                disabled={cancelMutation.isPending}
                              >
                                {cancelMutation.isPending ? '...' : 'Annuler'}
                              </Button>
                            </span>
                          </Tooltip>
                        </Stack>
                      }
                    >
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>#{order.id}</Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={`Client: ${order.customer_phone}`}
                        secondary={`Poids ${order.total_weight_kg.toFixed(2)} kg · Statut ${order.status}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
            <Divider light sx={{ borderColor: 'rgba(148, 163, 184, 0.35)' }}>
              <Chip label="Commandes livrées" color="success" variant="outlined" />
            </Divider>
            <Box>
              <Alert severity="success" sx={{ bgcolor: 'rgba(34, 197, 94, 0.12)' }}>
                Gain cumulé (livraisons complétées) : {completedTotal.toFixed(2)} €
              </Alert>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Button variant="outlined" size="small" onClick={() => setShowHistory((s) => !s)}>
                  {showHistory ? 'Masquer historique' : 'Historique'}
                </Button>
                {showHistory && (
                  <>
                    <Button variant="outlined" size="small" color="error" onClick={deleteAllHistory}>
                      Supprimer tout
                    </Button>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <input type="date" value={historyDate} onChange={(e) => setHistoryDate(e.target.value)} />
                      <Button variant="outlined" size="small" color="warning" onClick={deleteByDateHistory}>
                        Supprimer par jour
                      </Button>
                    </Stack>
                  </>
                )}
              </Stack>
              {isFetchingCompleted && <Typography sx={{ opacity: 0.6, mt: 1 }}>Récupération des livraisons terminées…</Typography>}
              {(!showHistory && !todaysCompleted.length) && !isFetchingCompleted && (
                <Alert severity="info" sx={{ mt: 1 }}>
                  Vous n'avez pas encore marqué de commande comme livrée aujourd'hui.
                </Alert>
              )}
              {showHistory ? (
                <List>
                  {(completedOrders || []).map((order) => (
                    <ListItem
                      key={`completed-${order.id}`}
                      sx={{
                        mb: 1,
                        borderRadius: 3,
                        bgcolor: 'rgba(21, 94, 49, 0.45)',
                        boxShadow: '0 12px 32px rgba(21,94,49,0.25)',
                      }}
                      secondaryAction={
                        <Button size="small" color="error" variant="outlined" onClick={() => deleteOneHistory(order.id)}>
                          Supprimer
                        </Button>
                      }
                    >
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'success.main' }}>#{order.id}</Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={`Gain : ${parseFloat(order.delivery_price_offer || '0').toFixed(2)} €`}
                        secondary={`Livrée le ${order.delivered_at ? new Date(order.delivered_at).toLocaleString() : 'Date inconnue'}`}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                !!todaysCompleted.length && (
                  <List>
                    {todaysCompleted.map((order) => (
                      <ListItem
                        key={`completed-today-${order.id}`}
                        sx={{
                          mb: 1,
                          borderRadius: 3,
                          bgcolor: 'rgba(21, 94, 49, 0.45)',
                          boxShadow: '0 12px 32px rgba(21,94,49,0.25)',
                        }}
                      >
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'success.main' }}>#{order.id}</Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={`Gain : ${parseFloat(order.delivery_price_offer || '0').toFixed(2)} €`}
                          secondary={`Livrée le ${order.delivered_at ? new Date(order.delivered_at).toLocaleTimeString() : 'Date inconnue'}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )
              )}
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}

type OrdersMapProps = {
  pending: Order[]
  active: Order[]
  myPos: { lat: number; lng: number } | null
  route: Array<[number, number]> | null
  optimizedRoute: Array<[number, number]> | null
  onRequestRoute: (dest: { lat: number; lng: number }) => void
  fitTrigger: number
}

function OrdersMap({ pending, active, myPos, route, optimizedRoute, onRequestRoute, fitTrigger }: OrdersMapProps) {
  // Center: average of all points, fallback to a default city center
  const all = [...pending, ...active]
  const avgLat = all.length ? all.reduce((a, o) => a + (o.location_lat || 0), 0) / all.length : 33.5731
  const avgLng = all.length ? all.reduce((a, o) => a + (o.location_lng || 0), 0) / all.length : -7.5898
  const center: LatLngExpression = [avgLat, avgLng]
  return (
    <MapContainer center={center} zoom={12} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <PanTo position={myPos} />
      <FitToMarkers points={all.map(o => [o.location_lat, o.location_lng] as [number, number])} trigger={fitTrigger} extra={myPos ? [[myPos.lat, myPos.lng] as [number, number]] : []} />
      
      {/* Commandes en attente - Orange */}
      {pending.map((o) => (
        <CircleMarker key={`p-${o.id}`} center={[o.location_lat, o.location_lng]} radius={8} pathOptions={{ color: '#f59e0b', fillColor: '#fef3c7', fillOpacity: 0.8 }}>
          <Popup>
            <strong>📦 Commande #{o.id}</strong><br />
            Poids: {o.total_weight_kg.toFixed(2)} kg<br />
            Offre: {o.delivery_price_offer} €<br />
            Statut: {o.status}
            <Button size="small" variant="text" onClick={() => onRequestRoute({ lat: o.location_lat, lng: o.location_lng })}>
              Itinéraire vers ce client
            </Button>
          </Popup>
        </CircleMarker>
      ))}
      
      {/* Commandes actives - Vert */}
      {active.map((o) => (
        <CircleMarker key={`a-${o.id}`} center={[o.location_lat, o.location_lng]} radius={8} pathOptions={{ color: '#22c55e', fillColor: '#dcfce7', fillOpacity: 0.8 }}>
          <Popup>
            <strong>🚚 En cours #{o.id}</strong><br />
            Poids: {o.total_weight_kg.toFixed(2)} kg<br />
            Offre: {o.delivery_price_offer} €<br />
            Statut: {o.status}
            <Button size="small" variant="text" onClick={() => onRequestRoute({ lat: o.location_lat, lng: o.location_lng })}>
              Itinéraire vers ce client
            </Button>
          </Popup>
        </CircleMarker>
      ))}
      
      {/* Position du livreur - Bleu */}
      {myPos && (
        <CircleMarker center={[myPos.lat, myPos.lng]} radius={10} pathOptions={{ color: '#3b82f6', fillColor: '#dbeafe', fillOpacity: 0.9 }}>
          <Popup><strong>📍 Ma position actuelle</strong></Popup>
        </CircleMarker>
      )}
      
      {/* Itinéraire simple - Bleu */}
      {route && route.length > 1 && (
        <Polyline positions={route} pathOptions={{ color: '#3b82f6', weight: 4, opacity: 0.7 }} />
      )}
      
      {/* Itinéraire optimisé avec étapes numérotées */}
      {optimizedRoute && optimizedRoute.length > 1 && (
        <>
          {/* Ligne principale rouge */}
          <Polyline positions={optimizedRoute} pathOptions={{ color: '#ef4444', weight: 5, opacity: 0.8 }} />
          
          {/* Points numérotés pour chaque étape */}
          {optimizedRoute.map((coord, index) => {
            const isStart = index === 0
            const isEnd = index === optimizedRoute.length - 1
            const isPickup = index % 2 === 1 && !isEnd // Impair = pickup
            const isDelivery = index % 2 === 0 && !isStart && !isEnd // Pair = delivery
            
            let icon = '📍'
            let color = '#ef4444'
            let fillColor = '#fef2f2'
            let description = `Étape ${index + 1}`
            
            if (isStart) {
              icon = '🚀'
              color = '#3b82f6'
              fillColor = '#dbeafe'
              description = 'Départ livreur'
            } else if (isPickup) {
              icon = '🏪'
              color = '#f59e0b'
              fillColor = '#fef3c7'
              description = `Récupération ${Math.ceil(index / 2)}`
            } else if (isDelivery) {
              icon = '🏠'
              color = '#22c55e'
              fillColor = '#dcfce7'
              description = `Livraison ${index / 2}`
            } else if (isEnd) {
              icon = '🏁'
              color = '#8b5cf6'
              fillColor = '#f3e8ff'
              description = 'Fin de tournée'
            }
            
            return (
              <CircleMarker 
                key={`route-${index}`} 
                center={[coord[0], coord[1]]} 
                radius={12} 
                pathOptions={{ color, fillColor, fillOpacity: 0.9, weight: 3 }}
              >
                <Popup>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', marginBottom: '5px' }}>{icon}</div>
                    <strong>{description}</strong><br />
                    <small>Étape {index + 1}/{optimizedRoute.length}</small>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
          
          {/* Flèches directionnelles sur la ligne */}
          {optimizedRoute.slice(0, -1).map((coord, index) => {
            const nextCoord = optimizedRoute[index + 1]
            const midLat = (coord[0] + nextCoord[0]) / 2
            const midLng = (coord[1] + nextCoord[1]) / 2
            
            return (
              <CircleMarker 
                key={`arrow-${index}`}
                center={[midLat, midLng]}
                radius={4}
                pathOptions={{ color: '#ef4444', fillColor: '#ffffff', fillOpacity: 1, weight: 2 }}
              >
                <Popup>
                  <small>➡️ Direction étape {index + 2}</small>
                </Popup>
              </CircleMarker>
            )
          })}
        </>
      )}
    </MapContainer>
  )
}

function FitToMarkers({ points, trigger, extra = [] as [number, number][] }: { points: [number, number][]; trigger: number; extra?: [number, number][] }) {
  const map = useMap()
  useEffect(() => {
    const pts = [...points, ...extra]
    if (pts.length === 0) return
    const valid = pts.filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng))
    if (valid.length === 0) return
    const bounds = L.latLngBounds(valid as [number, number][])
    try {
      map.fitBounds(bounds, { padding: [30, 30] })
    } catch {}
  }, [trigger])
  return null
}

function PanTo({ position }: { position: { lat: number; lng: number } | null }) {
  const map = useMap()
  useEffect(() => {
    if (!position) return
    try {
      map.flyTo([position.lat, position.lng], Math.max(map.getZoom(), 14))
    } catch {}
  }, [position])
  return null
}
