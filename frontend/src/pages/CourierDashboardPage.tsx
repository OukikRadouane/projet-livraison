import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
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
import DirectionsBikeRoundedIcon from '@mui/icons-material/DirectionsBikeRounded'
import LoginRoundedIcon from '@mui/icons-material/LoginRounded'
import AccessTimeRoundedIcon from '@mui/icons-material/AccessTimeRounded'
import PaidRoundedIcon from '@mui/icons-material/PaidRounded'
import axios from 'axios'
import type { UserProfile } from '../components/AuthDialogs'

interface Order {
  id: number
  status: string
  customer_phone: string
  delivery_price_offer: string
  courier: number | null
  total_weight_kg: number
  delivered_at: string | null
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
                          primary={`Client: ${order.customer_phone}`}
                          secondary={`Poids estimé ${order.total_weight_kg.toFixed(2)} kg · Offre ${order.delivery_price_offer} €`}
                        />
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
              {isFetchingCompleted && <Typography sx={{ opacity: 0.6, mt: 1 }}>Récupération des livraisons terminées…</Typography>}
              {!completedOrders?.length && !isFetchingCompleted && (
                <Alert severity="info" sx={{ mt: 1 }}>
                  Vous n'avez pas encore marqué de commande comme livrée aujourd'hui.
                </Alert>
              )}
              {!!completedOrders?.length && (
                <List>
                  {completedOrders.map((order) => (
                    <ListItem
                      key={`completed-${order.id}`}
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
                        secondary={`Livrée le ${order.delivered_at ? new Date(order.delivered_at).toLocaleString() : 'Date inconnue'}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}
