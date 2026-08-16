# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)

from ..core.ahp import matrice_vide, matrice_complete, ponderer_et_calculer, coherence_acceptable
from .matrice_comparaison import MatriceComparaisonWidget
from .echelle_saaty import EchelleSaatyWidget

CLE_FAMILLES = ("__familles__",)


class PonderationTab(QWidget):
    """Etape 4  : Comparaison des critères par paires (matrice de Saaty)."""

    configChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPage")

        self._familles = []          # dernier regroupement reçu (reconstruit à chaque appel de familles())
        self._matrice_familles = []  # comparaison des familles entre elles
        self._matrices_par_composition = {}  # composition -> matrice (persiste tant que la composition ne change pas)
        self._rc = {}       # composition -> dernier RC calculé (peut être > 10 %)
        self._agrege = {}   # composition -> True si l'agrégation a été validée pour cette matrice
        self._vue = "sous_criteres"  # "sous_criteres" ou "familles"

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        title = QLabel("Comparaison des critères par paires (matrice de Saaty)")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Comparez les critères deux à deux à partir de l'échelle de comparaison : renseignez uniquement la "
            "partie supérieure de la matrice (le terme symétrique et la "
            "diagonale se remplissent automatiquement)."
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        body.addLayout(self._build_left_column(), stretch=3)
        body.addLayout(self._build_right_column(), stretch=2)

    def _build_left_column(self):
        left = QVBoxLayout()
        left.setSpacing(10)

        # --- Sélecteur de vue --------------------------------------------
        selecteur = QHBoxLayout()
        self.btn_view_sc = QPushButton("Sous-critères")
        self.btn_view_familles = QPushButton("Familles de critères")
        for b in (self.btn_view_sc, self.btn_view_familles):
            b.setCheckable(True)
            b.setAutoExclusive(True)
            b.setObjectName("SecondaryButton")
        self.btn_view_sc.setChecked(True)
        self.btn_view_familles.setEnabled(False)
        self.btn_view_familles.setToolTip(
            "Disponible une fois que l'agrégation des sous-critères a été "
            "validée pour chaque famille."
        )

        self.cb_famille = QComboBox()
        self.cb_famille.setMinimumWidth(220)

        selecteur.addWidget(self.btn_view_sc)
        selecteur.addWidget(self.btn_view_familles)
        selecteur.addStretch()
        selecteur.addWidget(self.cb_famille)
        left.addLayout(selecteur)

        # --- Matrice de comparaison : occupe tout l'espace restant --------
        self.grp_matrice = QGroupBox("Matrice de comparaison")
        matrice_layout = QVBoxLayout(self.grp_matrice)
        self.matrix_widget = MatriceComparaisonWidget()
        matrice_layout.addWidget(self.matrix_widget)
        left.addWidget(self.grp_matrice, stretch=1)

        # --- Message d'erreur de saisie ------------------------------------
        self.lbl_erreur = QLabel("")
        self.lbl_erreur.setStyleSheet("color: #b23a3a;")
        self.lbl_erreur.setWordWrap(True)
        left.addWidget(self.lbl_erreur)

        # --- Ratio de cohérence, puis les deux boutons d'action ------------
        self.lbl_rc = QLabel("")
        self.lbl_rc.setWordWrap(True)
        left.addWidget(self.lbl_rc)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_calculer_coherence = QPushButton("Calculer la cohérence des jugements")
        self.btn_calculer_coherence.setObjectName("SecondaryButton")
        self.btn_agreger = QPushButton("Agrégation des sous-critères")
        self.btn_agreger.setObjectName("PrimaryButton")
        btn_row.addStretch()
        btn_row.addWidget(self.btn_calculer_coherence)
        btn_row.addWidget(self.btn_agreger)
        left.addLayout(btn_row)

        return left

    def _build_right_column(self):
        right = QVBoxLayout()
        right.setSpacing(12)

        # --- Tableau de poids contextuel (sous-critères OU familles) -----
        self.grp_poids = QGroupBox("Poids des sous-critères")
        poids_layout = QVBoxLayout(self.grp_poids)
        self.table_poids = QTableWidget()
        self.table_poids.setColumnCount(2)
        self.table_poids.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_poids.setSelectionMode(QTableWidget.NoSelection)
        self.table_poids.verticalHeader().setVisible(False)
        h1 = self.table_poids.horizontalHeader()
        h1.setSectionResizeMode(0, QHeaderView.Stretch)
        h1.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_poids.setColumnWidth(1, 90)
        self.table_poids.setMaximumHeight(160)
        poids_layout.addWidget(self.table_poids)
        right.addWidget(self.grp_poids)

        # --- Échelle de Saaty (référence fixe), pleine largeur --------------
        grp_echelle = QGroupBox("Échelle de comparaison par paires (Saaty, 1980)")
        echelle_layout = QVBoxLayout(grp_echelle)
        self.table_echelle = EchelleSaatyWidget()
        echelle_layout.addWidget(self.table_echelle)
        right.addWidget(grp_echelle, stretch=1)

        return right

    def _connect_signals(self):
        self.btn_view_sc.toggled.connect(self._on_view_toggled)
        self.btn_view_familles.toggled.connect(self._on_view_toggled)
        self.cb_famille.currentIndexChanged.connect(self._on_famille_combo_changed)
        self.matrix_widget.matrixChanged.connect(self._on_matrix_changed)
        self.matrix_widget.valeurInvalide.connect(self._on_valeur_invalide)
        self.btn_calculer_coherence.clicked.connect(self._on_calculer_coherence_clicked)
        self.btn_agreger.clicked.connect(self._on_agreger_clicked)

    # ------------------------------------------------------------------
    # Contexte fourni par les étapes précédentes
    # ------------------------------------------------------------------
    def set_context(self, familles):
        self._familles = familles

        for famille in familles:
            famille.matrice_ponderation = self._obtenir_matrice(
                self._cle_pour_famille(famille), len(famille.sous_criteres)
            )
        self._matrice_familles = self._obtenir_matrice(
            self._cle_pour_familles(familles), len(familles)
        )

        self._build_family_combo()
        self._recalculer_poids_toutes_familles()
        self._recalculer_poids_entre_familles()
        self._recalculer_poids_globaux()
        self._mettre_a_jour_disponibilite_familles()
        self._render_current_view(rebuild_matrix=True)

    def _obtenir_matrice(self, cle, n):
        """Retourne la matrice de comparaison associée à une composition
        (une famille de champs, ou l'ensemble des noms de familles),
        créée vide (matrice_vide) si elle n'existe pas encore."""
        matrice = self._matrices_par_composition.get(cle)
        if matrice is None or len(matrice) != n:
            matrice = matrice_vide(n)
            self._matrices_par_composition[cle] = matrice
        return matrice

    def _cle_pour_famille(self, famille):
        return tuple(sorted(sc.champ for sc in famille.sous_criteres))

    def _cle_pour_familles(self, familles):
        return CLE_FAMILLES + tuple(sorted(f.nom for f in familles))

    def _cle_courante(self):
        if self._vue == "familles":
            return self._cle_pour_familles(self._familles)
        famille = self._famille_selectionnee()
        return self._cle_pour_famille(famille) if famille else None

    def _matrice_courante(self):
        if self._vue == "familles":
            return self._matrice_familles
        famille = self._famille_selectionnee()
        return famille.matrice_ponderation if famille else None

    def _build_family_combo(self):
        self.cb_famille.blockSignals(True)
        self.cb_famille.clear()
        for famille in self._familles:
            self.cb_famille.addItem(famille.nom, famille.id)
        self.cb_famille.blockSignals(False)

    def _famille_selectionnee(self):
        idx = self.cb_famille.currentIndex()
        if 0 <= idx < len(self._familles):
            return self._familles[idx]
        return self._familles[0] if self._familles else None

    # ------------------------------------------------------------------
    # Calcul des Poids (en direct)
    # ------------------------------------------------------------------
    def _recalculer_poids_famille(self, famille):
        poids, _, _ = ponderer_et_calculer(famille.matrice_ponderation)
        for sc, p in zip(famille.sous_criteres, poids):
            sc.poids_local = p

    def _recalculer_poids_toutes_familles(self):
        for famille in self._familles:
            self._recalculer_poids_famille(famille)

    def _recalculer_poids_entre_familles(self):
        if not self._familles:
            return
        poids, _, _ = ponderer_et_calculer(self._matrice_familles)
        for famille, p in zip(self._familles, poids):
            famille.poids = p

    def _recalculer_poids_globaux(self):
        for famille in self._familles:
            for sc in famille.sous_criteres:
                sc.poids_global = sc.poids_local * famille.poids

    def _mettre_a_jour_disponibilite_familles(self):
        """L'onglet Familles ne se débloque que lorsque l'agrégation a été
        explicitement validée pour chaque famille de sous-critères."""
        tous_agreges = bool(self._familles) and all(
            self._agrege.get(self._cle_pour_famille(f), False) for f in self._familles
        )
        self.btn_view_familles.setEnabled(tous_agreges)
        if not tous_agreges and self._vue == "familles":
            self.btn_view_sc.setChecked(True)

    # ------------------------------------------------------------------
    # Affichage de la vue courante (matrice + poids + RC)
    # ------------------------------------------------------------------
    def _on_view_toggled(self, checked):
        if not checked:
            return
        self._vue = "familles" if self.btn_view_familles.isChecked() else "sous_criteres"
        self._render_current_view(rebuild_matrix=True)

    def _on_famille_combo_changed(self, _index):
        if self._vue == "sous_criteres":
            self._render_current_view(rebuild_matrix=True)

    def _on_matrix_changed(self):
        self.lbl_erreur.setText("")
        cle = self._cle_courante()

        if self._vue == "familles":
            self._recalculer_poids_entre_familles()
        else:
            famille = self._famille_selectionnee()
            if famille is not None:
                self._recalculer_poids_famille(famille)

        self._recalculer_poids_globaux()
        if cle is not None:
            self._rc.pop(cle, None)
            self._agrege[cle] = False

        self._mettre_a_jour_disponibilite_familles()
        self._render_current_view(rebuild_matrix=False)
        self.configChanged.emit()

    def _on_valeur_invalide(self, texte_saisi):
        self.lbl_erreur.setText(
            f"Valeur « {texte_saisi} » non reconnue : saisissez un nombre positif "
            "(par exemple 3, 0.333 ou 1/3)."
        )

    def _on_calculer_coherence_clicked(self):
        cle = self._cle_courante()
        matrice = self._matrice_courante()
        if cle is None or matrice is None or not matrice_complete(matrice):
            return  # le bouton est normalement désactivé dans ce cas ; sécurité

        if self._vue == "familles":
            self._recalculer_poids_entre_familles()
        else:
            famille = self._famille_selectionnee()
            if famille is not None:
                self._recalculer_poids_famille(famille)
        self._recalculer_poids_globaux()

        _, _, rc = ponderer_et_calculer(matrice)
        self._rc[cle] = rc

        self._render_current_view(rebuild_matrix=False)
        self.configChanged.emit()

    def _on_agreger_clicked(self):
        cle = self._cle_courante()
        rc = self._rc.get(cle)
        if cle is None or rc is None or not coherence_acceptable(rc):
            return  # le bouton est normalement désactivé dans ce cas ; sécurité

        self._agrege[cle] = True
        self._mettre_a_jour_disponibilite_familles()
        self._render_current_view(rebuild_matrix=False)
        self.configChanged.emit()

    def _render_current_view(self, rebuild_matrix):
        if not self._familles:
            return

        self.cb_famille.setVisible(self._vue == "sous_criteres")

        if self._vue == "familles":
            self.grp_matrice.setTitle("Matrice de comparaison — Familles de critères")
            self.btn_agreger.setText("Agrégation des familles de critères")
            labels = [f.id for f in self._familles]
            noms = [f.nom for f in self._familles]
            if rebuild_matrix:
                self.matrix_widget.set_matrix(labels, noms, self._matrice_familles)
            self._render_table_poids(
                "Poids des familles de critères", "Famille de critères",
                [(f.nom, f.poids) for f in self._familles],
            )
        else:
            famille = self._famille_selectionnee()
            if famille is None:
                return
            self.grp_matrice.setTitle(f"Matrice de comparaison — {famille.nom}")
            self.btn_agreger.setText("Agrégation des sous-critères")
            labels = [sc.id for sc in famille.sous_criteres]
            noms = [sc.nom for sc in famille.sous_criteres]
            if rebuild_matrix:
                self.matrix_widget.set_matrix(labels, noms, famille.matrice_ponderation)
            self._render_table_poids(
                f"Poids des sous-critères — {famille.nom}", "Sous-critère",
                [(sc.nom, sc.poids_local) for sc in famille.sous_criteres],
            )

        self._rafraichir_etat_boutons()
        self._render_rc()

    def _rafraichir_etat_boutons(self):
        matrice = self._matrice_courante()
        if matrice is None:
            self.btn_calculer_coherence.setEnabled(False)
            self.btn_agreger.setEnabled(False)
            return

        complete = matrice_complete(matrice)
        self.btn_calculer_coherence.setEnabled(complete)

        cle = self._cle_courante()
        rc = self._rc.get(cle)
        deja_agrege = self._agrege.get(cle, False)
        rc_acceptable = rc is not None and coherence_acceptable(rc)
        self.btn_agreger.setEnabled(rc_acceptable and not deja_agrege)

    def _render_table_poids(self, titre, entete_colonne, items):
        self.grp_poids.setTitle(titre)
        self.table_poids.setHorizontalHeaderLabels([entete_colonne, "Poids"])
        self.table_poids.setRowCount(len(items))
        for row, (nom, poids) in enumerate(items):
            self.table_poids.setItem(row, 0, self._ro_item(nom))
            item_p = self._ro_item(self._format_decimal(poids))
            item_p.setTextAlignment(Qt.AlignCenter)
            self.table_poids.setItem(row, 1, item_p)

    def _render_rc(self):
        matrice = self._matrice_courante()
        cle = self._cle_courante()

        if matrice is None or cle is None:
            self.lbl_rc.setText("")
            return

        if not matrice_complete(matrice):
            self.lbl_rc.setText(
                '<span style="font-size:14px; font-weight:700; color:#6b7280;">'
                "Ratio de cohérence : renseignez toutes les comparaisons de la "
                "matrice avant de pouvoir le calculer.</span>"
            )
            return

        rc = self._rc.get(cle)
        if rc is None:
            self.lbl_rc.setText(
                '<span style="font-size:14px; font-weight:700; color:#6b7280;">'
                "Ratio de cohérence : non calculé — cliquez sur « Calculer la "
                "cohérence des jugements ».</span>"
            )
            return

        ok = coherence_acceptable(rc)
        symbole, couleur = ("✓", "#2f9e63") if ok else ("⚠", "#d68a1f")
        texte = "Cohérence acceptable" if ok else "Cohérence à améliorer (RC > 10 %)"
        suffixe = "  —  Agrégation validée ✓" if self._agrege.get(cle, False) else ""
        self.lbl_rc.setText(
            f'<span style="font-size:14px; font-weight:700; color:{couleur};">'
            f"{symbole}&nbsp;&nbsp;Ratio de cohérence (RC) : {rc * 100:.1f} % — {texte}{suffixe}</span>"
        )

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------
    def _ro_item(self, texte):
        item = QTableWidgetItem(texte)
        item.setFlags(Qt.ItemIsEnabled)
        return item

    def _format_decimal(self, valeur):
        return f"{valeur:.3f}".replace(".", ",")

    # ------------------------------------------------------------------
    # Accesseurs utilisés par le reste du plugin
    # ------------------------------------------------------------------
    def familles(self):
        return self._familles

    def is_valid(self):
        if not self._familles:
            return False
        if not self._agrege.get(self._cle_pour_familles(self._familles), False):
            return False
        return all(
            self._agrege.get(self._cle_pour_famille(f), False) for f in self._familles
        )
