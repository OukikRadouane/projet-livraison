import { useState } from 'react'
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import axios from 'axios'

type Role = 'COURIER' | 'CUSTOMER'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

export type UserProfile = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string
  cne: string
  role: Role
  capacity_kg: number
}

interface SignupDialogProps {
  open: boolean
  onClose: () => void
}

export function SignupDialog({ open, onClose }: SignupDialogProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [phone, setPhone] = useState('')
  const [cne, setCne] = useState('')
  const [role, setRole] = useState<Role>('COURIER')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const reset = () => {
    setEmail('')
    setPassword('')
    setFirstName('')
    setLastName('')
    setPhone('')
    setCne('')
    setRole('COURIER')
    setSubmitting(false)
    setError(null)
    setSuccess(false)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await axios.post(`${API_BASE}/accounts/signup/`, {
        email,
        password,
        role,
        first_name: firstName,
        last_name: lastName,
        phone,
        cne,
      })
      setSuccess(true)
    } catch (err) {
      setError("Impossible de créer le compte. Vérifiez les informations fournies.")
    } finally {
      setSubmitting(false)
    }
  }

  const isCourier = role === 'COURIER'
  const canSubmit =
    !!email &&
    !!password &&
    (!isCourier || (firstName.trim() && lastName.trim() && phone.trim() && cne.trim())) &&
    !submitting

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>Créer un compte</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" sx={{ opacity: 0.7 }}>
            Choisissez votre rôle pour adapter l'expérience.
          </Typography>
          <ToggleButtonGroup
            color="primary"
            exclusive
            fullWidth
            value={role}
            onChange={(_, value: Role | null) => value && setRole(value)}
          >
            <ToggleButton value="COURIER">Livreur</ToggleButton>
            <ToggleButton value="CUSTOMER">Client</ToggleButton>
          </ToggleButtonGroup>
          {isCourier && (
            <Alert severity="info" variant="outlined">
              Un livreur doit fournir ses coordonnées complètes. La capacité maximale est fixée à 10&nbsp;kg.
            </Alert>
          )}
          <Stack spacing={1.5}>
            <TextField label="Email" value={email} onChange={(e) => setEmail(e.target.value)} fullWidth />
            <TextField
              label="Mot de passe"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
            />
            {isCourier && (
              <>
                <TextField label="Prénom" value={firstName} onChange={(e) => setFirstName(e.target.value)} fullWidth />
                <TextField label="Nom" value={lastName} onChange={(e) => setLastName(e.target.value)} fullWidth />
                <TextField label="Téléphone" value={phone} onChange={(e) => setPhone(e.target.value)} fullWidth />
                <TextField label="CNE" value={cne} onChange={(e) => setCne(e.target.value)} fullWidth />
              </>
            )}
          </Stack>
          {error && <Alert severity="error">{error}</Alert>}
          {success && <Alert severity="success">Compte créé avec succès. Vous pouvez vous connecter.</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleClose}>Fermer</Button>
        <Button variant="contained" disabled={!canSubmit} onClick={handleSubmit}>
          {submitting ? 'Création…' : "S'inscrire"}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

interface LoginDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: (payload: { token: string; user: UserProfile }) => void
}

export function LoginDialog({ open, onClose, onSuccess }: LoginDialogProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reset = () => {
    setEmail('')
    setPassword('')
    setSubmitting(false)
    setError(null)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const tokenResponse = await axios.post(`${API_BASE}/accounts/token/`, {
        username: email,
        password,
      })
      const token = tokenResponse.data.access
      const profileResponse = await axios.get(`${API_BASE}/accounts/me/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      onSuccess({ token, user: profileResponse.data as UserProfile })
      handleClose()
    } catch (err) {
      setError('Identifiants invalides. Réessayez.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>Se connecter</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField label="Email" value={email} onChange={(e) => setEmail(e.target.value)} fullWidth />
          <TextField
            label="Mot de passe"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
          />
          {error && <Alert severity="error">{error}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleClose}>Fermer</Button>
        <Button
          variant="contained"
          disabled={!email || !password || submitting}
          onClick={handleSubmit}
        >
          {submitting ? 'Connexion…' : 'Se connecter'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
