#!/bin/bash

echo "--- Customizando Apps, Fontes e Removendo Bloatware ---"

# 1. Removendo Bloatware (LibreOffice e outros)
sudo eopkg rm libreoffice-common libreoffice-calc libreoffice-writer libreoffice-impress -y

# 2. Instalando Fontes (Google Fonts + Microsoft Fonts)
# O pacote 'google-fonts' no Solus traz as principais como Roboto, Open Sans, etc.
sudo eopkg it mscorefonts google-fonts -y

# Atualizando o cache de fontes do sistema para o OnlyOffice detectar tudo
sudo fc-cache -f -v

# 3. Instalando Apps Nativos
sudo eopkg it vlc vscode -y

# 4. Instalando Apps via Flatpak
flatpak install flathub com.google.Chrome -y
flatpak install flathub com.stremio.Stremio -y
flatpak install flathub org.onlyoffice.desktopeditors -y

# 5. Limpeza Final
sudo eopkg dc -y && sudo eopkg rmo -y

echo "--- Tudo pronto! Fontes do Google instaladas e sistema limpo. ---"