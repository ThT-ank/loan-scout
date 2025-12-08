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

import { useState } from 'react'

interface OffersTableProps {
  offers?: Offer[]
}

export default function OffersTable({ offers = [] }: OffersTableProps) {
  const [collapsedBanks, setCollapsedBanks] = useState<Set<string>>(new Set())

  if (!offers || offers.length === 0) {
    return (
      <div className="empty-state">
        <span className="empty-icon">📭</span>
        <p>Aucune offre à afficher</p>
        <p className="small-muted">Lancez une simulation pour voir les résultats</p>
      </div>
    )
  }

  // Grouper les offres par banque
  const offersByBank = offers.reduce((acc, offer) => {
    const bank = offer.bank || 'Inconnue'
    if (!acc[bank]) acc[bank] = []
    acc[bank].push(offer)
    return acc
  }, {} as Record<string, Offer[]>)

  const toggleBank = (bank: string) => {
    setCollapsedBanks((prev) => {
      const next = new Set(prev)
      if (next.has(bank)) {
        next.delete(bank)
      } else {
        next.add(bank)
      }
      return next
    })
  }

  return (
    <div className="offers-container">
      {Object.entries(offersByBank).map(([bank, bankOffers]) => {
        const isCollapsed = collapsedBanks.has(bank)
        return (
          <div key={bank} className="bank-offers-section">
            <div className="bank-header" onClick={() => toggleBank(bank)}>
              <div className="bank-header-left">
                <button className="collapse-button" type="button">
                  {isCollapsed ? '▶' : '▼'}
                </button>
                <h3>{bank}</h3>
              </div>
              <span className="offers-count">{bankOffers.length} offre{bankOffers.length > 1 ? 's' : ''}</span>
            </div>
            {!isCollapsed && (
              <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Durée</th>
                  <th>Capital</th>
                  <th>Taux</th>
                  <th>Remise</th>
                  <th>Mensualité</th>
                  <th>Assurance</th>
                  <th>Économies</th>
                  <th>Dossier</th>
                  <th>Notes</th>
                  <th>Raw</th>
                </tr>
              </thead>
              <tbody>
                {bankOffers.map((o, idx) => (
                  <tr key={idx}>
                    <td><strong>{o.loan_duration_in_years ?? ''}</strong></td>
                    <td>{formatCurrency(o.capital_loaned)}</td>
                    <td>
                      <div className="rate-display">
                        {o.taux_nominal_fixe ?? ''}
                        {o.taux_apres_remise && (
                          <span className="rate-after">→ {o.taux_apres_remise}</span>
                        )}
                      </div>
                    </td>
                    <td><span className="remise-badge">{o.remise ?? '-'}</span></td>
                    <td><strong className="highlight">{formatCurrency(o.mensualite_apres_remise)}</strong></td>
                    <td>{formatCurrency(o.assurance)}</td>
                    <td><span className="economies-badge">{formatCurrency(o.economies)}</span></td>
                    <td>{formatCurrency(o.dossier)}</td>
                    <td className="small-muted">{o.notes ?? ''}</td>
                    <td>
                      {o.raw_result ? (
                        <button className="raw-button" onClick={() => openRaw(o)}>
                          Voir
                        </button>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
                </tbody>
              </table>
            </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function formatCurrency(value: number | string | undefined): string {
  if (!value && value !== 0) return ''
  const s = String(value)
  if (s.includes('€') || s.includes('%')) return s
  const cleaned = s.replace(/\s/g, '').replace(',', '.')
  const n = Number(cleaned)
  if (Number.isFinite(n)) {
    const intPart = Math.round(n * 100) / 100
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 2,
    }).format(intPart)
  }
  return s
}

function openRaw(o: Offer) {
  const win = window.open('', '_blank')
  if (!win) return
  const safe = (o.raw_result || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
  win.document.title = `${o.bank || 'raw'} - ${o.loan_duration_in_years || ''}`
  win.document.body.style.fontFamily = 'Menlo, monospace, monospace'
  win.document.body.style.whiteSpace = 'pre-wrap'
  win.document.body.style.padding = '12px'
  win.document.body.innerHTML = `<pre>${safe}</pre>`
}
