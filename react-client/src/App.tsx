import { useState, useEffect } from 'react'
import OffersTable from './components/OffersTable'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

interface Offer {
  bank?: string
  loan_duration_in_years?: number
  capital_loaned?: number | string
  taux_nominal_fixe?: string
  taux_apres_remise?: string
  remise?: string
  mensualite_apres_remise?: number | string
  assurance?: number | string
  economies?: number | string
  dossier?: number | string
  notes?: string
  raw_result?: string
}

function App() {
  const [amount, setAmount] = useState(300000)
  const [durationMin, setDurationMin] = useState(15)
  const [durationMax, setDurationMax] = useState(25)
  const [age1, setAge1] = useState('')
  const [age2, setAge2] = useState('')
  const [insurance, setInsurance] = useState('')
  const [offers, setOffers] = useState<Offer[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')

  const DUR_MIN = 15
  const DUR_MAX = 25

  const [selectedBanks, setSelectedBanks] = useState<string[]>(['fortuneo', 'boursorama', 'ing'])
  const availableBanks = [
    { id: 'fortuneo', name: 'Fortuneo', icon: '🏦' },
    { id: 'boursorama', name: 'Boursorama', icon: '💰' },
    { id: 'ing', name: 'ING', icon: '🦁' },
    { id: 'bnp', name: 'BNP Paribas', icon: '🏛️' },
    { id: 'ca', name: 'Crédit Agricole', icon: '🌾' },
  ]

  // Sanity check API au chargement
  useEffect(() => {
    const checkAPI = async () => {
      try {
        const res = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(5000) })
        if (res.ok) {
          setApiStatus('online')
        } else {
          setApiStatus('offline')
        }
      } catch {
        setApiStatus('offline')
      }
    }
    checkAPI()
    const interval = setInterval(checkAPI, 30000)
    return () => clearInterval(interval)
  }, [])

  const toggleBank = (bankId: string) => {
    setSelectedBanks((prev) =>
      prev.includes(bankId) ? prev.filter((id) => id !== bankId) : [...prev, bankId]
    )
  }

  const amountValid = Number.isFinite(Number(amount)) && Number(amount) >= 100000
  
  let rangeError = ''
  if (durationMin < DUR_MIN || durationMin > DUR_MAX)
    rangeError = `Durée min doit être entre ${DUR_MIN} et ${DUR_MAX}.`
  if (durationMax < DUR_MIN || durationMax > DUR_MAX)
    rangeError = `Durée max doit être entre ${DUR_MIN} et ${DUR_MAX}.`
  if (durationMin > durationMax)
    rangeError = 'La durée min doit être inférieure ou égale à la durée max.'

  const canSubmit = amountValid && !rangeError

  async function handleSimulate(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setOffers([])
    setProgress(0)
    setProgressMessage('')
    
    if (!canSubmit) {
      setError(rangeError || 'Données invalides')
      return
    }

    setLoading(true)
    setProgress(10)
    setProgressMessage('Préparation de la simulation...')

    const payload: any = { amount: Number(amount) }
    payload.duration_years_min = Number(durationMin)
    payload.duration_years_max = Number(durationMax)

    if (age1) payload.borrower_number_1_age = Number(age1)
    if (age2) payload.borrower_number_2_age = Number(age2)
    if (insurance) payload.insurance_rate = Number(insurance)
    if (selectedBanks.length > 0) payload.banks = selectedBanks

    try {
      setProgress(20)
      setProgressMessage('Connexion aux banques...')
      
      // Simuler une progression pendant que la requête est en cours
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev < 70) return prev + 2
          if (prev < 85) return prev + 1
          return prev
        })
      }, 500)

      const res = await fetch(`${API_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      clearInterval(progressInterval)
      setProgress(90)
      setProgressMessage('Traitement des résultats...')

      if (!res.ok) {
        const text = await res.text()
        throw new Error(`HTTP ${res.status} : ${text}`)
      }

      const data = await res.json()
      if (Array.isArray(data)) {
        setOffers(data)
      } else if (data) {
        setOffers([data])
      } else {
        setOffers([])
      }
      
      setProgress(100)
      setProgressMessage('Simulation terminée !')
      
      setTimeout(() => {
        setProgress(0)
        setProgressMessage('')
      }, 2000)
    } catch (err) {
      setError(String(err))
      setProgress(0)
      setProgressMessage('')
    } finally {
      setLoading(false)
    }
  }

  const infoMsg = rangeError || `Plage de durée: ${durationMin} - ${durationMax} ans`

  return (
    <div className="app">
      <div className="header">
        <div className="header-content">
          <h1>💰 Loan Scout</h1>
          <p className="subtitle">Comparez les meilleures offres de prêt immobilier</p>
        </div>
        <div className={`api-badge ${apiStatus}`}>
          <span className="api-dot"></span>
          {apiStatus === 'checking' ? 'Vérification...' : apiStatus === 'online' ? 'API en ligne' : 'API hors ligne'}
        </div>
      </div>

      {progress > 0 && (
        <div className="progress-container">
          <div className="progress-bar" style={{ width: `${progress}%` }}>
            <span className="progress-text">{progress}%</span>
          </div>
          {progressMessage && <p className="progress-message">{progressMessage}</p>}
        </div>
      )}

      <div className="container">
        <form onSubmit={handleSimulate} style={{ marginBottom: 20 }}>
        <div className="banks-section">
          <h3>Sélectionnez les banques</h3>
          <div className="banks-grid">
            {availableBanks.map((bank) => (
              <button
                key={bank.id}
                type="button"
                className={`bank-card ${selectedBanks.includes(bank.id) ? 'selected' : ''}`}
                onClick={() => toggleBank(bank.id)}
              >
                <span className="bank-icon">{bank.icon}</span>
                <span className="bank-name">{bank.name}</span>
                {selectedBanks.includes(bank.id) && <span className="check-mark">✓</span>}
              </button>
            ))}
          </div>
        </div>

        <div className="controls">
          <label className="full-width-control">
            Montant du prêt
            <br />
            <div className="input-with-unit">
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                min="100000"
                aria-label="Montant emprunté"
              />
              <span className="unit">€</span>
            </div>
          </label>

          <div className="duration-range-control full-width-control">
            <label>
              Durée du prêt (années)
              <div className="range-display">
                <span className="range-value primary">{durationMin} ans</span>
                <span className="range-separator">→</span>
                <span className="range-value primary">{durationMax} ans</span>
              </div>
            </label>
            <div className="dual-range-container">
              <input
                type="range"
                className="range-input range-min"
                min={DUR_MIN}
                max={DUR_MAX}
                value={durationMin}
                onChange={(e) => {
                  const val = Number(e.target.value)
                  if (val <= durationMax) setDurationMin(val)
                }}
              />
              <input
                type="range"
                className="range-input range-max"
                min={DUR_MIN}
                max={DUR_MAX}
                value={durationMax}
                onChange={(e) => {
                  const val = Number(e.target.value)
                  if (val >= durationMin) setDurationMax(val)
                }}
              />
              <div className="range-track">
                <div 
                  className="range-fill" 
                  style={{
                    left: `${((durationMin - DUR_MIN) / (DUR_MAX - DUR_MIN)) * 100}%`,
                    right: `${100 - ((durationMax - DUR_MIN) / (DUR_MAX - DUR_MIN)) * 100}%`
                  }}
                />
              </div>
            </div>
          </div>

          <label>
            Age emprunteur 1
            <br />
            <input
              type="number"
              value={age1}
              onChange={(e) => setAge1(e.target.value)}
              min="18"
              max="99"
            />
          </label>

          <label>
            Age emprunteur 2
            <br />
            <input
              type="number"
              value={age2}
              onChange={(e) => setAge2(e.target.value)}
              min="18"
              max="99"
            />
          </label>

          <label>
            Taux assurance (%) (optionnel)
            <br />
            <input
              type="number"
              value={insurance}
              onChange={(e) => setInsurance(e.target.value)}
              step="0.01"
              min="0"
            />
          </label>
        </div>

        <div style={{ marginTop: 12, display: 'flex', gap: 12, alignItems: 'center' }}>
          <button type="submit" disabled={loading || !amountValid || !!rangeError}>
            {loading ? 'Lancement des simulations...' : 'Lancer la simulation'}
          </button>
          <div className="small-muted" aria-live="polite">
            {infoMsg}
          </div>
        </div>
      </form>

      {error && <div className="error-message">⚠️ Erreur : {error}</div>}

        <section className="results">
          <h2>📊 Résultats de la simulation</h2>
          {offers.length > 0 && (
            <div className="results-summary">
              <div className="summary-card">
                <span className="summary-label">Offres trouvées</span>
                <span className="summary-value">{offers.length}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Banques</span>
                <span className="summary-value">{new Set(offers.map(o => o.bank)).size}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Meilleure mensualité</span>
                <span className="summary-value">
                  {Math.min(...offers.map(o => {
                    const val = typeof o.mensualite_apres_remise === 'string' 
                      ? parseFloat(o.mensualite_apres_remise.replace(/[^0-9.-]/g, '')) 
                      : o.mensualite_apres_remise || Infinity
                    return val
                  })).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}
                </span>
              </div>
            </div>
          )}
          <OffersTable offers={offers} />
        </section>
      </div>
    </div>
  )
}

export default App
