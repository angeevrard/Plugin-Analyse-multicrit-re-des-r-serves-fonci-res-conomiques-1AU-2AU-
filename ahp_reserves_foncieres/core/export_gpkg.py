# -*- coding: utf-8 -*-
"""
Export de la couche des résultats.

Écrit une copie de la couche d'entrée au format GeoPackage, à laquelle
sont ajoutés :
  - un champ par sous-critère, portant sa valeur standardisée (0 à 1) ;
  - un champ par famille de critères, portant son score intermédiaire de l'évaluation ;
  - le score final de l'évaluation, la classe du potentiel de mobilisation (élevé, modéré, faible) et le classement général.

"""
import re
import unicodedata

from qgis.core import (
    QgsField, QgsFeature, QgsFields, QgsVectorFileWriter, QgsProject
)
from qgis.PyQt.QtCore import QVariant

PREFIXE_CHAMP_FAMILLE = "mf_"
LONGUEUR_MAX_NOM_CHAMP = 20


def _slugifier(texte: str, longueur_max: int) -> str:
    """Conversion du nom de famille édité, en un nom sans accent, sans espace, et en minuscules"""
  
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    texte = re.sub(r"[^A-Za-z0-9]+", "_", texte).strip("_").lower()
    return texte[:longueur_max].strip("_") or "famille"


def _noms_champs_familles(familles):
    noms_utilises = set()
    correspondance = {}
    for famille in familles:
        base = PREFIXE_CHAMP_FAMILLE + _slugifier(famille.nom, LONGUEUR_MAX_NOM_CHAMP - len(PREFIXE_CHAMP_FAMILLE))
        nom = base
        suffixe = 2
        while nom in noms_utilises:
            nom = f"{base}_{suffixe}"
            suffixe += 1
        noms_utilises.add(nom)
        correspondance[famille.nom] = nom
    return correspondance


def exporter_couche_enrichie(layer, familles, id_field, resultats, chemin_sortie):
    """Écrit la couche enrichie au format GeoPackage"""
  
    if layer is None:
        return False, "Aucune couche d'entrée sélectionnée."
    if not chemin_sortie:
        return False, "Aucun fichier de sortie défini (étape Couche d'entrée)."

    tous_sous_criteres = [sc for famille in familles for sc in famille.sous_criteres]
    noms_champs_familles = _noms_champs_familles(familles)

    # --- Construction des champs : ceux de la couche d'origine, complétés
    # des champs standardisés, des scores par famille, puis du score final,
    # de la classe et du rang. ------------------------------------------
    fields = QgsFields()
    for champ in layer.fields():
        fields.append(champ)
    for sc in tous_sous_criteres:
        fields.append(QgsField(sc.champ_standardise, QVariant.Double))
    for famille in familles:
        fields.append(QgsField(noms_champs_familles[famille.nom], QVariant.Double))
    fields.append(QgsField("score_final", QVariant.Double))
    fields.append(QgsField("classe_apt", QVariant.String))
    fields.append(QgsField("rang", QVariant.Int))

    save_options = QgsVectorFileWriter.SaveVectorOptions()
    save_options.driverName = "GPKG"
    save_options.fileEncoding = "UTF-8"

    writer = QgsVectorFileWriter.create(
        chemin_sortie,
        fields,
        layer.wkbType(),
        layer.crs(),
        QgsProject.instance().transformContext(),
        save_options,
    )
    if writer is None or writer.hasError() != QgsVectorFileWriter.NoError:
        message = writer.errorMessage() if writer is not None else "Écriture impossible."
        return False, f"Échec de l'écriture du GeoPackage : {message}"

    # --- Résultats indexés par identifiant, pour retrouver rapidement
    # celui de chaque entité au moment de la recopier. -------------------
    resultats_par_id = {str(r["id"]): r for r in resultats}

    for feat in layer.getFeatures():
        id_val = str(feat.attribute(id_field)) if id_field else str(feat.id())
        resultat = resultats_par_id.get(id_val)

        nouvelle_feat = QgsFeature(fields)
        nouvelle_feat.setGeometry(feat.geometry())

        for champ in layer.fields():
            nouvelle_feat.setAttribute(champ.name(), feat.attribute(champ.name()))

        if resultat is not None:
            valeurs_std = resultat["valeurs_standardisees"]
            for sc in tous_sous_criteres:
                nouvelle_feat.setAttribute(sc.champ_standardise, valeurs_std.get(sc.champ))
            for famille in familles:
                nouvelle_feat.setAttribute(
                    noms_champs_familles[famille.nom],
                    resultat["scores_famille"].get(famille.nom),
                )
            nouvelle_feat.setAttribute("score_final", resultat["score_final"])
            nouvelle_feat.setAttribute("classe_apt", resultat["classe"])
            nouvelle_feat.setAttribute("rang", resultat["rang"])

        writer.addFeature(nouvelle_feat)

    del writer  # force l'écriture et la fermeture du fichier
    return True, f"Couche enrichie exportée vers :\n{chemin_sortie}"
