#!/bin/bash
# build_flatpak.sh - Gera o pacote .flatpak do SpeedScan (com redimensionamento de ícone)

set -e

cd "$(dirname "$0")"

APP_ID="org.speedscan.SpeedScan"
VERSION="0.9.0"
ICON_SOURCE="icon.png"
ICON_RESIZED="flatpak/icon_128.png"

echo "=== Iniciando build do Flatpak ==="

# Verifica se o executável existe
if [ ! -f "dist/speedscan" ]; then
    echo "Erro: executável não encontrado em dist/speedscan. Execute primeiro o PyInstaller."
    exit 1
fi

# Verifica se o ícone original existe
if [ ! -f "$ICON_SOURCE" ]; then
    echo "Erro: ícone $ICON_SOURCE não encontrado."
    exit 1
fi

# Cria o diretório flatpak se não existir
mkdir -p flatpak

# Redimensiona o ícone para 128x128 usando Python (Pillow)
echo "Redimensionando ícone para 128x128..."
python3 << EOF
from PIL import Image
img = Image.open("$ICON_SOURCE")
img.thumbnail((128, 128), Image.Resampling.LANCZOS)
img.save("$ICON_RESIZED")
EOF

# Verifica se o ícone redimensionado foi criado
if [ ! -f "$ICON_RESIZED" ]; then
    echo "Erro: falha ao redimensionar o ícone."
    exit 1
fi

# Verifica as dimensões do ícone redimensionado
DIMENSIONS=$(python3 -c "from PIL import Image; img = Image.open('$ICON_RESIZED'); print(img.size)")
echo "Dimensões do ícone redimensionado: $DIMENSIONS"
if [[ "$DIMENSIONS" != "(128, 128)" ]]; then
    echo "Erro: o ícone redimensionado não tem 128x128 pixels. Tem $DIMENSIONS."
    exit 1
fi

# Limpa o cache do flatpak-builder
echo "Limpando cache do flatpak-builder..."
rm -rf ~/.cache/flatpak-builder

# Verifica se o flatpak está configurado para usuário
flatpak --user remotes | grep -q flathub || flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Constrói o flatpak
cd flatpak

# Copia o ícone redimensionado para o local esperado pelo manifesto (nome simples)
cp "$ICON_RESIZED" icon.png

# Garante que o manifesto existe
if [ ! -f "$APP_ID.json" ]; then
    echo "Erro: manifesto $APP_ID.json não encontrado em flatpak/"
    exit 1
fi

# Constrói com força total (--disable-cache evita uso de cache)
flatpak-builder --user --force-clean --disable-cache build-dir "$APP_ID.json"

# Exporta para um repositório local
flatpak build-export repo build-dir

# Cria o bundle .flatpak
flatpak build-bundle repo "$APP_ID.flatpak" "$APP_ID"

# Move o bundle para o diretório principal
mv "$APP_ID.flatpak" ../

cd ..

echo "Pacote Flatpak gerado com sucesso: $APP_ID.flatpak"
echo "=== Build concluído! ==="
