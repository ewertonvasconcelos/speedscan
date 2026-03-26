#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar os widgets do SpeedScan
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.main import SpeedScanApp

# Criar instância do app
app = SpeedScanApp()

# Testar cada widget
print("=== Teste dos Widgets do SpeedScan ===\n")

widgets = [
    ('widget_uptime', app.widget_uptime),
    ('widget_battery', app.widget_battery),
    ('widget_temps', app.widget_temps),
    ('widget_gpu', app.widget_gpu),
    ('widget_disks', app.widget_disks),
    ('widget_hostname', app.widget_hostname),
    ('widget_distro', app.widget_distro),
    ('widget_kernel', app.widget_kernel),
    ('widget_health', app.widget_health),
    ('widget_cpu', app.widget_cpu),
    ('widget_ram', app.widget_ram),
]

for name, func in widgets:
    try:
        result = func()
        print(f"{name}:")
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {result}")
        print()
    except Exception as e:
        print(f"{name}: ERRO - {e}\n")

print("=== Teste concluído ===")
