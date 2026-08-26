# -*- coding: utf-8 -*-
"""
Agrégation des critères et calcul du score final de chaque réserve
foncière
"""
from typing import Dict, List, Optional, Tuple

# Classes de catégorisation des réserves foncière selon selon le score final (bornes [min, max[)
CLASSES_APTITUDE: List[Tuple[float, float, str]] = [
    (0.0, 1 / 3, "Potentiel faible"),
    (1 / 3, 2 / 3, "Potentiel modéré"),
    (2 / 3, 1.0001, "Potentiel élevé"),
]


def _normaliser(valeur) -> str:
    if valeur is None:
        return ""
    return str(valeur).strip().lower()


def standardiser_valeur(sous_critere, valeur_brute) -> Optional[float]:
    if valeur_brute is None:
        return None
    cible = _normaliser(valeur_brute)
    if not cible:
        return None
    for valeur_reference, score in sous_critere.bareme:
        if _normaliser(valeur_reference) == cible:
            return score
    return None


def calculer_score_famille(famille, valeurs_standardisees: Dict[str, Optional[float]]) -> Optional[float]:
    total = 0.0
    for sc in famille.sous_criteres:
        x_i = valeurs_standardisees.get(sc.champ)
        if x_i is None:
            return None
        total += sc.poids_local * x_i
    return total


def calculer_score_final(familles, scores_par_famille: Dict[str, Optional[float]]) -> Optional[float]:
    total = 0.0
    for famille in familles:
        m_f = scores_par_famille.get(famille.nom)
        if m_f is None:
            return None
        total += famille.poids * m_f
    return total


def classer_score(score_final: Optional[float]) -> str:
    if score_final is None:
        return "Incomplet"
    for borne_min, borne_max, libelle in CLASSES_APTITUDE:
        if borne_min <= score_final < borne_max:
            return libelle
    return "Potentiel élevé"


def calculer_resultats(familles, layer, id_field: str) -> List[dict]:
    """Calcule, pour chaque réserve foncière, le score de chaque
    famille, le score final, sa classification et le rang"""
    
    tous_sc = [sc for famille in familles for sc in famille.sous_criteres]

    resultats = []
    for feat in layer.getFeatures():
        id_val = feat.attribute(id_field) if id_field else feat.id()

        valeurs_std = {
            sc.champ: standardiser_valeur(sc, feat.attribute(sc.champ))
            for sc in tous_sc
        }

        scores_famille = {
            famille.nom: calculer_score_famille(famille, valeurs_std)
            for famille in familles
        }

        score_final = calculer_score_final(familles, scores_famille)

        resultats.append({
            "id": id_val,
            "valeurs_standardisees": valeurs_std,
            "scores_famille": scores_famille,
            "score_final": score_final,
            "classe": classer_score(score_final),
            "rang": None,
        })

    completes = [r for r in resultats if r["score_final"] is not None]
    completes.sort(key=lambda r: r["score_final"], reverse=True)
    for rang, r in enumerate(completes, start=1):
        r["rang"] = rang

    incomplets = [r for r in resultats if r["score_final"] is None]
    return completes + incomplets
