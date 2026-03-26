#!/bin/bash
set -e

echo "=== Iniciando construção do AppImage do SpeedScan ==="

# Vá para a pasta do projeto
cd /home/ewerton/speedscan/speedscan

# 1. Limpar construções anteriores
rm -rf SpeedScan.AppDir python314-appimage squashfs-root appimagetool-extract

# 2. Baixar Python 3.14 AppImage (se não existir)
if [ ! -f python3.14.0-cp314-cp314-manylinux2014_x86_64.AppImage ]; then
    echo "Baixando Python 3.14 AppImage..."
    wget -q https://github.com/niess/python-appimage/releases/download/python3.14/python3.14.0-cp314-cp314-manylinux2014_x86_64.AppImage
fi
chmod +x python3.14.0-*.AppImage

# 3. Extrair Python
echo "Extraindo Python 3.14..."
./python3.14.0-*.AppImage --appimage-extract
mv squashfs-root python314-appimage

# 4. Instalar dependências dentro do Python extraído
echo "Instalando dependências..."
./python314-appimage/opt/python3.14/bin/python3.14 -m ensurepip
./python314-appimage/opt/python3.14/bin/python3.14 -m pip install --no-cache-dir customtkinter psutil matplotlib requests speedtest-cli pillow

# 5. Criar estrutura do AppDir
mkdir -p SpeedScan.AppDir/usr/bin
mkdir -p SpeedScan.AppDir/usr/lib
mkdir -p SpeedScan.AppDir/usr/share/speedscan
mkdir -p SpeedScan.AppDir/usr/share/tcltk

# 6. Copiar o Python extraído (não o AppImage) para o AppDir
cp python314-appimage/opt/python3.14/bin/python3.14 SpeedScan.AppDir/usr/bin/python
chmod +x SpeedScan.AppDir/usr/bin/python

# 7. Copiar bibliotecas Tcl/Tk
cp python314-appimage/usr/lib/libtcl8.6.so SpeedScan.AppDir/usr/lib/
cp python314-appimage/usr/lib/libtk8.6.so SpeedScan.AppDir/usr/lib/
cp -r python314-appimage/usr/share/tcltk SpeedScan.AppDir/usr/share/

# 8. Copiar o código do SpeedScan (core, locale, assets)
cp -r core locale assets SpeedScan.AppDir/usr/share/speedscan/

# 9. Criar AppRun
cat > SpeedScan.AppDir/AppRun << 'EOF'
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PYTHONPATH="$HERE/usr/share/speedscan"
export LD_LIBRARY_PATH="$HERE/usr/lib:$LD_LIBRARY_PATH"
export TCL_LIBRARY="$HERE/usr/share/tcltk/tcl8.6"
export TK_LIBRARY="$HERE/usr/share/tcltk/tk8.6"
exec "$HERE/usr/bin/python" -m core.main
EOF
chmod +x SpeedScan.AppDir/AppRun

# 10. Criar arquivo .desktop e ícone
cat > SpeedScan.AppDir/speedscan.desktop << EOF
[Desktop Entry]
Name=SpeedScan
Exec=speedscan
Icon=speedscan
Type=Application
Categories=System;
EOF
cp assets/icon.png SpeedScan.AppDir/speedscan.png

# 11. Baixar e extrair appimagetool (se não tiver)
if [ ! -f appimagetool-x86_64.AppImage ]; then
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
fi
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage --appimage-extract
mv squashfs-root appimagetool-extract

# 12. Gerar AppImage final
echo "Gerando AppImage..."
cd ~
./appimagetool-extract/AppRun /home/ewerton/speedscan/speedscan/SpeedScan.AppDir

echo "✅ AppImage gerado com sucesso em ~/SpeedScan-x86_64.AppImage"
