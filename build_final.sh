#!/bin/bash
set -e

cd /home/ewerton/speedscan/speedscan

echo "=== Limpando construções anteriores ==="
rm -rf SpeedScan.AppDir python314-appimage squashfs-root appimagetool-extract

echo "=== Verificando Python 3.14 AppImage ==="
if [ ! -f python3.14.0-cp314-cp314-manylinux2014_x86_64.AppImage ]; then
    echo "Baixando Python 3.14 AppImage..."
    wget https://github.com/niess/python-appimage/releases/download/python3.14/python3.14.0-cp314-cp314-manylinux2014_x86_64.AppImage
fi
chmod +x python3.14.0-*.AppImage

echo "=== Extraindo Python 3.14 AppImage ==="
./python3.14.0-*.AppImage --appimage-extract
mv squashfs-root python314-appimage

echo "=== Instalando dependências no Python extraído ==="
./python314-appimage/opt/python3.14/bin/python3.14 -m ensurepip
./python314-appimage/opt/python3.14/bin/python3.14 -m pip install customtkinter psutil matplotlib requests speedtest-cli pillow

echo "=== Criando estrutura do AppDir ==="
mkdir -p SpeedScan.AppDir/usr/bin
mkdir -p SpeedScan.AppDir/usr/lib
mkdir -p SpeedScan.AppDir/usr/share/speedscan
mkdir -p SpeedScan.AppDir/usr/share/tcltk

echo "=== Copiando Python AppImage ==="
cp python3.14.0-*.AppImage SpeedScan.AppDir/usr/bin/python

echo "=== Copiando Tcl/Tk do Python extraído ==="
cp -r python314-appimage/usr/share/tcltk/* SpeedScan.AppDir/usr/share/tcltk/
cp python314-appimage/usr/lib/libtcl8.6.so SpeedScan.AppDir/usr/lib/
cp python314-appimage/usr/lib/libtk8.6.so SpeedScan.AppDir/usr/lib/

echo "=== Copiando código do SpeedScan (recursivamente) ==="
cp -r core locale assets SpeedScan.AppDir/usr/share/speedscan/

# Verificação crucial: ai_proactive.py
if [ -f SpeedScan.AppDir/usr/share/speedscan/core/ai_proactive.py ]; then
    echo "✅ ai_proactive.py copiado com sucesso"
else
    echo "❌ ai_proactive.py não encontrado! Copiando manualmente..."
    cp core/ai_proactive.py SpeedScan.AppDir/usr/share/speedscan/core/
fi

echo "=== Criando AppRun ==="
cat > SpeedScan.AppDir/AppRun << 'INNER_EOF'
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PYTHONPATH="$HERE/usr/share/speedscan"
export LD_LIBRARY_PATH="$HERE/usr/lib:$LD_LIBRARY_PATH"
export TCL_LIBRARY="$HERE/usr/share/tcltk/tcl8.6"
export TK_LIBRARY="$HERE/usr/share/tcltk/tk8.6"
exec "$HERE/usr/bin/python" -m core.main
INNER_EOF
chmod +x SpeedScan.AppDir/AppRun

echo "=== Criando .desktop e ícone ==="
cat > SpeedScan.AppDir/speedscan.desktop << DESKTOP_EOF
[Desktop Entry]
Name=SpeedScan
Exec=speedscan
Icon=speedscan
Type=Application
Categories=System;
DESKTOP_EOF
cp assets/icon.png SpeedScan.AppDir/speedscan.png

echo "=== Preparando appimagetool ==="
if [ ! -d appimagetool-extract ]; then
    if [ ! -f appimagetool-x86_64.AppImage ]; then
        wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    fi
    chmod +x appimagetool-x86_64.AppImage
    ./appimagetool-x86_64.AppImage --appimage-extract
    mv squashfs-root appimagetool-extract
fi

echo "=== Gerando AppImage final ==="
cd ~
./appimagetool-extract/AppRun /home/ewerton/speedscan/speedscan/SpeedScan.AppDir

echo "✅ AppImage criado: ~/SpeedScan-x86_64.AppImage"
