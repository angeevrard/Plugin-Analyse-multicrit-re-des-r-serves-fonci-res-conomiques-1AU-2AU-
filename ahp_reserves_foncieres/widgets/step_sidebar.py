# -*- coding: utf-8 -*-
"""
Barre latérale indiquant la progression dans les étapes du plugin (couche
d'entrée, association des champs, standardisation, pondération AHP,
résultats, export). Chaque étape est représentée par un badge numéroté ;
le badge passe au vert lorsque l'étape est considérée comme complète.

la navigation entre étapes se fait uniquement via
les boutons "Précédent" / "Suivant" de la fenêtre principale, pour éviter
qu'on ne saute une étape sans que sa validité ait été vérifiée.

"""
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame


class StepItem(QFrame):

    def __init__(self, index, title, parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("StepItem")

        self.badge = QLabel(str(index + 1))
        self.badge.setFixedSize(22, 22)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setObjectName("StepBadge")

        self.label = QLabel(title)
        self.label.setObjectName("StepLabel")
        self.label.setWordWrap(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        layout.addWidget(self.badge)
        layout.addWidget(self.label, stretch=1)

        self.set_checked(False)
        self.set_done(False)

    def _refresh_style(self):
        for w in (self, self.badge, self.label):
            w.style().unpolish(w)
            w.style().polish(w)

    def set_checked(self, checked):
        self.setProperty("checked", checked)
        self.badge.setProperty("checked", checked)
        self.label.setProperty("checked", checked)
        self._refresh_style()

    def set_done(self, done):
        self.setProperty("done", done)
        self.badge.setProperty("done", done)
        self._refresh_style()


class StepSidebar(QWidget):

    def __init__(self, titles, parent=None):
        super().__init__(parent)
        self.setObjectName("StepSidebar")
        self.setFixedWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 14, 0, 14)
        layout.setSpacing(2)

        self._items = []
        for i, title in enumerate(titles):
            item = StepItem(i, title, self)
            layout.addWidget(item)
            self._items.append(item)

        layout.addStretch()
        self.set_current(0)

    def set_current(self, index):
        for item in self._items:
            item.set_checked(item.index == index)

    def set_step_done(self, index, done=True):
        if 0 <= index < len(self._items):
            self._items[index].set_done(done)
