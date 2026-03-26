#!/bin/bash
# Build executables with PyInstaller

echo "🔨 Construindo executáveis com PyInstaller..."

# Instalar PyInstaller
pip install pyinstaller

# Construir para Linux
echo "🐧 Construindo para Linux..."
pyinstaller --onefile --windowed --name SpeedScan-Linux \
  --add-data "assets:assets" \
  --hidden-import="customtkinter" \
  --hidden-import="psutil" \
  --hidden-import="matplotlib" \
  --hidden-import="requests" \
  --hidden-import="speedtest" \
  --hidden-import="PIL" \
  core/main.py

# Mover para dist
mv dist/SpeedScan-Linux ../dist/

echo "✅ Executável Linux criado em dist/"

# Notas para Windows/macOS
echo "📝 Notas para outras plataformas:"
echo "Windows: Executar no Windows com: pyinstaller --onefile --windowed --name SpeedScan-Windows core/main.py"
echo "macOS: Executar no macOS com: pyinstaller --onefile --windowed --name SpeedScan-macOS --create-dmg core/main.py"
