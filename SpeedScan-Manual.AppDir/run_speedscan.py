#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório atual ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar e executar o SpeedScan
from core.main import SpeedScanApp

if __name__ == "__main__":
    app = SpeedScanApp()
    app.mainloop()
