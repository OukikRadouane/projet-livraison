# Projet Livraison (Django + React)

Application de livraison simplifiée : clients créent des commandes (téléphone, localisation, articles du catalogue, offre de prix livraison). Les livreurs s'inscrivent, voient les commandes en attente et en acceptent.

## Backend
- Django 5, DRF, SimpleJWT, Channels, drf-spectacular
- Custom user avec rôles (CLIENT par défaut / COURIER)
- Endpoints principaux:
  - `POST /api/accounts/signup/` inscription (choix rôle client/livreur)
  - `POST /api/accounts/token/` obtention JWT
  - `GET /api/accounts/me/` profil de l'utilisateur connecté
  - `GET /api/catalog/items/` liste d'articles
  - `POST /api/orders/` création commande publique
  - `GET /api/orders/pending/` commandes en attente (livreur authentifié)
  - `POST /api/orders/{id}/accept/` accepter une commande
  - Schéma OpenAPI: `/api/schema/` + Swagger `/api/docs/`

## Frontend
- React 18 + Vite + TS, MUI, React Query, Axios
- Page client: création de commande
- Page livreur: inscription / connexion / commandes en attente

## Démarrage (Windows PowerShell)
```powershell
# Créer et activer l'environnement
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installer dépendances (si non installé)
pip install -r requirements.txt

# Migrations & seed catalogue
python backend/manage.py migrate
python backend/manage.py seed_catalog

# Lancer API
python backend/manage.py runserver 0.0.0.0:8000
```
Ouvrir un autre terminal pour le frontend:
```powershell
cd frontend
npm install
npm run dev
```

Accès:
- API: http://localhost:8000
- Frontend: http://localhost:5173

## Fichier .env
Ajouter éventuellement `DJANGO_SECRET_KEY=` pour override.

## Tests (placeholder)
Lancer plus tard: `pytest` (à configurer).

## Prochaines étapes
- Service d'affectation automatique (nearest courier)
- Intégration OSRM pour distances
- WebSocket notifications sur nouvelles commandes
- Validation côté frontend (formulaires + carte pour la localisation)

---
Ce README évoluera avec les nouvelles fonctionnalités.
