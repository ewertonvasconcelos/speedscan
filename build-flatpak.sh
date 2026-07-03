#!/bin/bash
set -e

echo "🚀 Build Flatpak SpeedScan..."

rm -rf build-dir

flatpak-builder --force-clean build-dir \
    speedscan.yml \
    --user \
    --install

echo "✅ Sucesso!"
echo "⌨️ Execute: flatpak run com.github.ewertonvasconcelos.speedscan"
