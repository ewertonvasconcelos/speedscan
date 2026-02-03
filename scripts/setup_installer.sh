#!/bin/bash
# Instalador Automatizado SpeedScan Pro

echo "🚀 Iniciando instalação do SpeedScan..."

# 1. Instalar dependências do sistema (Solus)
sudo eopkg it python3 python3-pillow -y

# 2. Instalar dependências do Python
pip3 install customtkinter psutil pillow --user

# 3. Dar permissão aos AppImages locais
chmod +x ~/speedscan/installers/AppImage/*.AppImage 2>/dev/null

# 4. Criar o atalho no Menu do Sistema (Desktop Entry)
mkdir -p ~/.local/share/applications
cat << 'EOT' > ~/.local/share/applications/speedscan.desktop
[Desktop Entry]
Name=SpeedScan Pro
Exec=python3 $HOME/speedscan/speedscan_app.py
Icon=$HOME/speedscan/icon.png
Type=Application
Categories=System;Settings;
Terminal=false
EOT

echo "✅ Instalação concluída! SpeedScan já aparece no seu menu."
