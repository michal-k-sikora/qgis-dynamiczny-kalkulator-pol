# -*- coding: utf-8 -*-
"""
Dynamiczny_kalkulator_pol Plugin Initialization
"""

from .dynamiczny_kalkulator_pol import FieldCalcDockPlugin

def classFactory(iface):
    return FieldCalcDockPlugin(iface)
