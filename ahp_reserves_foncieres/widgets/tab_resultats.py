# -*- coding: utf-8 -*-
"""
Résultats et Export.
"""
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMessageBox
)

from ..core.resultats import calculer_resultats, CLASSES_APTITUDE
from ..core.export_gpkg import exporter_couche_enrichie

# Couleurs associées à chaque classe (fond, texte), réutilisées dans la
# table des résultats et dans la légende.
COULEURS_CLASSE = {
    "Potentiel faible": ("#db1515", "#ffffff"),
    "Potentiel modéré": ("#cf820d", "#ffffff"),
    "Potentiel élevé": ("#0a4e29", "#ffffff"),
    "Incomplet": ("#eef0f3", "#5b6472"),
}


class ResultatsTab(QWidget):

    configChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPage")

        self._resultats = []
        self._noms_familles = []
        self._familles = []
        self._layer = None
        self._id_field = ""
        self._output_path = ""
        self._create_enriched_copy = True

        self._build_ui()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        title = QLabel("Résultats et Export")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        self.lbl_resume = QLabel("")
        self.lbl_resume.setWordWrap(True)
        self.lbl_resume.setObjectName("PageSubtitle")
        root.addWidget(self.lbl_resume)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        # --- Table des résultats -------------------------------------------
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        body.addWidget(self.table, stretch=3)

        # --- Légende des classes de potentiel -------------------------------
        grp_legende = QGroupBox("Classification du potentiel de mobilisation")
        grp_legende.setFixedWidth(320)
        legende_layout = QVBoxLayout(grp_legende)
        self.table_legende = self._build_table_legende()
        legende_layout.addWidget(self.table_legende)
        legende_layout.addStretch()
        body.addWidget(grp_legende, stretch=0)


        actions = QHBoxLayout()
        self.btn_exporter = QPushButton("Exporter la couche enrichie (.gpkg)")
        self.btn_exporter.setObjectName("PrimaryButton")
        actions.addStretch()
        actions.addWidget(self.btn_exporter)
        root.addLayout(actions)

        self.btn_exporter.clicked.connect(self._on_exporter_clicked)

    def _build_table_legende(self):
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Score final", "Classe"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.verticalHeader().setVisible(False)

        police = table.font()
        police.setPointSize(police.pointSize() + 2)
        table.setFont(police)
        table.horizontalHeader().setFont(police)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        table.setColumnWidth(0, 150)

        table.setRowCount(len(CLASSES_APTITUDE))
        for row, (borne_min, borne_max, libelle) in enumerate(CLASSES_APTITUDE):
            if row == len(CLASSES_APTITUDE) - 1:
                texte_borne = f"{borne_min:.2f} \u2264 S \u2264 1"
            else:
                texte_borne = f"{borne_min:.2f} \u2264 S < {borne_max:.2f}"
            table.setItem(row, 0, self._ro_item(texte_borne.replace(".", ",")))

            item_classe = self._ro_item(libelle)
            fond, texte = COULEURS_CLASSE.get(libelle, ("#ffffff", "#1c2733"))
            item_classe.setBackground(QColor(fond))
            item_classe.setForeground(QColor(texte))
            table.setItem(row, 1, item_classe)

        table.resizeRowsToContents()
        hauteur = table.horizontalHeader().height() + 4
        for row in range(table.rowCount()):
            hauteur_ligne = table.rowHeight(row) + 22  
            table.setRowHeight(row, hauteur_ligne)
            hauteur += hauteur_ligne
        table.setFixedHeight(hauteur)
        return table


    def set_context(self, familles, layer, id_field, output_path="", create_enriched_copy=True):
        self._familles = familles
        self._layer = layer
        self._id_field = id_field
        self._output_path = output_path
        self._create_enriched_copy = create_enriched_copy

        if not create_enriched_copy:
            self.btn_exporter.setEnabled(False)
            self.btn_exporter.setToolTip(
                "Décochez « Créer une copie enrichie » à l'étape Couche "
                "d'entrée pour activer l'export."
            )
        elif not output_path:
            self.btn_exporter.setEnabled(False)
            self.btn_exporter.setToolTip(
                "Renseignez un fichier de sortie à l'étape Couche d'entrée."
            )
        else:
            self.btn_exporter.setEnabled(True)
            self.btn_exporter.setToolTip("")

        if layer is None or not familles:
            self._resultats = []
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.lbl_resume.setText(
                "Aucun résultat à afficher : vérifiez que les étapes "
                "précédentes sont complètes."
            )
            self.configChanged.emit()
            return

        self._resultats = calculer_resultats(familles, layer, id_field)
        self._populate_table(familles)
        self._update_resume()
        self.configChanged.emit()

    def _populate_table(self, familles):
        noms_familles = [f.nom for f in familles]
        self._noms_familles = noms_familles
        colonnes = ["Rang", "Identifiant"] + noms_familles + ["Score final", "Classe"]
        self.table.setColumnCount(len(colonnes))
        self.table.setHorizontalHeaderLabels(colonnes)
        self.table.setRowCount(len(self._resultats))

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(1, 110)

        for row, r in enumerate(self._resultats):
            col = 0
            self.table.setItem(row, col, self._ro_item(str(r["rang"]) if r["rang"] else "–", centre=True))
            col += 1
            self.table.setItem(row, col, self._ro_item(str(r["id"])))
            col += 1
            for nom in noms_familles:
                mf = r["scores_famille"].get(nom)
                texte = self._format_decimal(mf) if mf is not None else "–"
                self.table.setItem(row, col, self._ro_item(texte, centre=True))
                col += 1

            score_txt = self._format_decimal(r["score_final"]) if r["score_final"] is not None else "–"
            self.table.setItem(row, col, self._ro_item(score_txt, centre=True))
            col += 1

            item_classe = self._ro_item(r["classe"], centre=True)
            fond, texte = COULEURS_CLASSE.get(r["classe"], ("#ffffff", "#1c2733"))
            item_classe.setBackground(QColor(fond))
            item_classe.setForeground(QColor(texte))
            self.table.setItem(row, col, item_classe)

    def _update_resume(self):
        total = len(self._resultats)
        incomplets = sum(1 for r in self._resultats if r["score_final"] is None)
        texte = (
            f"{total} réserve(s) évaluée(s), classée(s) par score décroissant "
            "(rang 1 = potentiel le plus élevé)."
        )
        if incomplets:
            texte += (
                f"  ⚠ {incomplets} réserve(s) incomplète(s) : au moins une "
                "valeur brute ne correspond à aucune ligne de son barème "
                "(étape Standardisation)."
            )
        self.lbl_resume.setText(texte)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _on_exporter_clicked(self):
        if not self._resultats or not self._output_path:
            return
        succes, message = exporter_couche_enrichie(
            self._layer, self._familles, self._id_field, self._resultats, self._output_path
        )
        if succes:
            QMessageBox.information(self, "Export réussi", message)
        else:
            QMessageBox.warning(self, "Export impossible", message)


    def _ro_item(self, texte, centre=False):
        item = QTableWidgetItem(texte)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        if centre:
            item.setTextAlignment(Qt.AlignCenter)
        return item

    def _format_decimal(self, valeur):
        return f"{valeur:.3f}".replace(".", ",")

    def is_valid(self):
        return bool(self._resultats)
