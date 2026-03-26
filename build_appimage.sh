#!/bin/bash
set -e

cd /home/ewerton/speedscan/speedscan

echo "=== 1. Limpando ==="
rm -rf SpeedScan.AppDir python314-appimage squashfs-root appimagetool-extract

echo "=== 2. Python 3.14 AppImage ==="
if [ ! -f python3.14.0-cp314-cp314-manylinux2014_x86_64.AppImage ]; then
    wget https://github.com/niess/python-appimage/releases/download/python3.14/python3.14.0-cp314-cp314-manylinux2014_x86_64.AppImage
fi
chmod +x python3.14.0-*.AppImage

echo "=== 3. Extraindo Python ==="
./python3.14.0-*.AppImage --appimage-extract
mv squashfs-root python314-appimage

echo "=== 4. Instalando dependências ==="
./python314-appimage/opt/python3.14/bin/python3.14 -m ensurepip
./python314-appimage/opt/python3.14/bin/python3.14 -m pip install --no-cache-dir customtkinter psutil matplotlib requests speedtest-cli pillow

echo "=== 5. Criando AppDir ==="
mkdir -p SpeedScan.AppDir/usr/bin
mkdir -p SpeedScan.AppDir/opt/python3.14
mkdir -p SpeedScan.AppDir/usr/lib
mkdir -p SpeedScan.AppDir/usr/share/speedscan
mkdir -p SpeedScan.AppDir/usr/share/tcltk

echo "=== 6. Copiando Python completo ==="
cp python314-appimage/opt/python3.14/bin/python3.14 SpeedScan.AppDir/usr/bin/python
chmod +x SpeedScan.AppDir/usr/bin/python
cp -r python314-appimage/opt/python3.14/lib SpeedScan.AppDir/opt/python3.14/

echo "=== 7. Copiando Tcl/Tk ==="
cp python314-appimage/usr/lib/libtcl8.6.so SpeedScan.AppDir/usr/lib/
cp python314-appimage/usr/lib/libtk8.6.so SpeedScan.AppDir/usr/lib/
cp -r python314-appimage/usr/share/tcltk SpeedScan.AppDir/usr/share/

echo "=== 8. Copiando código SpeedScan ==="
cp -r core locale assets SpeedScan.AppDir/usr/share/speedscan/

echo "=== 9. Criando AppRun ==="
cat > SpeedScan.AppDir/AppRun << 'INNER_EOF'
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PYTHONPATH="$HERE/usr/share/speedscan"
export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/opt/python3.14/lib:$LD_LIBRARY_PATH"
export TCL_LIBRARY="$HERE/usr/share/tcltk/tcl8.6"
export TK_LIBRARY="$HERE/usr/share/tcltk/tk8.6"
exec "$HERE/usr/bin/python" -m core.main
INNER_EOF
chmod +x SpeedScan.AppDir/AppRun

echo "=== 10. .desktop e ícone ==="
cat > SpeedScan.AppDir/speedscan.desktop << DESKTOP_EOF
[Desktop Entry]
Name=SpeedScan
Exec=speedscan
Icon=speedscan
Type=Application
Categories=System;
DESKTOP_EOF
if [ -f assets/icon.png ]; then
    cp assets/icon.png SpeedScan.AppDir/speedscan.png
fi

echo "=== 11. Baixando appimagetool ==="
if [ ! -f appimagetool-x86_64.AppImage ]; then
    wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
fi
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage --appimage-extract
mv squashfs-root appimagetool-extract

echo "=== 12. Gerando AppImage ==="
cd ~
./appimagetool-extract/AppRun /home/ewerton/speedscan/speedscan/SpeedScan.AppDir

echo "=== AppImage gerado: ~/SpeedScan-x86_64.AppImage ==="
