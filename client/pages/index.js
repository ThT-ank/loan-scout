import React, { useState, useMemo } from "react";
import OffersTable from "../components/OffersTable";

/**
 * Page principale : formulaire minimal + bouton pour lancer la simulation.
 * - Utilise la variable d'environnement NEXT_PUBLIC_API_URL (ex: http://localhost:8080)
 * - Envoie soit { duration_years } soit { duration_years_min, duration_years_max }
 * - Fournit UI par selects pour choisir une plage (15..25)
 */
export default function Home() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8080";
  const [amount, setAmount] = useState(300000);
  const [duration, setDuration] = useState(20); // champ unique
  const [durationMin, setDurationMin] = useState(""); // vide = non utilisé
  const [durationMax, setDurationMax] = useState("");
  const [age1, setAge1] = useState("");
  const [age2, setAge2] = useState("");
  const [insurance, setInsurance] = useState("");
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const DUR_MIN = 15;
  const DUR_MAX = 25;
  const durationOptions = useMemo(() => {
    const arr = [];
    for (let i = DUR_MIN; i <= DUR_MAX; i++) arr.push(i);
    return arr;
  }, []);

  // Validation client : montant ok, min/max cohérents
  const amountValid = Number.isFinite(Number(amount)) && Number(amount) >= 100000;
  const minSet = durationMin !== "" && durationMin !== null;
  const maxSet = durationMax !== "" && durationMax !== null;
  const rangeActive = minSet || maxSet; // on considère "active" si l'un est renseigné
  const minVal = minSet ? Number(durationMin) : null;
  const maxVal = maxSet ? Number(durationMax) : null;

  let rangeError = "";
  if (minSet && (minVal < DUR_MIN || minVal > DUR_MAX)) rangeError = `Durée min doit être entre ${DUR_MIN} et ${DUR_MAX}.`;
  if (maxSet && (maxVal < DUR_MIN || maxVal > DUR_MAX)) rangeError = `Durée max doit être entre ${DUR_MIN} et ${DUR_MAX}.`;
  if (minSet && maxSet && minVal > maxVal) rangeError = "La durée min doit être inférieure ou égale à la durée max.";

  const canSubmit = amountValid && !rangeError && (!rangeActive || (minSet && maxSet) || (minSet && !maxSet) || (!minSet && maxSet));

  async function handleSimulate(e) {
    e.preventDefault();
    setError("");
    setOffers([]);
    if (!canSubmit) {
      setError(rangeError || "Données invalides");
      return;
    }

    setLoading(true);

    const payload = { amount: Number(amount) };
    // Si BOTH min et max renseignés => intervalle complet
    if (minSet && maxSet) {
      payload.duration_years_min = Number(durationMin);
      payload.duration_years_max = Number(durationMax);
    } else if (minSet && !maxSet) {
      // si seul min renseigné, utiliser min comme durée unique (ou on pourrait décider d'envoyer min..max=max)
      payload.duration_years = Number(durationMin);
    } else if (!minSet && maxSet) {
      payload.duration_years = Number(durationMax);
    } else {
      // aucun min/max => durée unique
      payload.duration_years = Number(duration);
    }

    if (age1) payload.borrower_number_1_age = Number(age1);
    if (age2) payload.borrower_number_2_age = Number(age2);
    if (insurance) payload.insurance_rate = Number(insurance);

    try {
      const res = await fetch(`${API_URL}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status} : ${text}`);
      }

      const data = await res.json();
      if (Array.isArray(data)) {
        setOffers(data);
      } else if (data) {
        setOffers([data]);
      } else {
        setOffers([]);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  // helpers pour UI : disable duration input si range active
  const disableDurationInput = rangeActive;
  const infoMsg = rangeError ? rangeError : rangeActive ? `Plage active: ${minSet ? durationMin : "?"} - ${maxSet ? durationMax : "?"} ans` : `Durée unique: ${duration} ans`;

  return (
    <div className="container">
      <h1>Loan Scout — Interface de simulation</h1>
      <form onSubmit={handleSimulate} style={{ marginBottom: 20 }}>
        <div className="controls">
          <label>
            Montant (€)
            <br />
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              min="100000"
              aria-label="Montant emprunté"
            />
          </label>

          <label>
            Durée unique (années)
            <br />
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              min={DUR_MIN}
              max={DUR_MAX}
              disabled={disableDurationInput}
            />
          </label>

          <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
            <label>
              Durée min
              <br />
              <select
                value={durationMin}
                onChange={(e) => {
                  const v = e.target.value;
                  setDurationMin(v);
                  // si on active la plage, on peut synchroniser le champ duration si besoin
                }}
              >
                <option value="">—</option>
                {durationOptions.map((d) => (
                  <option key={d} value={d}>
                    {d} ans
                  </option>
                ))}
              </select>
            </label>

            <label>
              Durée max
              <br />
              <select
                value={durationMax}
                onChange={(e) => {
                  const v = e.target.value;
                  setDurationMax(v);
                }}
              >
                <option value="">—</option>
                {durationOptions.map((d) => (
                  <option key={d} value={d}>
                    {d} ans
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label>
            Age emprunteur 1
            <br />
            <input type="number" value={age1} onChange={(e) => setAge1(e.target.value)} min="18" max="99" />
          </label>

          <label>
            Age emprunteur 2
            <br />
            <input type="number" value={age2} onChange={(e) => setAge2(e.target.value)} min="18" max="99" />
          </label>

          <label>
            Taux assurance (%) (optionnel)
            <br />
            <input type="number" value={insurance} onChange={(e) => setInsurance(e.target.value)} step="0.01" min="0" />
          </label>
        </div>

        <div style={{ marginTop: 12, display: "flex", gap: 12, alignItems: "center" }}>
          <button type="submit" disabled={loading || !amountValid || !!rangeError}>
            {loading ? "Lancement des simulations..." : "Lancer la simulation"}
          </button>
          <div className="small-muted" aria-live="polite">{infoMsg}</div>
        </div>
      </form>

      {error && <div style={{ color: "red", marginBottom: 12 }}>Erreur : {error}</div>}

      <section className="results">
        <h2>Résultats</h2>
        <OffersTable offers={offers} />
      </section>
    </div>
  );
}