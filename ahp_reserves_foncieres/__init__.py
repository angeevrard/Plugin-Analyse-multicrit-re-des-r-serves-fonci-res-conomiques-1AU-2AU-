# -*- coding: utf-8 -*-
"""
Plugin AHP Réserves foncières
==============================

Point d'entrée du plugin, requis par QGIS. La fonction classFactory est
appelée automatiquement au chargement du plugin et doit retourner une
instance de la classe principale (voir ahp_reserves_foncieres.py).

Développé dans le cadre du mémoire de fin d'études (M2 OTG - ADIRA) :
"Evaluation du potentiel de mobilisation des réserves foncières
économiques" - Ange SERY.
"""


def classFactory(iface):
    from .ahp_reserves_foncieres import AhpReservesFoncieres
    return AhpReservesFoncieres(iface)
