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
  Divider,
  Avatar
} from '@mui/material'
import StoreIcon from '@mui/icons-material/Store'
import HomeIcon from '@mui/icons-material/Home'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import RouteIcon from '@mui/icons-material/Route'

interface RouteStep {
  step: number
  type: 'start' | 'pickup' | 'delivery'
  lat: number
  lng: number
  store_name?: string
  order_id?: number
  customer_phone?: string
  profit?: number
  description: string
  estimated_time: string
}

interface Props {
  routeDetails: RouteStep[]
  totalDistance: number
  totalProfit: number
  onClose: () => void
}

export default function OptimizedRouteDisplay({ routeDetails, totalDistance, totalProfit, onClose }: Props) {
  if (!routeDetails || routeDetails.length === 0) return null

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'start':
        return <PlayArrowIcon color="primary" />
      case 'pickup':
        return <StoreIcon color="secondary" />
      case 'delivery':
        return <HomeIcon color="success" />
      default:
        return <RouteIcon />
    }
  }

  const getStepColor = (type: string) => {
    switch (type) {
      case 'start':
        return 'primary'
      case 'pickup':
        return 'secondary'
      case 'delivery':
        return 'success'
      default:
        return 'default'
    }
  }

  return (
    <Card sx={{ mt: 2, bgcolor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <RouteIcon color="error" />
            <Typography variant="h6">Itinéraire Optimisé</Typography>
            <Chip label="Tabu Search + Branch & Bound" color="error" size="small" />
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
            label={`${routeDetails.length} étapes`} 
            color="error" 
            variant="outlined" 
          />
          <Chip 
            label={`${totalDistance.toFixed(2)}km total`} 
            color="info" 
            variant="outlined" 
          />
          <Chip 
            label={`${totalProfit.toFixed(2)}€ profit`} 
            color="success" 
            variant="outlined" 
          />
        </Box>

        <Typography variant="subtitle2" gutterBottom>
          Séquence d'Exécution Optimisée:
        </Typography>
        
        <List dense>
          {routeDetails.map((step, index) => (
            <ListItem key={index} sx={{ 
              mb: 1, 
              bgcolor: 'rgba(255,255,255,0.05)', 
              borderRadius: 2,
              border: '1px solid rgba(255,255,255,0.1)'
            }}>
              <ListItemIcon>
                <Avatar 
                  sx={{ 
                    width: 32, 
                    height: 32, 
                    bgcolor: `${getStepColor(step.type)}.main`,
                    fontSize: '0.875rem'
                  }}
                >
                  {step.step}
                </Avatar>
              </ListItemIcon>
              <Box sx={{ mr: 2 }}>
                {getStepIcon(step.type)}
              </Box>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="subtitle2">
                      {step.description}
                    </Typography>
                    {step.type === 'pickup' && (
                      <Chip label={step.store_name} size="small" color="secondary" />
                    )}
                    {step.type === 'delivery' && step.profit && (
                      <Chip label={`${step.profit.toFixed(2)}€`} size="small" color="success" />
                    )}
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="caption" display="block">
                      📍 {step.lat.toFixed(5)}, {step.lng.toFixed(5)}
                    </Typography>
                    <Typography variant="caption" color="primary.main">
                      ⏱️ {step.estimated_time}
                    </Typography>
                    {step.customer_phone && (
                      <Typography variant="caption" display="block" color="text.secondary">
                        📞 {step.customer_phone}
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
          🔴 Itinéraire rouge sur la carte • Numérotation des étapes • Respect des contraintes de capacité
        </Typography>
      </CardContent>
    </Card>
  )
}