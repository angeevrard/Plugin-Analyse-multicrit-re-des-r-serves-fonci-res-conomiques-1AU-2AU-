# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .ahp import matrice_vide


@dataclass
class SousCritere:

    champ: str                                # nom du champ de la couche (identité du sous-critère)
    famille: str = ""                          # nom de la famille, texte libre saisi par l'utilisateur
    bareme: List[Tuple[str, float]] = field(default_factory=list)  # (valeur brute, score 0-1)
    poids_local: float = 0.0                  # poids au sein de sa famille
    poids_global: float = 0.0                 # poids_local x poids de la famille 

    @property
    def id(self) -> str:
        return self.champ

    @property
    def nom(self) -> str:
        return self.champ

    @property
    def champ_standardise(self) -> str:
        """Nom du champ qui portera la valeur d'aptitude standardisée de ce sous-critère
        (préfixe 'std_' devant le nom du champ source)."""
        return f"std_{self.champ}"


@dataclass
class FamilleCriteres:
    """Un regroupement de sous-critères sous un nom de famille commun (texte
    libre saisi par l'utilisateur."""

    nom: str
    sous_criteres: List[SousCritere] = field(default_factory=list)
    matrice_ponderation: List[List[float]] = field(default_factory=list)  # comparaison de ses sous-critères
    poids: float = 0.0                        # poids de la famille parmi les autres (étape 4)

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


BAREMES_PAR_DEFAUT = {
    "position_armature": [
        ("Ville centre et cœur métropolitain", 1.0),
        ("Polarités", 0.75),
        ("Hors polarités (villages)", 0.50),
    ],
    "acess_echangeur": [
        ("Moins de 10 minutes", 1.0),
        ("Entre 10 et 20 minutes", 0.75),
        ("Plus de 20 minutes", 0.50),
    ],
    "acess_tc": [
        ("Moins de 5 minutes", 1.0),
        ("Entre 5 et 10 minutes", 0.75),
        ("Plus de 10 minutes", 0.50),
    ],
    "articu_piste_cyclable": [
        ("Accès direct", 1.0),
        ("Accès indirect", 0.75),
        ("Absence (dans un rayon de 500 m)", 0.25),
    ],
    "acess_restauration": [
        ("Moins de 5 minutes", 1.0),
        ("Entre 5 et 10 minutes", 0.75),
        ("Plus de 10 minutes", 0.50),
    ],
    "acess_aep": [
        ("Moins de 100 m", 1.0),
        ("Plus de 100 m", 0.50),
    ],
    "proximite_res_elect": [
        ("Moins de 400 m", 1.0),
        ("Plus de 400 m", 0.50),
    ],
    "articu_zae_existante": [
        ("Contiguë ou à proximité immédiate (< 500 m)", 1.0),
        ("Plus de 500 m", 0.50),
    ],
    "enjeux_forestier": [
        ("Absence d'espace boisé", 1.0),
        ("Présence d'espace boisé", 0.25),
    ],
    "expo_risq_inondation": [
        ("Hors zone inondable", 1.0),
        ("Dans une zone inondable", 0.25),
    ],
    "expo_risque_mvt_terr": [
        ("Hors zone de risque", 1.0),
        ("Dans une zone de risque", 0.25),
    ],
    "zone_hum_res_bio": [
        ("Hors zone humide / réservoir de biodiversité", 1.0),
        ("Dans une zone humide ou un réservoir de biodiversité", 0.25),
    ],
    "pente_moy_terrain": [
        ("Inférieure ou égale à 10 %", 1.0),
        ("Entre 10 % et 20 %", 0.75),
        ("Supérieure à 20 %", 0.25),
    ],
    "maitrise_fonciere": [
        ("Entièrement maîtrisée par l'entité publique", 1.0),
        ("Maîtrise mixte (publique et privée)", 0.75),
        ("Entièrement détenue par des propriétaires privés", 0.50),
    ],
}


# Échelle générale de standardisation : sert de
# légende de référence dans l'étape "Standardisation".
ECHELLE_STANDARDISATION: List[Tuple[str, float]] = [
    ("Impossible (aptitude nulle)", 0.0),
    ("Défavorable", 0.25),
    ("Neutre", 0.50),
    ("Favorable", 0.75),
    ("Très favorable", 1.0),
]

_REFERENCE_MEMOIRE = [
    ("Attractivité géographique", [
        ("position_armature", ["armature", "position"]),
        ("acess_echangeur", ["echangeur", "autorout"]),
        ("acess_tc", ["tc", "transport", "gare", "bus"]),
        ("articu_piste_cyclable", ["cyclable", "cycl", "piste"]),
        ("acess_restauration", ["restaur", "alimentaire", "commerce"]),
    ]),
    ("Aptitude aux réseaux techniques et à la mutualisation", [
        ("acess_aep", ["aep", "eau_potable", "assainissement"]),
        ("proximite_res_elect", ["elect", "electr"]),
        ("articu_zae_existante", ["zae"]),
    ]),
    ("Enjeux forestiers, écologiques et de risques naturels", [
        ("enjeux_forestier", ["forest", "bois"]),
        ("zone_hum_res_bio", ["humide", "biodiv", "znieff", "ecolog"]),
        ("expo_risq_inondation", ["inond"]),
        ("expo_risque_mvt_terr", ["mvt_terr", "mouvement", "argile", "glissement"]),
    ]),
    ("Aptitude physique et foncière", [
        ("pente_moy_terrain", ["pente"]),
        ("maitrise_fonciere", ["maitrise", "foncier"]),
    ]),
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
