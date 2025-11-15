import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Stack,
  TextField,
  Typography,
  MenuItem,
  InputAdornment,
} from '@mui/material'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import LocalPhoneRoundedIcon from '@mui/icons-material/LocalPhoneRounded'
import FmdGoodRoundedIcon from '@mui/icons-material/FmdGoodRounded'
import MyLocationRoundedIcon from '@mui/icons-material/MyLocationRounded'
import axios from 'axios'

interface Item {
  id: number
  name: string
  category: string
  unit: string
  weight_per_unit_kg: number
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

export default function CustomerOrderPage() {
  const qc = useQueryClient()
  const { data: items, isLoading } = useQuery<Item[]>({
    queryKey: ['items'],
    queryFn: async () => (await axios.get(`${API_BASE}/catalog/items/`)).data,
  })

  const [phone, setPhone] = useState('')
  const [lat, setLat] = useState('')
  const [lng, setLng] = useState('')
  const [offer, setOffer] = useState('')
  const [selectedItems, setSelectedItems] = useState<{ item_id: number; quantity: number }[]>([])
  const [geoLoading, setGeoLoading] = useState(false)
  const [geoError, setGeoError] = useState<string | null>(null)

  const orderMutation = useMutation({
    mutationFn: async () =>
      axios.post(`${API_BASE}/orders/`, {
        customer_phone: phone,
        location_lat: parseFloat(lat),
        location_lng: parseFloat(lng),
        delivery_price_offer: offer,
        items: selectedItems,
      }),
    onSuccess: () => {
      setPhone('')
      setLat('')
      setLng('')
      setOffer('')
      setSelectedItems([])
      setGeoError(null)
      qc.invalidateQueries({ queryKey: ['items'] })
    },
  })

  const totalWeight = useMemo(() => {
    if (!items) return 0
    return selectedItems.reduce((acc, current) => {
      const item = items.find((i) => i.id === current.item_id)
      if (!item) return acc
      return acc + item.weight_per_unit_kg * current.quantity
    }, 0)
  }, [items, selectedItems])

  const addItem = (id: number) => {
    setSelectedItems((prev) =>
      prev.find((p) => p.item_id === id) ? prev : [...prev, { item_id: id, quantity: 1 }],
    )
  }

  const updateQty = (id: number, qty: number) => {
    setSelectedItems((prev) => prev.map((p) => (p.item_id === id ? { ...p, quantity: Math.max(1, qty) } : p)))
  }

  const removeItem = (id: number) => {
    setSelectedItems((prev) => prev.filter((p) => p.item_id !== id))
  }

  const handleUseLocation = () => {
    if (!navigator?.geolocation) {
      setGeoError("La géolocalisation n'est pas disponible sur ce navigateur.")
      return
    }
    setGeoLoading(true)
    setGeoError(null)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords
        setLat(latitude.toFixed(6))
        setLng(longitude.toFixed(6))
        setGeoLoading(false)
      },
      (error) => {
        const messages: Record<number, string> = {
          1: "Permission refusée. Autorisez l'accès à votre position pour remplir automatiquement les champs.",
          2: 'La position est indisponible. Réessayez dans un instant.',
          3: 'La demande de position a expiré. Réessayez.',
        }
        setGeoError(messages[error.code] || 'Impossible de récupérer votre position.')
        setGeoLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" fontWeight={600} gutterBottom>
          Commande express
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.75 }}>
          Choisissez vos produits frais, indiquez votre localisation et proposez un prix pour la livraison.
        </Typography>
      </Box>

      {orderMutation.isSuccess && <Alert severity="success">Votre commande a été transmise, un livreur va l'accepter rapidement.</Alert>}
      {orderMutation.isError && <Alert severity="error">Impossible d'envoyer la commande. Vérifiez votre connexion.</Alert>}

      <Card className="glass-panel">
        <CardHeader
          title={<Typography variant="h6">Coordonnées</Typography>}
          subheader="Comment vous joindre et où livrer la commande"
        />
        <CardContent>
          <Stack spacing={2}>
            <TextField
              fullWidth
              label="Téléphone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LocalPhoneRoundedIcon sx={{ color: 'secondary.light' }} />
                  </InputAdornment>
                ),
              }}
            />
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ md: 'center' }}>
              <Button
                variant="contained"
                color="secondary"
                startIcon={<MyLocationRoundedIcon />}
                onClick={handleUseLocation}
                disabled={geoLoading}
              >
                {geoLoading ? 'Localisation…' : 'Utiliser ma position'}
              </Button>
              <Typography variant="body2" sx={{ opacity: 0.7 }}>
                Autorisez l'accès à votre position pour remplir automatiquement la latitude et la longitude.
              </Typography>
            </Stack>
            {geoError && <Alert severity="warning">{geoError}</Alert>}
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                fullWidth
                label="Latitude"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <FmdGoodRoundedIcon sx={{ color: 'secondary.light' }} />
                    </InputAdornment>
                  ),
                }}
              />
              <TextField
                fullWidth
                label="Longitude"
                value={lng}
                onChange={(e) => setLng(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <FmdGoodRoundedIcon sx={{ color: 'secondary.light' }} />
                    </InputAdornment>
                  ),
                }}
              />
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card className="glass-panel">
        <CardHeader title={<Typography variant="h6">Articles</Typography>} subheader="Sélectionnez les produits souhaités" />
        <CardContent>
          {isLoading ? (
            <Typography>Chargement du catalogue...</Typography>
          ) : (
            <Stack spacing={3}>
              <TextField
                select
                label="Ajouter un article"
                value=""
                onChange={(event) => addItem(parseInt(event.target.value, 10))}
                fullWidth
              >
                <MenuItem value="" disabled>
                  Choisir un article
                </MenuItem>
                {items?.map((item) => (
                  <MenuItem key={item.id} value={item.id}>
                    {item.name} · {item.category}
                  </MenuItem>
                ))}
              </TextField>

              <Stack spacing={2}>
                {selectedItems.length === 0 && (
                  <Typography sx={{ opacity: 0.6 }}>Aucun article sélectionné pour le moment.</Typography>
                )}
                {selectedItems.map((sel) => {
                  const item = items?.find((i) => i.id === sel.item_id)
                  if (!item) return null
                  return (
                    <Card key={sel.item_id} sx={{ bgcolor: 'background.paper', borderRadius: 3 }}>
                      <CardContent>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ sm: 'center' }} justifyContent="space-between">
                          <Box>
                            <Typography variant="subtitle1" fontWeight={600}>
                              {item.name}
                            </Typography>
                            <Chip size="small" label={item.category.toLowerCase()} sx={{ textTransform: 'capitalize', mt: 1 }} />
                          </Box>
                          <TextField
                            type="number"
                            label="Quantité"
                            inputProps={{ min: 1 }}
                            value={sel.quantity}
                            onChange={(e) => updateQty(sel.item_id, parseInt(e.target.value, 10) || 1)}
                            sx={{ maxWidth: 150 }}
                          />
                          <Button
                            color="error"
                            startIcon={<DeleteOutlineRoundedIcon />}
                            onClick={() => removeItem(sel.item_id)}
                          >
                            Retirer
                          </Button>
                        </Stack>
                      </CardContent>
                    </Card>
                  )
                })}
              </Stack>
            </Stack>
          )}
        </CardContent>
      </Card>

      <Card className="glass-panel">
        <CardHeader title={<Typography variant="h6">Résumé</Typography>} subheader="Proposez un prix et validez la demande" />
        <CardContent>
          <Stack spacing={3}>
            <TextField
              fullWidth
              label="Offre pour la livraison (€)"
              value={offer}
              onChange={(e) => setOffer(e.target.value)}
            />

            <Divider light>
              <Chip label={`Poids estimé: ${totalWeight.toFixed(2)} kg`} color="secondary" variant="outlined" />
            </Divider>

            <Button
              variant="contained"
              size="large"
              onClick={() => orderMutation.mutate()}
              disabled={!phone || !lat || !lng || !offer || selectedItems.length === 0 || orderMutation.isPending}
            >
              {orderMutation.isPending ? 'Envoi en cours…' : 'Envoyer la commande'}
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}
