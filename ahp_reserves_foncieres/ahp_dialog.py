# -*- coding: utf-8 -*-
"""
Fenêtre principale du plugin.
"""
import os.path

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QStackedWidget, QWidget,
    QPushButton, QFrame
)

from .widgets.step_sidebar import StepSidebar
from .widgets.tab_couche_entree import CoucheEntreeTab
from .widgets.tab_association_champs import AssociationChampsTab
from .widgets.tab_standardisation import StandardisationTab
from .widgets.tab_ponderation import PonderationTab
from .widgets.tab_resultats import ResultatsTab

STEP_TITLES = [
    "Couche d'entrée",
    "Association des champs",
    "Standardisation",
    "Comparaison des critères par paires",
    "Résultats et Export",
]


class AhpDialog(QDialog):

    closed = pyqtSignal()

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface

        self.setObjectName("AhpDialog")
        self.setWindowTitle("Plugin AHP – Réserves foncières")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)
        self.resize(1200, 900)

        self._build_ui()
        self._load_stylesheet()
        self._connect_signals()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = StepSidebar(STEP_TITLES, self)
        outer.addWidget(self.sidebar)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)

        self.stack = QStackedWidget()

        self.tab_couche_entree = CoucheEntreeTab()
        self.stack.addWidget(self.tab_couche_entree)

        self.tab_association = AssociationChampsTab()
        self.stack.addWidget(self.tab_association)

        self.tab_standardisation = StandardisationTab()
        self.stack.addWidget(self.tab_standardisation)

        self.tab_ponderation = PonderationTab()
        self.stack.addWidget(self.tab_ponderation)

        self.tab_resultats = ResultatsTab()
        self.stack.addWidget(self.tab_resultats)

        right_col.addWidget(self.stack, stretch=1)
        right_col.addWidget(self._build_nav_bar())

        right_widget = QWidget()
        right_widget.setLayout(right_col)
        outer.addWidget(right_widget, stretch=1)

    def _build_nav_bar(self):
        nav_frame = QFrame()
        nav_frame.setObjectName("NavBar")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(24, 10, 24, 10)

        self.btn_prev = QPushButton("Précédent")
        self.btn_prev.setObjectName("SecondaryButton")

        self.btn_next = QPushButton("Suivant")
        self.btn_next.setObjectName("PrimaryButton")

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        return nav_frame

    def _load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(__file__), "resources", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _connect_signals(self):
        self.btn_prev.clicked.connect(self._go_previous)
        self.btn_next.clicked.connect(self._go_next)
        self.tab_couche_entree.configChanged.connect(self._update_nav_state)
        self.tab_association.configChanged.connect(self._update_nav_state)
        self.tab_standardisation.configChanged.connect(self._update_nav_state)
        self.tab_ponderation.configChanged.connect(self._update_nav_state)
        self.tab_resultats.configChanged.connect(self._update_nav_state)
        self._update_nav_state()

    # ------------------------------------------------------------------
    # Navigation entre étapes
    # ------------------------------------------------------------------
    def _go_to_step(self, index):
        if index == 1:

            self.tab_association.set_context(
                self.tab_couche_entree.current_layer(),
                self.tab_couche_entree.current_id_field(),
            )
        elif index == 2:

            self.tab_standardisation.set_context(
                self.tab_association.familles(),
                self.tab_couche_entree.current_layer(),
            )
        elif index == 3:
            self.tab_ponderation.set_context(self.tab_association.familles())
        elif index == 4:
            self.tab_resultats.set_context(
                self.tab_ponderation.familles(),
                self.tab_couche_entree.current_layer(),
                self.tab_couche_entree.current_id_field(),
                self.tab_couche_entree.output_path(),
                self.tab_couche_entree.create_enriched_copy(),
            )

        self.stack.setCurrentIndex(index)
        self.sidebar.set_current(index)
        self._update_nav_state()

    def _go_previous(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self._go_to_step(idx - 1)

    def _go_next(self):
        idx = self.stack.currentIndex()
        if idx >= self.stack.count() - 1:
            self.close()
            return
        self._go_to_step(idx + 1)

    def _update_nav_state(self):
        idx = self.stack.currentIndex()
        self.btn_prev.setEnabled(idx > 0)

        derniere_etape = (idx == self.stack.count() - 1)

        if idx == 0:
            valid = self.tab_couche_entree.is_valid()
            self.sidebar.set_step_done(0, valid)
        elif idx == 1:
            valid = self.tab_association.is_valid()
            self.sidebar.set_step_done(1, valid)
        elif idx == 2:
            valid = self.tab_standardisation.is_valid()
            self.sidebar.set_step_done(2, valid)
        elif idx == 3:
            valid = self.tab_ponderation.is_valid()
            self.sidebar.set_step_done(3, valid)
        elif idx == 4:
            valid = self.tab_resultats.is_valid()
            self.sidebar.set_step_done(4, valid)
        else:
            valid = True

        if derniere_etape:
            self.btn_next.setText("Fermer")
            self.btn_next.setEnabled(True)
        else:
            self.btn_next.setText("Suivant")
            self.btn_next.setEnabled(valid)
