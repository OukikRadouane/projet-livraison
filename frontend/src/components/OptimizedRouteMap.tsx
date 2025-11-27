import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'
import { Box, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Typography, Stack } from '@mui/material'
import StorefrontIcon from '@mui/icons-material/Storefront'
import LocationOnIcon from '@mui/icons-material/LocationOn'
import LocalShippingIcon from '@mui/icons-material/LocalShipping'

interface RouteStop {
  id: number
  sequence: number
  stop_type: 'store' | 'client' | 'depot'
  store_details?: { name: string; latitude: number; longitude: number; address: string; phone?: string }
  order_details?: { id: number; customer_phone: string; delivery_price_offer: string; items: any[] }
  latitude: number
  longitude: number
  estimated_arrival_time?: string
  distance_from_previous: number
}

interface OptimizedRouteMapProps {
  route: {
    id: number
    total_distance: number
    total_time: number
    total_profit: number
    is_active: boolean
    stops: RouteStop[]
  }
}

// Créer des icônes personnalisées
const storeIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23FF6B6B" width="32" height="32"><path d="M18 18.5a1.5 1.5 0 01-1.5-1.5V9.5a1.5 1.5 0 013 0V17a1.5 1.5 0 01-1.5 1.5zm-12 0a1.5 1.5 0 01-1.5-1.5V9.5a1.5 1.5 0 013 0V17a1.5 1.5 0 01-1.5 1.5zM12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/></svg>',
  iconSize: [32, 32],
  popupAnchor: [0, -10],
})

const clientIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234ECDC4" width="32" height="32"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>',
  iconSize: [32, 32],
  popupAnchor: [0, -10],
})

const depotIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2345B7D1" width="32" height="32"><path d="M18 8h-1V6c0-.55-.45-1-1-1H8c-.55 0-1 .45-1 1v2H6c-1.1 0-2 .9-2 2v10h16V10c0-1.1-.9-2-2-2zm-3-2v2H9V6h6zM4 20h16v-8H4v8z"/></svg>',
  iconSize: [32, 32],
  popupAnchor: [0, -10],
})

const createIcon = (type: 'store' | 'client' | 'depot') => {
  if (type === 'store') return storeIcon
  if (type === 'client') return clientIcon
  return depotIcon
}

export default function OptimizedRouteMap({ route }: OptimizedRouteMapProps) {
  if (!route.stops || route.stops.length === 0) {
    return (
      <Paper sx={{ p: 3, bgcolor: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(8px)' }}>
        <Typography color="error">Aucun arrêt dans cette route</Typography>
      </Paper>
    )
  }

  // Filtrer les arrêts valides
  const validStops = route.stops.filter(stop => 
    typeof stop.latitude === 'number' && 
    typeof stop.longitude === 'number' &&
    !isNaN(stop.latitude) &&
    !isNaN(stop.longitude)
  )

  if (validStops.length === 0) {
    return (
      <Paper sx={{ p: 3, bgcolor: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(8px)' }}>
        <Typography color="error">Aucun arrêt valide avec coordonnées GPS</Typography>
      </Paper>
    )
  }

  // Créer les coordonnées pour la polyline
  const coordinates = validStops.map((stop) => [stop.latitude, stop.longitude] as [number, number])

  // Calculer le centre de la map
  const centerLat = coordinates.reduce((sum, coord) => sum + coord[0], 0) / coordinates.length
  const centerLng = coordinates.reduce((sum, coord) => sum + coord[1], 0) / coordinates.length

  return (
    <Stack spacing={3}>
      {/* Statistiques résumées */}
      <Paper sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(8px)' }}>
        <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap' }}>
          <Chip
            label={`Distance totale: ${route.total_distance.toFixed(2)} km`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`Temps: ${Math.round(route.total_time)} min`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`Bénéfice: ${route.total_profit.toFixed(2)} DH`}
            color="success"
            variant="outlined"
          />
          <Chip
            label={route.is_active ? '🟢 Actif' : '🔴 Inactif'}
            color={route.is_active ? 'success' : 'default'}
          />
        </Stack>
      </Paper>

      {/* Carte interactive */}
      <Paper sx={{ height: '400px', borderRadius: 2, overflow: 'hidden', position: 'relative' }}>
        <MapContainer center={[centerLat, centerLng]} zoom={13} style={{ width: '100%', height: '100%' }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />

          {/* Tracer la polyline (itinéraire) */}
          {coordinates.length > 1 && (
            <Polyline positions={coordinates} color="#4ECDC4" weight={3} opacity={0.7} dashArray="5, 5" />
          )}

          {/* Ajouter les marqueurs pour chaque arrêt */}
          {validStops.map((stop) => (
            <Marker
              key={`marker-${stop.id}`}
              position={[stop.latitude, stop.longitude]}
              icon={createIcon(stop.stop_type)}
            >
              <Popup>
                <Box sx={{ minWidth: '250px', p: 1 }}>
                  <Typography variant="h6" sx={{ mb: 1, fontWeight: 600, fontSize: '0.9rem' }}>
                    {stop.stop_type === 'store' ? '🏪 Magasin' : stop.stop_type === 'client' ? '📦 Client' : '🏢 Dépôt'}{' '}
                    #{stop.sequence}
                  </Typography>
                  
                  {stop.store_details && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        <strong>Nom:</strong> {stop.store_details.name}
                      </Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        <strong>Adresse:</strong> {stop.store_details.address}
                      </Typography>
                      {stop.store_details.phone && (
                        <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                          <strong>Téléphone:</strong> {stop.store_details.phone}
                        </Typography>
                      )}
                    </Box>
                  )}
                  
                  {stop.order_details && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        <strong>Téléphone:</strong> {stop.order_details.customer_phone}
                      </Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        <strong>Prix:</strong> {stop.order_details.delivery_price_offer} DH
                      </Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        <strong>Items:</strong> {Array.isArray(stop.order_details.items) ? stop.order_details.items.length : 0}
                      </Typography>
                    </Box>
                  )}
                  
                  <Box sx={{ pt: 1, borderTop: '1px solid #ddd' }}>
                    <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                      <strong>Distance:</strong> {stop.distance_from_previous.toFixed(2)} km
                    </Typography>
                    {stop.estimated_arrival_time && (
                      <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                        <strong>Arrivée:</strong> {new Date(stop.estimated_arrival_time).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </Paper>

      {/* Tableau des arrêts */}
      <Box>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
          Détail de la tournée ({validStops.length} arrêts)
        </Typography>
        <TableContainer component={Paper} sx={{ bgcolor: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(8px)' }}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: 'rgba(255,255,255,0.1)' }}>
                <TableCell align="center" sx={{ fontWeight: 600, fontSize: '0.9rem' }}>
                  #
                </TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.9rem' }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.9rem' }}>Détail</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600, fontSize: '0.9rem' }}>
                  Distance (km)
                </TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.9rem' }}>Arrivée</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {validStops.map((stop) => (
                <TableRow key={`row-${stop.id}`} hover>
                  <TableCell align="center" sx={{ fontWeight: 600, fontSize: '0.9rem' }}>
                    {stop.sequence}
                  </TableCell>
                  <TableCell sx={{ fontSize: '0.9rem' }}>
                    <Chip
                      icon={
                        stop.stop_type === 'store' ? (
                          <StorefrontIcon sx={{ fontSize: '1rem' }} />
                        ) : stop.stop_type === 'client' ? (
                          <LocationOnIcon sx={{ fontSize: '1rem' }} />
                        ) : (
                          <LocalShippingIcon sx={{ fontSize: '1rem' }} />
                        )
                      }
                      label={stop.stop_type === 'store' ? 'Magasin' : stop.stop_type === 'client' ? 'Client' : 'Dépôt'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell sx={{ fontSize: '0.9rem' }}>
                    {stop.store_details ? `${stop.store_details.name}` : ''}
                    {stop.order_details ? `Client: ${stop.order_details.customer_phone}` : ''}
                    {stop.stop_type === 'depot' && 'Dépôt de départ'}
                  </TableCell>
                  <TableCell align="right" sx={{ fontSize: '0.9rem' }}>
                    {stop.distance_from_previous.toFixed(2)}
                  </TableCell>
                  <TableCell sx={{ fontSize: '0.9rem' }}>
                    {stop.estimated_arrival_time 
                      ? new Date(stop.estimated_arrival_time).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
                      : '-'
                    }
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Stack>
  )
}
