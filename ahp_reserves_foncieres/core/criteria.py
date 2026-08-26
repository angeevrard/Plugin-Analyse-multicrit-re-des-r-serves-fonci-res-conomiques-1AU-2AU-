# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .ahp import matrice_vide


@dataclass
class SousCritere:

    champ: str                                # nom du champ des sous-critères
    famille: str = ""                          # nom de la famille de critères, texte libre saisi par l'utilisateur
    bareme: List[Tuple[str, float]] = field(default_factory=list)  # (Standardisation des valeurs brutes des sous-critères)
    poids_local: float = 0.0                  # poids du sous-critères au sein de sa famille de critères
    poids_global: float = 0.0                 # poids_local x poids de la famille 

    @property
    def id(self) -> str:
        return self.champ

    @property
    def nom(self) -> str:
        return self.champ

    @property
    def champ_standardise(self) -> str:
        """Nom du champ qui portera la valeur standardisée des observations des sous-critères
        (préfixe 'std_' devant le nom du champ source)"""
        return f"std_{self.champ}"


@dataclass
class FamilleCriteres:
    """Regroupement de sous-critères sous un nom de famille commun (texte
    libre saisi par l'utilisateur"""

    nom: str
    sous_criteres: List[SousCritere] = field(default_factory=list)
    matrice_ponderation: List[List[float]] = field(default_factory=list)  
    poids: float = 0.0                        # poids de la famille de critères

    @property
    def id(self) -> str:
        return self.nom


def tous_les_sous_criteres(familles: List[FamilleCriteres]):
    for famille in familles:
        for sc in famille.sous_criteres:
            yield famille, sc


def regrouper_par_famille(
    sous_criteres: List[SousCritere],
    matrices_existantes: Optional[Dict[Tuple[str, ...], List[List[float]]]] = None,
) -> List[FamilleCriteres]:
    groupes: Dict[str, List[SousCritere]] = {}
    ordre: List[str] = []

    for sc in sous_criteres:
        nom_famille = (sc.famille or "").strip()
        if not nom_famille:
            continue
        if nom_famille not in groupes:
            groupes[nom_famille] = []
            ordre.append(nom_famille)
        groupes[nom_famille].append(sc)

    resultat = []
    for nom_famille in ordre:
        membres = groupes[nom_famille]
        cle_composition = tuple(sorted(sc.champ for sc in membres))
        matrice = None
        if matrices_existantes:
            matrice = matrices_existantes.get(cle_composition)
        if matrice is None or len(matrice) != len(membres):
            matrice = matrice_vide(len(membres))
        resultat.append(FamilleCriteres(nom=nom_famille, sous_criteres=membres, matrice_ponderation=matrice))
    return resultat


# Échelle numérique pour la standardisation des sous-critères: sert de
# légende de référence dans l'étape "Standardisation".
ECHELLE_STANDARDISATION: List[Tuple[str, float]] = [
    ("Impossible (aptitude nulle)", 0.0),
    ("Défavorable", 0.25),
    ("Neutre", 0.50),
    ("Favorable", 0.75),
    ("Très favorable", 1.0),
]

def _normalize_mot(texte: str) -> str:
    texte = texte.lower()
    remplacements = (
        ("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"),
        ("î", "i"), ("ô", "o"), ("ç", "c"), ("ù", "u"),
    )
    for a, b in remplacements:
        texte = texte.replace(a, b)
    return texte


def _tokens(texte: str) -> List[str]:
    texte = _normalize_mot(texte)
    for sep in ("_", "-", " "):
        texte = texte.replace(sep, " ")
    return [t for t in texte.split(" ") if t]


def _score_nom(reference: str, mots_cles: List[str], nom_champ: str) -> float:
    tokens_champ = _tokens(nom_champ)
    champ_concat = "".join(tokens_champ)

    for mot in [reference] + mots_cles:
        mot_concat = "".join(_tokens(mot))
        if len(mot_concat) >= 4 and champ_concat and (
            mot_concat in champ_concat or champ_concat in mot_concat
        ):
            return 1.0

    meilleur = 0.0
    for mot in mots_cles:
        for tm in _tokens(mot):
            if len(tm) < 3:
                continue
            for tc in tokens_champ:
                if len(tc) < 3:
                    continue
                if tm == tc:
                    meilleur = max(meilleur, 1.0)
                elif tm in tc or tc in tm:
                    ratio = min(len(tm), len(tc)) / max(len(tm), len(tc))
                    if ratio >= 0.6:
                        meilleur = max(meilleur, 0.8)
    return meilleur


SEUIL_SUGGESTION = 0.6


def deviner_famille_et_bareme(nom_champ: str) -> Tuple[str, List[Tuple[str, float]]]:
    meilleure_ref, meilleure_famille, meilleur_score = None, "", 0.0
    for famille_nom, sous in _REFERENCE_MEMOIRE:
        for id_ref, mots_cles in sous:
            score = _score_nom(id_ref, mots_cles, nom_champ)
            if score > meilleur_score:
                meilleur_score, meilleure_ref, meilleure_famille = score, id_ref, famille_nom

    if meilleure_ref and meilleur_score >= SEUIL_SUGGESTION:
        return meilleure_famille, list(BAREMES_PAR_DEFAUT.get(meilleure_ref, []))
    return "", []
