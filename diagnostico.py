# diagnstico.py
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from core.main import SpeedScan

if __name__ == "__main__":
    app = SpeedScan()
    print("DEBUG: SpeedScan instanciado")
    app.mainloop()
