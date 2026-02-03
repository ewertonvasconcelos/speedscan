#!/bin/bash
echo "🚀 Iniciando instalação universal do SpeedScan..."

# Detecção refinada para Solus
if command -v eopkg &> /dev/null; then
    echo "📦 Detectado Solus OS. Ajustando pacotes..."
    # Instalamos um por um para evitar que o erro de um pare todos
    sudo eopkg it -y python3 python-pillow python-psutil python3-tkinter
elif command -v apt &> /dev/null; then
    sudo apt install -y python3 python3-pip python3-tk python3-pil python3-psutil
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3 python3-tkinter python3-pillow python3-psutil
elif command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm python python-pillow python-psutil tk
fi

echo "🐍 Verificando bibliotecas Python..."
pip3 install customtkinter pillow psutil --user --upgrade

echo "📂 Atualizando atalho e permissões..."
chmod +x ~/speedscan/speedscan_app.py
mkdir -p ~/.local/share/applications
cat << EOM > ~/.local/share/applications/speedscan.desktop
[Desktop Entry]
Name=SpeedScan
Exec=python3 $HOME/speedscan/speedscan_app.py
Icon=$HOME/speedscan/icon.png
Terminal=false
Type=Application
Categories=System;Settings;
Comment=Otimização e Diagnóstico de Sistema
EOM

chmod +x ~/.local/share/applications/speedscan.desktop
echo "✅ Tudo pronto e atualizado!"
