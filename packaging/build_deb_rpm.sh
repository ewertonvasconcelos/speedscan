#!/bin/bash
# Build DEB and RPM packages for SpeedScan

echo "🔨 Construindo DEB/RPM..."

# Instalar fpm
gem install fpm || echo "fpm já instalado"

# Criar estrutura do pacote
mkdir -p speedscan-deb/usr/bin
mkdir -p speedscan-deb/usr/share/applications
mkdir -p speedscan-deb/usr/share/icons/hicolor/256x256/apps
mkdir -p speedscan-deb/usr/lib/speedscan

# Copiar arquivos
cp -r /home/ewerton/speedscan/speedscan speedscan-deb/usr/lib/
cp /home/ewerton/speedscan/speedscan/launch.sh speedscan-deb/usr/bin/speedscan
chmod +x speedscan-deb/usr/bin/speedscan

# Criar desktop file
cat > speedscan-deb/usr/share/applications/speedscan.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Name=SpeedScan
Comment=System monitoring tool
Exec=/usr/bin/speedscan
Icon=speedscan
Categories=System;Monitor;
DESKTOP_EOF

# Copiar ícone
cp /home/ewerton/speedscan/speedscan/assets/icon.png speedscan-deb/usr/share/icons/hicolor/256x256/apps/speedscan.png 2>/dev/null || true

# Construir DEB
fpm -s dir -t deb \
    -n speedscan \
    -v 1.0.0 \
    --depends python3 \
    --depends python3-tk \
    --depends python3-pip \
    -C speedscan-deb \
    -p ../dist/speedscan_ARCH.deb \
    usr

# Construir RPM
fpm -s dir -t rpm \
    -n speedscan \
    -v 1.0.0 \
    --depends python3 \
    --depends python3-tkinter \
    -C speedscan-deb \
    -p ../dist/speedscan_ARCH.rpm \
    usr

echo "✅ Pacotes DEB/RPM criados em dist/"
