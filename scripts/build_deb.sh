#!/bin/bash
# build_deb.sh - Gera o pacote .deb do SpeedScan

set -e  # interrompe em caso de erro

cd "$(dirname "$0")"

# Configurações
APP_NAME="speedscan"
VERSION="0.9.0"
ARCH="amd64"
MAINTAINER="Ewerton Vasconcelos <ewerton@consertop6.com>"
DESCRIPTION="Ferramenta de diagnóstico e otimização de sistemas"
ICON_PATH="icon.png"
EXECUTABLE="dist/$APP_NAME"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Iniciando build do pacote .deb ===${NC}"

# 1. Gerar executável com PyInstaller (se não existir)
if [ ! -f "$EXECUTABLE" ]; then
    echo "Executável não encontrado. Gerando com PyInstaller..."
    if ! command -v pyinstaller &> /dev/null; then
        echo "PyInstaller não encontrado. Instalando..."
        pip install pyinstaller
    fi
    pyinstaller --onefile \
                --windowed \
                --name "$APP_NAME" \
                --add-data "core:core" \
                --add-data "$ICON_PATH:." \
                --hidden-import customtkinter \
                --hidden-import PIL \
                --hidden-import psutil \
                --hidden-import platform \
                --hidden-import subprocess \
                --hidden-import threading \
                --hidden-import json \
                --hidden-import time \
                --hidden-import sys \
                --hidden-import re \
                --hidden-import datetime \
                core/speedscan_app.py
fi

if [ ! -f "$EXECUTABLE" ]; then
    echo -e "${RED}Erro: executável não foi gerado.${NC}"
    exit 1
fi

# 2. Criar estrutura do pacote .deb
DEB_DIR="build/$APP_NAME-$VERSION"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/48x48/apps"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/96x96/apps"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$DEB_DIR/usr/share/doc/$APP_NAME"

# 3. Copiar o executável
cp "$EXECUTABLE" "$DEB_DIR/usr/bin/$APP_NAME"
chmod 755 "$DEB_DIR/usr/bin/$APP_NAME"

# 4. Copiar o ícone (redimensionar para vários tamanhos - opcional)
if [ -f "$ICON_PATH" ]; then
    cp "$ICON_PATH" "$DEB_DIR/usr/share/icons/hicolor/48x48/apps/$APP_NAME.png"
    cp "$ICON_PATH" "$DEB_DIR/usr/share/icons/hicolor/96x96/apps/$APP_NAME.png"
    cp "$ICON_PATH" "$DEB_DIR/usr/share/icons/hicolor/128x128/apps/$APP_NAME.png"
else
    echo -e "${RED}Aviso: ícone não encontrado.${NC}"
fi

# 5. Criar arquivo .desktop
cat > "$DEB_DIR/usr/share/applications/$APP_NAME.desktop" << EOF
[Desktop Entry]
Name=SpeedScan
Comment=$DESCRIPTION
Exec=$APP_NAME
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Utility;System;
EOF

# 6. Criar arquivo de controle (control)
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 SpeedScan é uma ferramenta de diagnóstico e otimização de sistemas
 desenvolvida em Python com CustomTkinter. Oferece monitoramento em tempo
 real, otimização de desempenho, configuração de rede e diagnóstico de
 drivers.
EOF

# 7. Copiar documentação (opcional)
echo "Veja https://github.com/ewertonvasconcelos/speedscan para mais informações." > "$DEB_DIR/usr/share/doc/$APP_NAME/README"
gzip -9 "$DEB_DIR/usr/share/doc/$APP_NAME/README"

# 8. Construir o pacote .deb
DEB_FILE="${APP_NAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --build "$DEB_DIR" "$DEB_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Pacote gerado com sucesso: $DEB_FILE${NC}"
else
    echo -e "${RED}Falha ao gerar pacote.${NC}"
    exit 1
fi

# 9. Limpeza (opcional)
rm -rf "$DEB_DIR"

echo -e "${GREEN}=== Build concluído! ===${NC}"
