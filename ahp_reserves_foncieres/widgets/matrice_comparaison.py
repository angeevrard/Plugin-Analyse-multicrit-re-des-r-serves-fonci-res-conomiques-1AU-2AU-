# -*- coding: utf-8 -*-
"""
Widget de saisie d'une matrice de comparaison par paires.

Seule la partie supérieure est éditable : l'utilisateur y
tape directement une valeur (ex. '3', '0.333' ou '1/3'). Le programme
remplit automatiquement :
"""
import re

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QFontMetrics
from qgis.PyQt.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

COULEUR_DIAGONALE = QColor("#eef0f3")
LARGEUR_MAX_LIGNE_ENTETE = 13   


def formater_valeur(valeur) -> str:
    if valeur is None:
        return ""
    if valeur == 0:
        return "0"
    arrondi = round(valeur)
    if arrondi != 0 and abs(valeur - arrondi) / abs(arrondi) < 0.01:
        return str(int(arrondi))
    return f"{valeur:.3f}"


def parser_valeur(texte: str):
    """Convertit une saisie utilisateur ('3', '0.333', '1/3', '1,5') en
    nombre strictement positif, ou Non si la saisie n'est pas valide."""
    texte = texte.strip().replace(",", ".")
    if not texte:
        return None
    try:
        if "/" in texte:
            numerateur, denominateur = texte.split("/", 1)
            valeur = float(numerateur) / float(denominateur)
        else:
            valeur = float(texte)
    except (ValueError, ZeroDivisionError):
        return None
    return valeur if valeur > 0 else None


def _decouper_libelle(texte: str, largeur_max_car: int = LARGEUR_MAX_LIGNE_ENTETE) -> str:
    morceaux = re.split(r"(?<=[ _])", texte)
    lignes, ligne = [], ""
    for morceau in morceaux:
        if not ligne or len(ligne) + len(morceau) <= largeur_max_car:
            ligne += morceau
        else:
            lignes.append(ligne.rstrip())
            ligne = morceau
    if ligne:
        lignes.append(ligne.rstrip())
    return "\n".join(lignes)


class MatriceComparaisonWidget(QTableWidget):
    matrixChanged = pyqtSignal()
    valeurInvalide = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setWordWrap(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._labels = []
        self._libelles = []
        self._matrice = None

        self.itemChanged.connect(self._on_item_changed)

    # ------------------------------------------------------------------
    def set_matrix(self, labels, noms_complets, matrice):
        self._labels = labels
        self._matrice = matrice
        self._render()

    def _render(self):
        n = len(self._labels)
        self.blockSignals(True)
        self.clear()
        self.setRowCount(n)
        self.setColumnCount(n)

        self._libelles = [_decouper_libelle(lbl) for lbl in self._labels]
        self.setHorizontalHeaderLabels(self._libelles)
        self.setVerticalHeaderLabels(self._libelles)

        for i in range(n):
            for j in range(n):
                valeur = self._matrice[i][j]
                item = QTableWidgetItem(formater_valeur(valeur))
                item.setTextAlignment(Qt.AlignCenter)
                if i == j:
                    item.setText("1")
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setBackground(COULEUR_DIAGONALE)
                elif i < j:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                    if valeur == 0:
                        item.setForeground(Qt.gray)  # pas encore renseigné
                else:
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setForeground(Qt.gray)
                self.setItem(i, j, item)

        self.blockSignals(False)
        self._appliquer_dimensions()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._labels:
            self._appliquer_dimensions()

    def _appliquer_dimensions(self):
        n = len(self._labels)
        if n == 0:
            return

        fm = QFontMetrics(self.font())
        hauteur_ligne_texte = fm.height() + 4


        largeur_necessaire = []
        hauteur_necessaire = []
        for lbl in self._libelles:
            lignes = lbl.split("\n")
            largeur_necessaire.append(max(fm.horizontalAdvance(l) for l in lignes) + 18)
            hauteur_necessaire.append(len(lignes) * hauteur_ligne_texte + 8)

        largeur_entete_v = max(largeur_necessaire)
        self.verticalHeader().setFixedWidth(largeur_entete_v)

        hauteur_entete_h = max(hauteur_necessaire)
        self.horizontalHeader().setFixedHeight(hauteur_entete_h)

        largeur_dispo = max(self.width() - largeur_entete_v - 6, sum(largeur_necessaire))
        extra_largeur = largeur_dispo - sum(largeur_necessaire)
        for j in range(n):
            self.setColumnWidth(j, largeur_necessaire[j] + extra_largeur // n)

        hauteur_dispo = max(self.height() - hauteur_entete_h - 6, sum(hauteur_necessaire))
        extra_hauteur = hauteur_dispo - sum(hauteur_necessaire)
        for i in range(n):
            self.setRowHeight(i, hauteur_necessaire[i] + extra_hauteur // n)

    # ------------------------------------------------------------------
    def _on_item_changed(self, item):
        i, j = item.row(), item.column()
        if i >= j:
            return 

        valeur = parser_valeur(item.text())
        if valeur is None:
            self.valeurInvalide.emit(item.text())
            self.blockSignals(True)
            item.setText(formater_valeur(self._matrice[i][j]))
            self.blockSignals(False)
            return

        self._matrice[i][j] = valeur
        self._matrice[j][i] = 1.0 / valeur

        self.blockSignals(True)
        item.setText(formater_valeur(valeur))
        item_reciproque = self.item(j, i)
        if item_reciproque is not None:
            item_reciproque.setText(formater_valeur(1.0 / valeur))
        self.blockSignals(False)

        self.matrixChanged.emit()
