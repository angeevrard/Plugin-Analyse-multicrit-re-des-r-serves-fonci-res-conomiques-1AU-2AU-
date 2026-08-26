# -*- coding: utf-8 -*-
"""
Couche d'entrée.

Permet de sélectionner la couche vectorielle des réserves foncières sur
laquelle portera l'ensemble de l'analyse, d'identifier son champ
identifiant unique, et de définir le fichier GeoPackage de sortie qui
recevra la copie enrichie des résultats
"""
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox, QgsFileWidget

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)


class CoucheEntreeTab(QWidget):

    configChanged = pyqtSignal()

    NB_LIGNES_APERCU = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPage")
        self._build_ui()
        self._connect_signals()
        self._on_layer_changed(self.cb_layer.currentLayer())

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        title = QLabel("Couche d'entrée")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
        )
        subtitle.setWordWrap(True)
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        # --- Source des données ---------------------------------------
        grp_source = QGroupBox("Source des données")
        form = QFormLayout(grp_source)
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        self.cb_layer = QgsMapLayerComboBox()
        self.cb_layer.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.cb_layer.setAllowEmptyLayer(True)
        self.cb_layer.setToolTip(
            "Couche polygonale des réserves foncières (1AU/2AU) chargée dans le projet."
        )
        form.addRow("Couche des réserves foncières", self.cb_layer)

        self.cb_field_id = QgsFieldComboBox()
        self.cb_field_id.setToolTip("Champ contenant un identifiant unique par réserve.")
        form.addRow("Champ identifiant", self.cb_field_id)

        self.lbl_count = QLabel("–")
        self.lbl_count.setObjectName("ReadOnlyValue")
        form.addRow("Nombre de réserves foncières", self.lbl_count)

        self.lbl_crs = QLabel("–")
        self.lbl_crs.setObjectName("ReadOnlyValue")
        form.addRow("Système de coordonnées", self.lbl_crs)

        root.addWidget(grp_source)

        # --- Résultats ----------------------------------------------------
        grp_sortie = QGroupBox("Résultats")
        form2 = QFormLayout(grp_sortie)
        form2.setLabelAlignment(Qt.AlignRight)
        form2.setHorizontalSpacing(16)
        form2.setVerticalSpacing(10)

        self.chk_copie = QCheckBox(
            "Créer une copie enrichie de la couche d'entrée (les champs standardisés et les scores "
            "y seront ajoutés au fil de l'analyse)"
        )
        self.chk_copie.setChecked(True)
        form2.addRow("", self.chk_copie)

        self.file_output = QgsFileWidget()
        self.file_output.setStorageMode(QgsFileWidget.SaveFile)
        self.file_output.setFilter("GeoPackage (*.gpkg)")
        form2.addRow("Fichier de sortie", self.file_output)

        root.addWidget(grp_sortie)

        # --- Aperçu des attributs -----------------------------------------
        lbl_apercu = QLabel("Aperçu des attributs (premières lignes)")
        lbl_apercu.setObjectName("SectionLabel")
        root.addWidget(lbl_apercu)

        self.table_preview = QTableWidget()
        self.table_preview.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_preview.setSelectionMode(QTableWidget.NoSelection)
        self.table_preview.setAlternatingRowColors(True)
        self.table_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_preview.verticalHeader().setVisible(False)
        self.table_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.table_preview, stretch=1)

    def _connect_signals(self):
        self.cb_layer.layerChanged.connect(self._on_layer_changed)
        self.cb_field_id.fieldChanged.connect(lambda *_: self.configChanged.emit())
        self.chk_copie.toggled.connect(lambda *_: self.configChanged.emit())
        self.file_output.fileChanged.connect(lambda *_: self.configChanged.emit())

    def _on_layer_changed(self, layer):
        self.cb_field_id.setLayer(layer)

        if layer is None:
            self.lbl_count.setText("–")
            self.lbl_crs.setText("–")
            self._fill_preview(None)
            self.configChanged.emit()
            return

        self.lbl_count.setText(str(layer.featureCount()))

        crs = layer.crs()
        if crs.isValid():
            desc = crs.description()
            self.lbl_crs.setText(f"{crs.authid()} — {desc}" if desc else crs.authid())
        else:
            self.lbl_crs.setText("Non défini")

        self._fill_preview(layer)
        self.configChanged.emit()

    def _fill_preview(self, layer):
        self.table_preview.clear()
        if layer is None:
            self.table_preview.setRowCount(0)
            self.table_preview.setColumnCount(0)
            return

        field_names = [f.name() for f in layer.fields()]
        self.table_preview.setColumnCount(len(field_names))
        self.table_preview.setHorizontalHeaderLabels(field_names)

        features = []
        for feat in layer.getFeatures():
            features.append(feat)
            if len(features) >= self.NB_LIGNES_APERCU:
                break

        self.table_preview.setRowCount(len(features))
        for row, feat in enumerate(features):
            for col, name in enumerate(field_names):
                value = feat.attribute(name)
                text = "" if value is None else str(value)
                self.table_preview.setItem(row, col, QTableWidgetItem(text))


    def current_layer(self):
        return self.cb_layer.currentLayer()

    def current_id_field(self):
        return self.cb_field_id.currentField()

    def output_path(self):
        return self.file_output.filePath()

    def create_enriched_copy(self):
        return self.chk_copie.isChecked()

    def is_valid(self):
        return (
            self.current_layer() is not None
            and bool(self.current_id_field())
            and bool(self.output_path())
        )
