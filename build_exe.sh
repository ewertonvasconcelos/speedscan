#!/bin/bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --icon="icon.png" --add-data "icon.png:." speedscan_app.py
echo "✅ Binário criado na pasta /dist"
