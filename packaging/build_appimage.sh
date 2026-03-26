#!/bin/bash
# Build AppImage for SpeedScan

echo "🔨 Construindo AppImage..."

# Instalar linuxdeploy se não existir
if [ ! -f "linuxdeploy-x86_64.AppImage" ]; then
    wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
    chmod +x linuxdeploy-x86_64.AppImage
fi

# Criar AppDir
mkdir -p SpeedScan.AppDir/usr/bin
mkdir -p SpeedScan.AppDir/usr/lib
mkdir -p SpeedScan.AppDir/usr/share/applications
mkdir -p SpeedScan.AppDir/usr/share/icons/hicolor/256x256/apps

# Copiar executável PyInstaller
cp ../dist/SpeedScan-Linux SpeedScan.AppDir/usr/bin/
chmod +x SpeedScan.AppDir/usr/bin/SpeedScan-Linux

# Copiar bibliotecas necessárias
ldd ../dist/SpeedScan-Linux | grep "=> /" | awk '{print $3}' | xargs -I '{}' cp -v '{}' SpeedScan.AppDir/usr/lib/ 2>/dev/null || true

# Criar desktop file
cat > SpeedScan.AppDir/usr/share/applications/speedscan.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Name=SpeedScan
Comment=System monitoring tool
Exec=SpeedScan-Linux
Icon=speedscan
Categories=System;Monitor;
DESKTOP_EOF

# Copiar ícone (se existir)
cp ../assets/icon.png SpeedScan.AppDir/usr/share/icons/hicolor/256x256/apps/speedscan.png 2>/dev/null || \
wget -O SpeedScan.AppDir/usr/share/icons/hicolor/256x256/apps/speedscan.png https://raw.githubusercontent.com/windmillbuilder/SpeedScan/main/assets/icon.png 2>/dev/null || \
echo "⚠️ Ícone não encontrado"

# Criar AppRun
cat > SpeedScan.AppDir/AppRun << 'APPRUN_EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/SpeedScan-Linux"
APPRUN_EOF
chmod +x SpeedScan.AppDir/AppRun

# Construir AppImage
./linuxdeploy-x86_64.AppImage --appdir SpeedScan.AppDir --output appimage --desktop-file SpeedScan.AppDir/usr/share/applications/speedscan.desktop

# Mover para dist
mv SpeedScan*.AppImage ../dist/
echo "✅ AppImage criado em dist/"
echo "📦 Arquivo: $(ls ../dist/SpeedScan*.AppImage)"
