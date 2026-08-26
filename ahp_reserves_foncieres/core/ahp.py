# -*- coding: utf-8 -*-
from typing import List, Tuple

Matrice = List[List[float]]


# --------------------------------------------------------------------------
# Échelle de comparaison par paires de Saaty 
# --------------------------------------------------------------------------
ECHELLE_SAATY: List[Tuple[float, str, str]] = [
    (9.0, "Importance extrême", "{x} est considéré absolument beaucoup plus important que {y}"),
    (7.0, "Importance très forte", "{x} est considéré beaucoup plus important que {y}"),
    (5.0, "Importance forte", "{x} est considéré plus important que {y}"),
    (3.0, "Importance modérée", "{x} est considéré un peu plus important que {y}"),
    (1.0, "Importance égale", "{x} et {y} ont la même importance"),
    (1 / 3, "Importance modérément moindre", "{x} est considéré un peu moins important que {y}"),
    (1 / 5, "Importance fortement moindre", "{x} est considéré moins important que {y}"),
    (1 / 7, "Importance très fortement moindre", "{x} est considéré beaucoup moins important que {y}"),
    (1 / 9, "Importance extrêmement moindre", "{x} est considéré absolument moins important que {y}"),
]

# Indice aléatoire (IA) 
INDICES_ALEATOIRES = {
    1: 0.0, 2: 0.0, 3: 0.52, 4: 0.89, 5: 1.11,
    6: 1.25, 7: 1.35, 8: 1.40, 9: 1.45, 10: 1.49,
}

# Seuil d'acceptabilité du ratio de cohérence (RC ≤ 10 %, Saaty et Vargas, 2012)
SEUIL_RC_ACCEPTABLE = 0.10


def matrice_identite(n: int) -> Matrice:
    return [[1.0 for _ in range(n)] for _ in range(n)]


def matrice_vide(n: int) -> Matrice:
    """Matrice de comparaison non renseignée : diagonale à 1 (fixe), toutes
    les autres cases à 0"""
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def matrice_complete(matrice: Matrice) -> bool:
    """Vrai si toutes les comparaisons hors diagonale ont été saisies"""
    n = len(matrice)
    return all(
        matrice[i][j] != 0.0
        for i in range(n) for j in range(n) if i != j
    )


def normaliser_matrice(matrice: Matrice) -> Matrice:
    """Normalisation de la matrice de Saaty"""
    n = len(matrice)
    sommes_colonnes = [sum(matrice[k][j] for k in range(n)) for j in range(n)]
    return [
        [
            (matrice[i][j] / sommes_colonnes[j]) if sommes_colonnes[j] else 0.0
            for j in range(n)
        ]
        for i in range(n)
    ]


def calculer_poids(matrice_normalisee: Matrice) -> List[float]:
    """Calcul du poids des critères"""
    n = len(matrice_normalisee)
    if n == 0:
        return []
    return [sum(ligne) / n for ligne in matrice_normalisee]


def calculer_lambda_max(matrice: Matrice, poids: List[float]) -> float:
    n = len(matrice)
    if n == 0:
        return 0.0
    v = [sum(matrice[i][j] * poids[j] for j in range(n)) for i in range(n)]
    lambdas = [v[i] / poids[i] if poids[i] else 0.0 for i in range(n)]
    return sum(lambdas) / n


def calculer_ratio_coherence(matrice: Matrice, poids: List[float]) -> float:
    """Ratio de cohérence RC = IC / IA, avec IC = (λmax - n) / (n - 1).

    Cas particulier n ≤ 2 : une comparaison entre au plus deux éléments est
    toujours parfaitement cohérente (l'indice aléatoire IA vaut 0 dans la
    table de la Figure 22) ; RC est alors fixé à 0 par convention plutôt
    que de diviser par zéro."""
    n = len(matrice)
    if n <= 2:
        return 0.0
    lambda_max = calculer_lambda_max(matrice, poids)
    ic = (lambda_max - n) / (n - 1)
    ia = INDICES_ALEATOIRES.get(n, INDICES_ALEATOIRES[10])
    return ic / ia if ia else 0.0


def coherence_acceptable(ratio_coherence: float) -> bool:
    """RC ≤ 10 % (seuil de cohérence) - source : Saaty et Vargas (2012)"""
    return ratio_coherence <= SEUIL_RC_ACCEPTABLE


def ponderer_et_calculer(matrice: Matrice) -> Tuple[List[float], float, float]:
    """Enchaîne les 4 étapes du calcul de pondération pour une matrice
    donnée : normalisation, poids, λmax, ratio de cohérence.
    Retourne le poids des critères, et ratio de cohérence"""
    matrice_normalisee = normaliser_matrice(matrice)
    poids = calculer_poids(matrice_normalisee)
    lambda_max = calculer_lambda_max(matrice, poids)
    rc = calculer_ratio_coherence(matrice, poids)
    return poids, lambda_max, rc


def formater_valeur_saaty(valeur: float) -> str:
    """Représentation sous forme textuelle d'une valeur de l'échelle de Saaty :
    '3' pour 3.0, '1/5' pour 0.2, etc pour plus de flexibilité au remplissage de la matrice"""
    if valeur >= 1:
        arrondi = round(valeur)
        return str(arrondi) if abs(valeur - arrondi) < 1e-6 else f"{valeur:.2f}"
    denominateur = round(1 / valeur) if valeur else 0
    return f"1/{denominateur}"


def libelle_saaty(valeur: float, x: str, y: str) -> str:
    for v, _, formulation in ECHELLE_SAATY:
        if abs(v - valeur) < 1e-9:
            return formulation.format(x=x, y=y)
    return ""
