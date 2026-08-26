# -*- coding: utf-8 -*-
"""
Standardisation.

"""
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTreeWidget,
    QTreeWidgetItem, QDoubleSpinBox, QAbstractItemView
)

from ..core.criteria import tous_les_sous_criteres, ECHELLE_STANDARDISATION

COLS_BAREME = ["Valeur brute", "valeur standardisée"]


class StandardisationTab(QWidget):

    configChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPage")

        self._familles = []      
        self._layer = None
        self._current_sc = None
        self._editing = False

        self._build_ui()
        self._connect_signals()
        self._populate_echelle_table()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        title = QLabel("Standardisation")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Définissez, pour chaque sous-critère, la correspondance entre "
            "ses valeurs brutes et une valeur d'aptitude (0 à 1) : se référer à l'échelle"
            "de standardisation."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

      
        grp_liste = QGroupBox("Sous-critères")
        grp_liste.setFixedWidth(280)
        liste_layout = QVBoxLayout(grp_liste)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        liste_layout.addWidget(self.tree)

        body.addWidget(grp_liste)

       
        right = QVBoxLayout()
        right.setSpacing(14)

        self.grp_correspondance = QGroupBox("Correspondance")
        corr_layout = QVBoxLayout(self.grp_correspondance)

        self.table_bareme = QTableWidget()
        self.table_bareme.setColumnCount(len(COLS_BAREME))
        self.table_bareme.setHorizontalHeaderLabels(COLS_BAREME)
        self.table_bareme.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_bareme.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_bareme.setSelectionMode(QTableWidget.SingleSelection)
        self.table_bareme.verticalHeader().setVisible(False)
        header = self.table_bareme.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_bareme.setColumnWidth(1, 130)
        corr_layout.addWidget(self.table_bareme)

        actions = QHBoxLayout()
        self.btn_add_row = QPushButton("+")
        self.btn_add_row.setObjectName("SecondaryButton")
        self.btn_add_row.setFixedWidth(32)
        self.btn_remove_row = QPushButton("–")
        self.btn_remove_row.setObjectName("SecondaryButton")
        self.btn_remove_row.setFixedWidth(32)
        self.btn_detect = QPushButton("Détecter les valeurs de la couche")
        self.btn_detect.setObjectName("SecondaryButton")
        self.btn_edit = QPushButton("Éditer")
        self.btn_edit.setObjectName("PrimaryButton")

        actions.addWidget(self.btn_add_row)
        actions.addWidget(self.btn_remove_row)
        actions.addWidget(self.btn_detect)
        actions.addStretch()
        actions.addWidget(self.btn_edit)
        corr_layout.addLayout(actions)

        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setObjectName("PageSubtitle")
        corr_layout.addWidget(self.lbl_feedback)

        right.addWidget(self.grp_correspondance, stretch=1)

        
        grp_echelle = QGroupBox("Échelle de standardisation")
        echelle_layout = QVBoxLayout(grp_echelle)
        self.table_echelle = QTableWidget()
        self.table_echelle.setColumnCount(2)
        self.table_echelle.setHorizontalHeaderLabels(["Définition de l'aptitude", "Valeur d'aptitude"])
        self.table_echelle.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_echelle.setSelectionMode(QTableWidget.NoSelection)
        self.table_echelle.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table_echelle.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table_echelle.verticalHeader().setVisible(False)
        e_header = self.table_echelle.horizontalHeader()
        e_header.setSectionResizeMode(0, QHeaderView.Stretch)
        e_header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_echelle.setColumnWidth(1, 130)
        echelle_layout.addWidget(self.table_echelle)
        right.addWidget(grp_echelle)

        body.addLayout(right, stretch=1)

    def _connect_signals(self):
        self.tree.currentItemChanged.connect(self._on_tree_selection_changed)
        self.btn_add_row.clicked.connect(self._on_add_row)
        self.btn_remove_row.clicked.connect(self._on_remove_row)
        self.btn_detect.clicked.connect(self._on_detect_values)
        self.btn_edit.clicked.connect(self._on_toggle_edit)

    def _populate_echelle_table(self):
        self.table_echelle.setRowCount(len(ECHELLE_STANDARDISATION))
        for row, (label, score) in enumerate(ECHELLE_STANDARDISATION):
            item_label = QTableWidgetItem(label)
            item_label.setFlags(Qt.ItemIsEnabled)
            item_score = QTableWidgetItem(self._format_score(score))
            item_score.setFlags(Qt.ItemIsEnabled)
            item_score.setTextAlignment(Qt.AlignCenter)
            self.table_echelle.setItem(row, 0, item_label)
            self.table_echelle.setItem(row, 1, item_score)

        self.table_echelle.resizeRowsToContents()
        hauteur = self.table_echelle.horizontalHeader().height() + 4
        for row in range(self.table_echelle.rowCount()):
            hauteur += self.table_echelle.rowHeight(row)
        self.table_echelle.setFixedHeight(hauteur)


    def set_context(self, familles, layer):

        self._familles = familles
        self._layer = layer

        if layer is not None:
            for _, sc in tous_les_sous_criteres(familles):
                self._detecter_valeurs_pour(sc)

        self._build_tree()

    def _sous_criteres_avec_champ(self):
        return [sc for _, sc in tous_les_sous_criteres(self._familles) if sc.champ]

  
    def _build_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()

        premier_item = None
        for famille in self._familles:
            item_famille = QTreeWidgetItem([famille.nom])
            item_famille.setFlags(Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(item_famille)
            for sc in famille.sous_criteres:
                libelle = sc.nom if self._bareme_valide(sc) else f"⚠ {sc.nom}"
                item_sc = QTreeWidgetItem([libelle])
                item_sc.setData(0, Qt.UserRole, sc)
                item_famille.addChild(item_sc)
                if premier_item is None:
                    premier_item = item_sc
            item_famille.setExpanded(True)

        self.tree.blockSignals(False)

        if premier_item is not None:
            self.tree.setCurrentItem(premier_item)
        else:
            self._set_current_sc(None)

    def _on_tree_selection_changed(self, current, previous):
        sc = current.data(0, Qt.UserRole) if current is not None else None
        self._set_current_sc(sc)

    def _set_current_sc(self, sc):
        if self._editing:
            self._commit_valeur_edits()
        self._editing = False
        self.btn_edit.setText("Éditer")
        self._current_sc = sc

        if sc is None:
            self.grp_correspondance.setTitle("Correspondance")
            self.table_bareme.setRowCount(0)
            self.lbl_feedback.setText("Sélectionnez un sous-critère associé à un champ (étape 2).")
        else:
            self.grp_correspondance.setTitle(f"Correspondance — {sc.nom}")
            self.lbl_feedback.setText("")
            self._populate_bareme_table()

        self._update_row_action_state()

    def _update_row_action_state(self):
        actif = self._current_sc is not None
        self.btn_edit.setEnabled(actif)
        self.btn_detect.setEnabled(actif and self._layer is not None)
        self.btn_add_row.setEnabled(actif and self._editing)
        self.btn_remove_row.setEnabled(actif and self._editing)


    def _populate_bareme_table(self):
        sc = self._current_sc
        self.table_bareme.setRowCount(len(sc.bareme) if sc else 0)
        if sc is None:
            return

        for row, (valeur, score) in enumerate(sc.bareme):
            if self._editing:
                item_valeur = QTableWidgetItem(valeur)
                item_valeur.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                self.table_bareme.setItem(row, 0, item_valeur)
                self.table_bareme.removeCellWidget(row, 1)
                self.table_bareme.setCellWidget(row, 1, self._build_score_spinbox(row, score))
            else:
                self.table_bareme.removeCellWidget(row, 1)
                item_valeur = QTableWidgetItem(valeur)
                item_valeur.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item_score = QTableWidgetItem(self._format_score(score))
                item_score.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item_score.setTextAlignment(Qt.AlignCenter)
                self.table_bareme.setItem(row, 0, item_valeur)
                self.table_bareme.setItem(row, 1, item_score)

        self.table_bareme.setEditTriggers(
            QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed if self._editing
            else QTableWidget.NoEditTriggers
        )

    def _build_score_spinbox(self, row, score):
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 1.0)
        spin.setSingleStep(0.25)
        spin.setDecimals(2)
        spin.setValue(score)
        spin.valueChanged.connect(lambda v, r=row: self._on_score_edited(r, v))
        return spin

    def _on_score_edited(self, row, value):
        if self._current_sc and 0 <= row < len(self._current_sc.bareme):
            valeur, _ = self._current_sc.bareme[row]
            self._current_sc.bareme[row] = (valeur, value)

    def _commit_valeur_edits(self):
        if self._current_sc is None:
            return
        nouveau_bareme = []
        for row in range(self.table_bareme.rowCount()):
            item = self.table_bareme.item(row, 0)
            texte = item.text().strip() if item else ""
            _, score = self._current_sc.bareme[row]
            nouveau_bareme.append((texte, score))
        self._current_sc.bareme = nouveau_bareme

    def _rafraichir_libelle_courant(self):
        item = self.tree.currentItem()
        if item is None or self._current_sc is None:
            return
        libelle = self._current_sc.nom if self._bareme_valide(self._current_sc) else f"⚠ {self._current_sc.nom}"
        item.setText(0, libelle)


    def _on_toggle_edit(self):
        if self._current_sc is None:
            return
        if self._editing:
            self._commit_valeur_edits()

        self._editing = not self._editing
        self.btn_edit.setText("Terminer l'édition" if self._editing else "Éditer")
        self._populate_bareme_table()
        self._update_row_action_state()

        if not self._editing:
            self._rafraichir_libelle_courant()
            self.configChanged.emit()

    def _on_add_row(self):
        if self._current_sc is None or not self._editing:
            return
        self._commit_valeur_edits()
        self._current_sc.bareme.append(("", 0.0))
        self._populate_bareme_table()
        self.table_bareme.scrollToBottom()

    def _on_remove_row(self):
        if self._current_sc is None or not self._editing:
            return
        row = self.table_bareme.currentRow()
        if row < 0 or row >= len(self._current_sc.bareme):
            return
        self._commit_valeur_edits()
        del self._current_sc.bareme[row]
        self._populate_bareme_table()

    def _detecter_valeurs_pour(self, sc):
        if self._layer is None or not sc.champ:
            return []

        valeurs_existantes = {v for v, _ in sc.bareme}
        valeurs_trouvees = set()
        for feat in self._layer.getFeatures():
            v = feat.attribute(sc.champ)
            if v is not None and str(v).strip() != "":
                valeurs_trouvees.add(str(v))

        nouvelles = sorted(valeurs_trouvees - valeurs_existantes)
        for v in nouvelles:
            sc.bareme.append((v, 0.0))
        return nouvelles

    def _on_detect_values(self):
        sc = self._current_sc
        if sc is None:
            return

        nouvelles = self._detecter_valeurs_pour(sc)

        if nouvelles:
            if not self._editing:
                self._editing = True
                self.btn_edit.setText("Terminer l'édition")
            self._populate_bareme_table()
            self._update_row_action_state()
            self.lbl_feedback.setText(
                f"{len(nouvelles)} nouvelle(s) valeur(s) ajoutée(s) depuis la couche "
                "(score à compléter)."
            )
        else:
            self.lbl_feedback.setText("Aucune valeur nouvelle détectée dans la couche.")


    def _format_score(self, score):
        return f"{score:.2f}".replace(".", ",")


    def is_valid(self):
        if self._editing:
            self._commit_valeur_edits()
        sous_criteres = self._sous_criteres_avec_champ()
        if not sous_criteres:
            return False
        return all(self._bareme_valide(sc) for sc in sous_criteres)

    def _bareme_valide(self, sc):
        return bool(sc.bareme) and all(valeur.strip() for valeur, _ in sc.bareme)
