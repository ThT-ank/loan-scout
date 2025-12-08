"""Pydantic schemas for loan simulation."""
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class SimulationInput(BaseModel):
    """Input schema for loan simulation request."""

    amount: int = Field(
        ..., gt=100000, description="Montant emprunté en euros"
    )

    # durée unique (optionnelle)
    duration_years: Optional[int] = Field(
        None, ge=15, le=25, description="Durée du prêt en années (unique)"
    )

    # intervalle (optionnels)
    duration_years_min: Optional[int] = Field(
        None, ge=15, le=25, description="Durée min (inclus) en années"
    )
    duration_years_max: Optional[int] = Field(
        None, ge=15, le=25, description="Durée max (inclus) en années"
    )

    borrower_number_1_age: Optional[int] = Field(None, ge=18, le=99)
    borrower_number_2_age: Optional[int] = Field(None, ge=18, le=99)
    insurance_rate: Optional[float] = Field(
        None, ge=0.0, description="Taux assurance % annuel (facultatif)"
    )

    @model_validator(mode="before")
    @classmethod
    def check_duration_fields(cls, data):
        """
        Valide que l'appel contient soit :
         - 'duration_years' (durée unique), OU
         - BOTH 'duration_years_min' et 'duration_years_max' (intervalle)
        Et s'assure que duration_years_min <= duration_years_max si fournis.
        (mode='before' : on reçoit le dict d'entrée)
        """
        # Pydantic v2: data est déjà un dict
        d = data.get("duration_years")
        dmin = data.get("duration_years_min")
        dmax = data.get("duration_years_max")

        # Exiger soit duration_years soit BOTH min & max
        if d is None and (dmin is None or dmax is None):
            raise ValueError(
                "Fournir soit 'duration_years' soit les deux "
                "'duration_years_min' et 'duration_years_max'."
            )

        # Si intervalle fourni, vérifier l'ordre
        if dmin is not None and dmax is not None and dmin > dmax:
            raise ValueError(
                "'duration_years_min' doit être inférieur ou égal à "
                "'duration_years_max'."
            )

        return data


class Offer(BaseModel):
    """Offer schema for loan simulation result."""

    bank: str
    loan_duration_in_years: str
    capital_loaned: str  # TODO: éventuellement float
    taux_nominal_fixe: str
    remise: str
    taux_apres_remise: str
    mensualite_avant_remise: str
    mensualite_apres_remise: str
    assurance: str
    economies: str
    dossier: str

    raw_result: str

    apr: Optional[float] = None  # TAEG en %
    monthly_payment: Optional[float] = None
    total_cost: Optional[float] = None
    insurance_monthly: Optional[float] = None
    notes: Optional[str] = None
