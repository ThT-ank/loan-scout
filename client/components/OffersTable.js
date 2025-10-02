import React from "react";

/**
 * Affiche un tableau simple des offres (props.offers : array d'objets Offer).
 * Ajout : formatage monétaire basique et affichage des notes/raw.
 */
export default function OffersTable({ offers = [] }) {
  if (!offers || offers.length === 0) {
    return <div className="small-muted">Aucune offre à afficher.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Banque</th>
            <th>Durée</th>
            <th>Capital</th>
            <th>Taux</th>
            <th>Remise</th>
            <th>Mensualité (après)</th>
            <th>Assurance</th>
            <th>Économies</th>
            <th>Dossier</th>
            <th>Notes</th>
            <th>Raw</th>
          </tr>
        </thead>
        <tbody>
          {offers.map((o, idx) => (
            <tr key={idx}>
              <td>{o.bank ?? ""}</td>
              <td>{o.loan_duration_in_years ?? ""}</td>
              <td>{formatCurrency(o.capital_loaned)}</td>
              <td>
                {o.taux_nominal_fixe ?? ""} {o.taux_apres_remise ? `→ ${o.taux_apres_remise}` : ""}
              </td>
              <td>{o.remise ?? ""}</td>
              <td>{formatCurrency(o.mensualite_apres_remise)}</td>
              <td>{formatCurrency(o.assurance)}</td>
              <td>{formatCurrency(o.economies)}</td>
              <td>{formatCurrency(o.dossier)}</td>
              <td className="small-muted">{o.notes ?? ""}</td>
              <td>
                {o.raw_result ? (
                  <button
                    className="raw-button"
                    onClick={() => openRaw(o)}
                  >
                    Voir
                  </button>
                ) : "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCurrency(value) {
  if (!value && value !== 0) return "";
  // Accepte les valeurs déjà formatées (string contenant €) ou numériques
  const s = String(value);
  if (s.includes("€") || s.includes("%")) return s;
  // retirer espaces et convertir virgule -> point si présent
  const cleaned = s.replace(/\s/g, "").replace(",", ".");
  const n = Number(cleaned);
  if (Number.isFinite(n)) {
    // formatage simple : 300000 -> "300 000 €" ou float -> "1 234,56 €"
    const intPart = Math.round(n * 100) / 100;
    return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 2 }).format(intPart);
  }
  return s;
}

function openRaw(o) {
  const win = window.open("", "_blank");
  if (!win) return;
  const safe = (o.raw_result || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  win.document.title = `${o.bank || "raw"} - ${o.loan_duration_in_years || ""}`;
  win.document.body.style.fontFamily = "Menlo, monospace, monospace";
  win.document.body.style.whiteSpace = "pre-wrap";
  win.document.body.style.padding = "12px";
  win.document.body.innerHTML = `<pre>${safe}</pre>`;
}