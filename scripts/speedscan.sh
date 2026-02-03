#!/bin/bash

# Cores para o terminal
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # Sem cor

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}             SpeedScan                 ${NC}"
echo -e "${BLUE}=======================================${NC}"

# Detectando o Sistema Operacional
if [ -f /etc/solus-release ]; then
    echo "[*] Sistema detectado: Solus"
    sudo eopkg dc -y && sudo eopkg rmo -y
elif [ -f /etc/fedora-release ]; then
    echo "[*] Sistema detectado: Fedora"
    sudo dnf clean all -y
elif [ -f /etc/lsb-release ]; then
    echo "[*] Sistema detectado: Ubuntu/Derivado"
    sudo apt autoremove -y && sudo apt clean
fi

# Limpezas Universais (Caches de Apps e Logs)
echo "[*] Limpando caches de aplicativos e logs..."
rm -rf ~/.cache/google-chrome/*
rm -rf ~/.cache/thumbnails/*
sudo journalctl --vacuum-time=1d

# Atualização de ícones (Padrão Linux Desktop)
if command -v kbuildsycoca5 &> /dev/null; then
    kbuildsycoca5 --noincremental > /dev/null 2>&1
fi
update-desktop-database ~/.local/share/applications 2>/dev/null

echo -e "${GREEN}=======================================${NC}"
echo -e "      Otimização Concluída!            "
echo -e "${GREEN}=======================================${NC}"