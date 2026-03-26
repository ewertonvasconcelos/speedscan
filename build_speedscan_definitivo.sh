#!/bin/bash
set -e

echo "=== Construindo AppImage do SpeedScan ==="

cd /home/ewerton/speedscan/speedscan

# Limpar construções anteriores
rm -rf SpeedScan.AppDir python314-appimage squashfs-root appimagetool-extract

# Baixar Python 3.14 AppImage (se não existir)
if [ ! -f python3.14.0-cp314-cp314-manylinux2014_x86_64.AppImage ]; then
    wget https://github.com/niess/python-appimage/releases/download/python3.14/python3.14.0-cp314-cp314-manylinux2014_x86_64.AppImage
fi
chmod +x python3.14.0-*.AppImage

# Extrair Python
./python3.14.0-*.AppImage --appimage-extract
mv squashfs-root python314-appimage

# Instalar dependências
./python314-appimage/opt/python3.14/bin/python3.14 -m ensurepip
./python314-appimage/opt/python3.14/bin/python3.14 -m pip install customtkinter psutil matplotlib requests speedtest-cli pillow

# Criar AppDir
mkdir -p SpeedScan.AppDir/usr/bin
mkdir -p SpeedScan.AppDir/usr/lib
mkdir -p SpeedScan.AppDir/usr/share/speedscan
mkdir -p SpeedScan.AppDir/usr/share/tcltk

# Copiar Python (real)
cp python314-appimage/opt/python3.14/bin/python3.14 SpeedScan.AppDir/usr/bin/python
chmod +x SpeedScan.AppDir/usr/bin/python

# Copiar Tcl/Tk
cp python314-appimage/usr/lib/libtcl8.6.so SpeedScan.AppDir/usr/lib/
cp python314-appimage/usr/lib/libtk8.6.so SpeedScan.AppDir/usr/lib/
cp -r python314-appimage/usr/share/tcltk SpeedScan.AppDir/usr/share/

# Copiar código do SpeedScan
cp -r core locale assets SpeedScan.AppDir/usr/share/speedscan/

# Criar AppRun
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

# Criar .desktop e ícone
cat > SpeedScan.AppDir/speedscan.desktop << EOF
[Desktop Entry]
Name=SpeedScan
Exec=speedscan
Icon=speedscan
Type=Application
Categories=System;
EOF
cp assets/icon.png SpeedScan.AppDir/speedscan.png

# Baixar appimagetool (se não existir)
if [ ! -f appimagetool-x86_64.AppImage ]; then
    wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
fi
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage --appimage-extract
mv squashfs-root appimagetool-extract

# Gerar AppImage
cd ~
./appimagetool-extract/AppRun /home/ewerton/speedscan/speedscan/SpeedScan.AppDir

echo "✅ AppImage gerado: ~/SpeedScan-x86_64.AppImage"
