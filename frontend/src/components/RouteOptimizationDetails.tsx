import React from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Box,
  Divider
} from '@mui/material'
import StoreIcon from '@mui/icons-material/Store'
import HomeIcon from '@mui/icons-material/Home'
import RouteIcon from '@mui/icons-material/Route'

interface RouteDetail {
  type: 'pickup' | 'delivery' | 'start'
  lat: number
  lng: number
  store_name?: string
  order_id?: number
  profit?: number
  description?: string
}

interface OptimizationResult {
  selected_order_ids: number[]
  total_profit: number
  total_distance_km: number
  total_weight_kg: number
  delivery_sequence: number[]
  pickup_sequence: [number, number][]
  route_details: RouteDetail[]
  algorithm: string
}

interface Props {
  result: OptimizationResult | null
  onClose: () => void
}

export default function RouteOptimizationDetails({ result, onClose }: Props) {
  if (!result) return null

  return (
    <Card sx={{ mt: 2, bgcolor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <RouteIcon color="primary" />
            <Typography variant="h6">Route Optimisée</Typography>
            <Chip label={result.algorithm} color="primary" size="small" />
          </Box>
        }
        action={
          <Typography variant="button" onClick={onClose} sx={{ cursor: 'pointer', opacity: 0.7 }}>
            ✕
          </Typography>
        }
      />
      <CardContent>
        <Box display="flex" gap={2} mb={2} flexWrap="wrap">
          <Chip 
            label={`${result.selected_order_ids?.length || 0} commandes`} 
            color="secondary" 
            variant="outlined" 
          />
          <Chip 
            label={`${(result.total_profit || 0).toFixed(2)}€ profit`} 
            color="success" 
            variant="outlined" 
          />
          <Chip 
            label={`${(result.total_distance_km || 0).toFixed(2)}km distance`} 
            color="info" 
            variant="outlined" 
          />
          <Chip 
            label={`${(result.total_weight_kg || 0).toFixed(2)}kg poids`} 
            color="warning" 
            variant="outlined" 
          />
        </Box>

        <Typography variant="subtitle2" gutterBottom>
          Séquence de Route Optimisée:
        </Typography>
        
        <List dense>
          {result.route_details.map((detail, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                {detail.type === 'pickup' ? (
                  <StoreIcon color="secondary" />
                ) : (
                  <HomeIcon color="primary" />
                )}
              </ListItemIcon>
              <ListItemText
                primary={
                  detail.type === 'pickup' 
                    ? `Récupération - ${detail.store_name || 'Magasin'}`
                    : detail.type === 'start'
                    ? 'Départ livreur'
                    : `Livraison - Commande #${detail.order_id || 'N/A'}`
                }
                secondary={
                  <Box>
                    <Typography variant="caption" display="block">
                      {detail.lat.toFixed(5)}, {detail.lng.toFixed(5)}
                    </Typography>
                    {detail.profit && (
                      <Typography variant="caption" color="success.main">
                        Profit: {detail.profit.toFixed(2)}€
                      </Typography>
                    )}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>

        <Divider sx={{ my: 2 }} />
        
        <Typography variant="caption" color="text.secondary">
          Algorithmes utilisés: Branch & Bound (sélection des commandes) + Tabu Search (optimisation de route)
        </Typography>
      </CardContent>
    </Card>
  )
}