"""Loan Scout API - FastAPI application for loan simulation."""
from typing import Dict, Any, List
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from schemas import SimulationInput, Offer
from collectors.boursobank import BoursoBankSimulator, SimulationInputs
from utils import extract_loan_data


app = FastAPI(title="Loan Scout API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "loan-scout-api"}


def _parse_years(years_str: str) -> int:
    """Parse '15 ans' -> 15 (int). Retourne 0 si non-parsable."""
    try:
        return int(''.join(ch for ch in years_str if ch.isdigit()))
    except (TypeError, ValueError):
        return 0


def run_simulation_for_duration(
    sim_inputs: SimulationInputs,
    duration_years_string: str,
) -> Dict[str, Any]:
    """
    Worker qui instancie un simulateur et lance la simulation.

    Extrait les données utiles et s'assure de libérer les ressources.
    Retourne un dictionnaire normalisé (ou contenant 'error').
    """
    logger.info("Starting simulation for {}", duration_years_string)
    simulator = None
    t0 = time.perf_counter()
    try:
        simulator = BoursoBankSimulator(sim_inputs)
        simulation_result = simulator.run_simulation(duration_years_string)

        # extraire les champs textuels utiles
        result = extract_loan_data(
            simulation_result.get("raw_result", ""), duration_years_string
        )

        # Normaliser le résultat pour inclure durée, banque, raw_result
        result_normalized = {
            "Durée": duration_years_string,
            "bank": simulation_result.get("bank", ""),
            "raw_result": simulation_result.get("raw_result", ""),
            "notes": simulation_result.get("notes"),
            **result,
        }

        elapsed = time.perf_counter() - t0
        logger.info(
            "Simulation finished for {} in {:.1f}s",
            duration_years_string,
            elapsed,
        )
        return result_normalized
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception(
            "Erreur pendant la simulation pour {}: {}",
            duration_years_string,
            exc,
        )
        return {"Durée": duration_years_string, "error": str(exc)}
    finally:
        # Tenter de fermer proprement le driver si présent sur l'instance de simulateur
        try:
            if simulator is not None:
                driver = getattr(simulator, "driver", None)
                if driver is not None:
                    try:
                        driver.quit()
                    except Exception:
                        pass
        except Exception:
            pass


@app.post("/simulate", response_model=List[Offer])
def simulate(inp: SimulationInput) -> List[Offer]:
    """
    Appelle le collecteur Selenium Boursobank.

    Retourne toutes les offres (liste d'`Offer`) pour les durées demandées :
    soit une durée unique (`duration_years`), soit un intervalle
    (`duration_years_min` .. `duration_years_max`).
    """
    logger.info(
        "/simulate amount={} duration_years={} min={} max={}",
        inp.amount,
        inp.duration_years,
        getattr(inp, "duration_years_min", None),
        getattr(inp, "duration_years_max", None),
    )

    # Préparer inputs de simulation
    sim_inputs = SimulationInputs.default_values()
    sim_inputs.montant_emprunt = str(inp.amount)

    if inp.borrower_number_1_age is not None:
        sim_inputs.emprunteur1_age = str(inp.borrower_number_1_age)
    if inp.borrower_number_2_age is not None:
        sim_inputs.emprunteur2_age = str(inp.borrower_number_2_age)

    # Construire la liste des durées à simuler selon l'input
    dur_min = 15
    dur_max = 25
    loan_duration_list: List[str] = []

    # Priorité : si intervalle fourni, utiliser l'intervalle
    if (
        getattr(inp, "duration_years_min", None) is not None
        or getattr(inp, "duration_years_max", None) is not None
    ):
        dmin = getattr(inp, "duration_years_min", None)
        dmax = getattr(inp, "duration_years_max", None)
        # Si un seul des deux est fourni, compléter avec borne par défaut
        if dmin is None and dmax is not None:
            dmin = dur_min
        if dmax is None and dmin is not None:
            dmax = dur_max

        # Clamp aux bornes autorisées
        dmin = max(dur_min, int(dmin))
        dmax = min(dur_max, int(dmax))

        if dmin > dmax:
            raise HTTPException(
                status_code=400,
                detail=(
                    "'duration_years_min' doit être inférieur ou égal à "
                    "'duration_years_max'."
                ),
            )

        loan_duration_list = [f"{i} ans" for i in range(dmin, dmax + 1)]

    elif getattr(inp, "duration_years", None) is not None:
        # durée unique
        d = int(inp.duration_years)
        if d < dur_min or d > dur_max:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"duration_years doit être entre {dur_min} et "
                    f"{dur_max} ans."
                ),
            )
        loan_duration_list = [f"{d} ans"]
    else:
        # Fallback : simuler 15..25
        loan_duration_list = [f"{i} ans" for i in range(dur_min, dur_max + 1)]

    t0 = time.perf_counter()

    results: List[Dict[str, Any]] = []
    max_workers = (
        min(5, len(loan_duration_list))
        if len(loan_duration_list) > 0
        else 1
    )
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                run_simulation_for_duration, sim_inputs, duration
            ): duration
            for duration in loan_duration_list
        }

        for future in as_completed(futures):
            duration = futures[future]
            try:
                res = future.result()
                results.append(res)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.exception(
                    "Future failed for {}: {}", duration, exc
                )
                results.append(
                    {"Durée": duration, "error": str(exc)}
                )

    elapsed_seconds = int(time.perf_counter() - t0)
    logger.info("All simulations completed in {} seconds", elapsed_seconds)

    # Garder uniquement les résultats valides (sans 'error')
    successful_results = [
        r for r in results if r and "error" not in r
    ]
    if not successful_results:
        errors = [r for r in results if r and "error" in r]
        err_msg = (
            "; ".join(
                f"{e.get('Durée')}: {e.get('error')}" for e in errors
            )
            if errors
            else "Aucun résultat disponible"
        )
        logger.error("Aucun résultat valide: {}", err_msg)
        raise HTTPException(
            status_code=502,
            detail=f"Boursobank indisponible: {err_msg}",
        )

    sorted_results = sorted(
        successful_results, key=lambda x: _parse_years(x.get("Durée", ""))
    )

    # Construire une Offer par résultat trié
    offers: List[Offer] = []
    for r in sorted_results:
        try:
            offer = Offer(
                bank=r.get("bank", "") or "",
                loan_duration_in_years=r.get("Durée", "") or "",
                capital_loaned=r.get("Capital", "") or "",
                taux_nominal_fixe=r.get("Taux n. fixe", "") or "",
                remise=r.get("Remise", "") or "",
                taux_apres_remise=r.get("Taux ap. remise", "") or "",
                mensualite_avant_remise=(
                    r.get("Mensualité av. remise", "") or ""
                ),
                mensualite_apres_remise=(
                    r.get("Mensualité ap. remise", "") or ""
                ),
                assurance=r.get("Assurance", "") or "",
                economies=r.get("Économies", "") or "",
                dossier=r.get("Dossier", "") or "",
                raw_result=r.get("raw_result", "") or "",
                apr=None,
                monthly_payment=None,
                total_cost=None,
                insurance_monthly=None,
                notes=r.get("notes"),
            )
            offers.append(offer)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception(
                "Erreur lors de la construction d'une Offer pour {}: {}",
                r.get("Durée"),
                e,
            )

    if not offers:
        logger.error(
            "Aucune Offer construite à partir des résultats valides."
        )
        raise HTTPException(
            status_code=502, detail="Aucune offre exploitable"
        )

    return offers
