# -*- coding: utf-8 -*-
"""
Tableau de référence (figé, non éditable) : échelle de comparaison par
paires de Saaty.
"""
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFontMetrics
from qgis.PyQt.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

from ..core.ahp import ECHELLE_SAATY
from .matrice_comparaison import formater_valeur

LARGEURS_MIN = (46, 90, 150)  # Degré, Niveau, Formulation


class EchelleSaatyWidget(QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Degré", "Niveau", "Formulation"])
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setVisible(False)
        self.setWordWrap(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)

        self._degres = []
        self._formulations = []

        self.setRowCount(len(ECHELLE_SAATY))
        for row, (valeur, degre, formulation) in enumerate(ECHELLE_SAATY):
            texte_formulation = formulation.format(x="X", y="Y")
            self._degres.append(degre)
            self._formulations.append(texte_formulation)

            item_v = self._ro_item(formater_valeur(valeur))
            item_v.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 0, item_v)
            self.setItem(row, 1, self._ro_item(degre))
            self.setItem(row, 2, self._ro_item(texte_formulation))

        for col, largeur in enumerate(LARGEURS_MIN):
            self.setColumnWidth(col, largeur)

        self._appliquer_dimensions()

    def _ro_item(self, texte):
        item = QTableWidgetItem(texte)
        item.setFlags(Qt.ItemIsEnabled)
        return item

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._appliquer_dimensions()

    def _appliquer_dimensions(self):
        # --- Largeur des colonnes : au moins le minimum nécessaire, le
        # reste de la largeur disponible étant réparti au prorata pour
        # occuper tout le panneau plutôt que de laisser un espace vide.
        largeur_dispo = max(self.viewport().width(), sum(LARGEURS_MIN))
        largeur_min_totale = sum(LARGEURS_MIN)
        extra = largeur_dispo - largeur_min_totale

        largeurs = [
            largeur_min + (extra * largeur_min // largeur_min_totale)
            for largeur_min in LARGEURS_MIN
        ]
        largeurs[-1] += largeur_dispo - sum(largeurs)  # absorbe l'arrondi

        for col, largeur in enumerate(largeurs):
            self.setColumnWidth(col, max(largeur, LARGEURS_MIN[col]))

        # --- Hauteur des lignes : recalculée à partir des largeurs de
        # colonnes réellement appliquées ci-dessus.
        fm = QFontMetrics(self.font())
        largeur_niveau = self.columnWidth(1)
        largeur_formulation = self.columnWidth(2)

        hauteur_totale = self.horizontalHeader().height() + 6
        for row in range(self.rowCount()):
            h_niveau = fm.boundingRect(0, 0, largeur_niveau - 8, 5000, Qt.TextWordWrap, self._degres[row]).height()
            h_formulation = fm.boundingRect(
                0, 0, largeur_formulation - 8, 5000, Qt.TextWordWrap, self._formulations[row]
            ).height()
            hauteur = max(h_niveau, h_formulation, fm.height()) + 12
            self.setRowHeight(row, hauteur)
            hauteur_totale += hauteur

        self.setMinimumHeight(hauteur_totale)
        self.setMaximumHeight(hauteur_totale)
