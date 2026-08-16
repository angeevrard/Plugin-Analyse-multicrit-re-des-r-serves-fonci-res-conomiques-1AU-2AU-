# -*- coding: utf-8 -*-
import os.path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


class AhpReservesFoncieres:
    """Classe d'intégration du plugin dans QGIS."""

    MENU_NAME = "&AHP Réserves foncières"

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.dlg = None

    # ------------------------------------------------------------------
    # Appel du Plugin par QGIS
    # ------------------------------------------------------------------
    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        action = QAction(
            QIcon(icon_path),
            "Analyse AHP des réserves foncières",
            self.iface.mainWindow(),
        )
        action.triggered.connect(self.run)
        action.setEnabled(True)

        self.iface.addToolBarIcon(action)
        self.iface.addPluginToVectorMenu(self.MENU_NAME, action)
        self.actions.append(action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.MENU_NAME, action)
            self.iface.removeToolBarIcon(action)
        self.actions = []

        if self.dlg is not None:
            self.dlg.close()
            self.dlg = None

    # ------------------------------------------------------------------
    def run(self):
        from .ahp_dialog import AhpDialog

        if self.dlg is None:
            self.dlg = AhpDialog(self.iface, parent=self.iface.mainWindow())
            self.dlg.closed.connect(self._on_dialog_closed)

        self.dlg.show()
        self.dlg.raise_()
        self.dlg.activateWindow()

    def _on_dialog_closed(self):
        self.dlg = None
