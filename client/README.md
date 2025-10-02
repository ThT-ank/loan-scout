# Frontend Next.js minimal pour LoanScout

Ce frontend minimal permet de lancer l'endpoint `/simulate` et d'afficher la liste des offres.

Prérequis :
- Node.js 18+ / npm

Installation & lancement (PowerShell) :
```powershell
cd frontend
npm install
# créer .env.local à partir de .env.local.example si nécessaire
# Exemple : set NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev