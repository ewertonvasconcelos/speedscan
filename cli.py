#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from core.main import *
print("SpeedScan CLI mode")
print(f"Python: {sys.version}")
try:
    import customtkinter, psutil, matplotlib
    print("✅ Todas as dep Python carregam!")
except Exception as e:
    print(f"❌ Erro: {e}")
