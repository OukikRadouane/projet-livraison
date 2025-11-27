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
import Divider from '@mui/material/Divider'
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
  fixedRole?: Role
}

export function SignupDialog({ open, onClose, fixedRole }: SignupDialogProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [password2, setPassword2] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [phone, setPhone] = useState('')
  const [cne, setCne] = useState('')
  const [role, setRole] = useState<Role>(fixedRole ?? 'CUSTOMER')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const reset = () => {
    setEmail('')
    setPassword('')
    setPassword2('')
    setFirstName('')
    setLastName('')
    setPhone('')
    setCne('')
    setRole(fixedRole ?? 'CUSTOMER')
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
      if (password !== password2) {
        throw new Error('Les mots de passe ne correspondent pas.')
      }
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
      if (axios.isAxiosError(err) && err.response?.data) {
        const data = err.response.data as any
        if (typeof data === 'string') {
          setError(data)
        } else if (typeof data === 'object') {
          // Collect field errors into a single readable string
          const messages: string[] = []
          for (const [key, value] of Object.entries(data)) {
            if (Array.isArray(value)) {
              messages.push(`${key}: ${value.join(', ')}`)
            } else if (typeof value === 'string') {
              messages.push(`${key}: ${value}`)
            }
          }
            // Fallback generic if nothing parsed
          setError(messages.length ? messages.join(' | ') : 'Impossible de créer le compte. Vérifiez les informations fournies.')
        } else {
          setError('Impossible de créer le compte. Vérifiez les informations fournies.')
        }
      } else {
        setError((err as Error).message || 'Impossible de créer le compte.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const isCourier = role === 'COURIER'
  const canSubmit =
    !!email && !!password && !!password2 && password === password2 &&
    (firstName.trim() && lastName.trim() && phone.trim()) &&
    (!isCourier || cne.trim()) &&
    !submitting

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>Créer un compte</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" sx={{ opacity: 0.7 }}>
            Choisissez votre rôle pour adapter l'expérience.
          </Typography>
          {!fixedRole && (
            <ToggleButtonGroup
              color="primary"
              exclusive
              fullWidth
              value={role}
              onChange={(_, value: Role | null) => value && setRole(value)}
            >
              <ToggleButton value="CUSTOMER">Client</ToggleButton>
              <ToggleButton value="COURIER">Livreur</ToggleButton>
            </ToggleButtonGroup>
          )}
          <Alert severity="info" variant="outlined">
            Renseignez vos coordonnées pour créer un compte {isCourier ? 'livreur' : 'client'}. {isCourier && 'La capacité maximale est fixée à 10 kg.'}
          </Alert>
          <Stack spacing={1.5}>
            {/* Nom et prénom en premier */}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
              <TextField label="Prénom" value={firstName} onChange={(e) => setFirstName(e.target.value)} fullWidth />
              <TextField label="Nom" value={lastName} onChange={(e) => setLastName(e.target.value)} fullWidth />
            </Stack>
            {/* Coordonnées */}
            <TextField label="Email" value={email} onChange={(e) => setEmail(e.target.value)} fullWidth />
            <TextField label="Téléphone" value={phone} onChange={(e) => setPhone(e.target.value)} fullWidth />
            {isCourier && <TextField label="CNE" value={cne} onChange={(e) => setCne(e.target.value)} fullWidth />}
            {/* Passwords à la fin */}
            <TextField
              label="Mot de passe"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
            />
            <TextField
              label="Confirmer le mot de passe"
              type="password"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              fullWidth
              error={!!password2 && password !== password2}
              helperText={password2 && password !== password2 ? 'Les mots de passe ne correspondent pas.' : ''}
            />
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

interface AuthGatewayDialogProps {
  open: boolean
  onClose: () => void
  onLoginSuccess: (payload: { token: string; user: UserProfile }) => void
}

export function AuthGatewayDialog({ open, onClose, onLoginSuccess }: AuthGatewayDialogProps) {
  const [flow, setFlow] = useState<'CHOICE' | 'SIGNUP_CUSTOMER' | 'SIGNUP_COURIER' | 'LOGIN'>('CHOICE')

  const handleClose = () => {
    setFlow('CHOICE')
    onClose()
  }

  if (flow === 'SIGNUP_CUSTOMER') {
    return <SignupDialog open={open} onClose={handleClose} fixedRole="CUSTOMER" />
  }
  if (flow === 'SIGNUP_COURIER') {
    return <SignupDialog open={open} onClose={handleClose} fixedRole="COURIER" />
  }
  if (flow === 'LOGIN') {
    return <LoginDialog open={open} onClose={handleClose} onSuccess={onLoginSuccess} />
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>Authentification requise</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            Choisissez une option pour continuer.
          </Typography>
          <Button variant="contained" onClick={() => setFlow('SIGNUP_CUSTOMER')}>Créer un compte client</Button>
          <Button variant="outlined" onClick={() => setFlow('SIGNUP_COURIER')}>Créer un compte livreur</Button>
          <Divider />
          <Button color="secondary" onClick={() => setFlow('LOGIN')}>J'ai déjà un compte</Button>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleClose}>Fermer</Button>
      </DialogActions>
    </Dialog>
  )
}
