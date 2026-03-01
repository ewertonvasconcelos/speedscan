#!/bin/bash
# scripts/build-appimage.sh
set -e

# Criar diretório AppDir
mkdir -p AppDir/usr/bin
cp dist/SpeedScan AppDir/usr/bin/
cp assets/icon.png AppDir/icon.png

# Criar arquivo .desktop
cat > AppDir/speedscan.desktop <<EOF
[Desktop Entry]
Name=SpeedScan
Comment=Ferramenta de diagnóstico e otimização
Exec=SpeedScan
Icon=icon
Terminal=false
Type=Application
Categories=Utility;
EOF

# Baixar linuxdeploy
wget -c "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
chmod +x linuxdeploy-x86_64.AppImage

# Gerar AppImage
./linuxdeploy-x86_64.AppImage --appdir AppDir --output appimage

