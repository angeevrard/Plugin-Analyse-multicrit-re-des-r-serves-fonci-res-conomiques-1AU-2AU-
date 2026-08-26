# -*- coding: utf-8 -*-
"""
Association des champs.

Chaque champ de la couche des réserves foncières (à l'exception du champ
identifiant défini à l'étape 1) devient un sous-critère candidat de
l'analyse. L'utilisateur lui attribue une famille de critères en texte
libre : des critères recevant le même nom de famille seront regroupés et
comparés entre eux à l'étape "Comparaison par paire des critères". Un champ dont la famille
reste vide est simplement exclu de l'analyse.

"""
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)

from ..core.criteria import SousCritere, deviner_famille_et_bareme, regrouper_par_famille

COLS = ["Famille", "Sous-critère", "Type détecté", "Statut"]


class AssociationChampsTab(QWidget):

    configChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPage")

        self._layer = None
        self._id_field = ""
        self._sous_criteres = []  

        self._build_ui()
        self._connect_signals()
        self._populate_table()
        self._refresh_controls()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        title = QLabel("Association des champs")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        left = QVBoxLayout()
        left.setSpacing(8)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        self.table.setColumnWidth(0, 260)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 130)
        left.addWidget(self.table, stretch=1)

        feedback_row = QHBoxLayout()
        lbl_aide = QLabel("Double-cliquez sur une cellule « Famille » pour la modifier.")
        lbl_aide.setObjectName("PageSubtitle")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setObjectName("PageSubtitle")
        feedback_row.addWidget(lbl_aide)
        feedback_row.addStretch()
        feedback_row.addWidget(self.lbl_feedback)
        left.addLayout(feedback_row)

        body.addLayout(left, stretch=3)

        grp_controle = QGroupBox("Contrôle des données")
        grp_controle.setFixedWidth(260)
        controle_layout = QVBoxLayout(grp_controle)
        controle_layout.setSpacing(10)

        self.lbl_check_ids = QLabel("–")
        self.lbl_check_geom = QLabel("–")
        self.lbl_check_missing = QLabel("–")
        for lbl in (self.lbl_check_ids, self.lbl_check_geom, self.lbl_check_missing):
            lbl.setWordWrap(True)
            controle_layout.addWidget(lbl)

        controle_layout.addStretch()

        self.btn_refresh_controls = QPushButton("Actualiser le contrôle")
        self.btn_refresh_controls.setObjectName("SecondaryButton")
        controle_layout.addWidget(self.btn_refresh_controls)

        body.addWidget(grp_controle, stretch=0)

    def _connect_signals(self):
        self.table.itemChanged.connect(self._on_item_changed)
        self.btn_refresh_controls.clicked.connect(self._refresh_controls)


    def set_context(self, layer, id_field):

        nouvelle_couche = layer is not None and (
            self._layer is None or layer.id() != self._layer.id()
        )
        self._layer = layer
        self._id_field = id_field

        if nouvelle_couche:
            self._sous_criteres = self._construire_sous_criteres(layer, id_field)

        self._populate_table()
        self._refresh_controls()
        self.configChanged.emit()

    def _construire_sous_criteres(self, layer, id_field):
        sous_criteres = []
        for f in layer.fields():
            nom_champ = f.name()
            if nom_champ == id_field:
                continue
            famille_suggeree, _bareme_suggere = deviner_famille_et_bareme(nom_champ)
            sous_criteres.append(SousCritere(champ=nom_champ, famille=famille_suggeree, bareme=[]))
        return sous_criteres

    def _populate_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._sous_criteres))

        for row, sc in enumerate(self._sous_criteres):
            item_famille = QTableWidgetItem(sc.famille)
            item_famille.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table.setItem(row, 0, item_famille)

            self.table.setItem(row, 1, self._ro_item(sc.champ))
            self.table.setItem(row, 2, self._ro_item(self._type_label(sc.champ)))

            self.table.removeCellWidget(row, 3)
            self.table.setCellWidget(row, 3, self._status_widget(bool(sc.famille.strip())))

        self.table.blockSignals(False)
        self._update_feedback_label()

    def _on_item_changed(self, item):
        if item.column() != 0:
            return
        row = item.row()
        if row >= len(self._sous_criteres):
            return

        self._sous_criteres[row].famille = item.text().strip()
        self.table.removeCellWidget(row, 3)
        self.table.setCellWidget(row, 3, self._status_widget(bool(self._sous_criteres[row].famille)))
        self._update_feedback_label()
        self.configChanged.emit()

    def _update_feedback_label(self):
        total = len(self._sous_criteres)
        assignes = sum(1 for sc in self._sous_criteres if sc.famille.strip())
        self.lbl_feedback.setText(f"{assignes}/{total} sous-critères catégorisés")


    def _refresh_controls(self):
        if self._layer is None:
            for lbl in (self.lbl_check_ids, self.lbl_check_geom, self.lbl_check_missing):
                lbl.setText("–")
            return

        champs_inclus = [sc.champ for sc in self._sous_criteres if sc.famille.strip()]

        identifiants = []
        nb_geom_invalides = 0
        nb_valeurs_manquantes = 0

        for feat in self._layer.getFeatures():
            if self._id_field:
                identifiants.append(feat.attribute(self._id_field))

            geom = feat.geometry()
            if geom is None or geom.isEmpty() or not geom.isGeosValid():
                nb_geom_invalides += 1

            for champ in champs_inclus:
                valeur = feat.attribute(champ)
                if valeur is None or (isinstance(valeur, str) and valeur.strip() == ""):
                    nb_valeurs_manquantes += 1

        if not self._id_field:
            self._set_check(self.lbl_check_ids, False, "Champ identifiant non défini (étape 1)")
        else:
            vides = sum(1 for v in identifiants if v in (None, ""))
            doublons = len(identifiants) - len(set(identifiants)) - vides
            if vides == 0 and doublons <= 0:
                self._set_check(self.lbl_check_ids, True, "Identifiants uniques OK")
            elif vides:
                self._set_check(self.lbl_check_ids, False, f"{vides} identifiant(s) manquant(s)")
            else:
                self._set_check(self.lbl_check_ids, False, f"{doublons} doublon(s) d'identifiant")

        if nb_geom_invalides == 0:
            self._set_check(self.lbl_check_geom, True, "0 géométrie invalide")
        else:
            self._set_check(self.lbl_check_geom, False, f"{nb_geom_invalides} géométrie(s) invalide(s)")

        if not champs_inclus:
            self.lbl_check_missing.setText("–  Aucun sous-critère catégorisé pour l'instant")
        elif nb_valeurs_manquantes == 0:
            self._set_check(self.lbl_check_missing, True, "Aucune valeur manquante")
        else:
            self._set_check(self.lbl_check_missing, None, f"{nb_valeurs_manquantes} valeur(s) manquante(s) à vérifier")

    def _set_check(self, label, state, text):
        if state is True:
            symbole, couleur = "✓", "#2f9e63"
        elif state is False:
            symbole, couleur = "✗", "#d64545"
        else:
            symbole, couleur = "⚠", "#d68a1f"
        label.setText(f'<span style="color:{couleur}; font-weight:600;">{symbole}</span>&nbsp;&nbsp;{text}')

    def _ro_item(self, text):
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        return item

    def _type_label(self, nom_champ):
        if not nom_champ or self._layer is None:
            return "–"
        idx = self._layer.fields().indexFromName(nom_champ)
        if idx < 0:
            return "–"
        return self._layer.fields().at(idx).typeName() or "–"

    def _status_widget(self, categorise):
        pill = QLabel("Catégorisé" if categorise else "Non catégorisé")
        pill.setObjectName("StatusPill")
        pill.setProperty("state", "ok" if categorise else "neutre")
        pill.setAlignment(Qt.AlignCenter)

        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.addWidget(pill)
        layout.addStretch()
        return wrapper

    def familles(self):
        """Reconstruit la liste des familles à partir des familles saisies
        par l'utilisateur (regroupement recalculé à chaque appel : léger,
        et toujours à jour)."""
        return regrouper_par_famille(self._sous_criteres)

    def is_valid(self):
        if self._layer is None:
            return False
        return any(sc.famille.strip() for sc in self._sous_criteres)
