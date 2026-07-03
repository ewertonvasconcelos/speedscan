#!/bin/bash
set -e

echo "⚡ SpeedScan Automated Installer v1.0"
echo "======================================"

# Check if running in terminal or script
if [ -t 0 ]; then
    echo "Script mode enabled..."
else
    echo "Running non-interactively..."
fi

# Detect system package manager
detect_pkg_mgr() {
    if command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v apt &>/dev/null; then
        echo "apt"
    else
        echo "unknown"
    fi
}

PKG_MGR=$(detect_pkg_mgr)
echo "[✓] Detected: $PKG_MGR"

# Install distrobox if missing
if ! command -v distrobox &>/dev/null; then
    echo "[!] Installing distrobox..."
    case "$PKG_MGR" in
        dnf) sudo dnf install -y distrobox;;
        apt) sudo apt install -y distrobox;;
        *) echo "Manual distrobox installation required"; exit 1;;
    esac
else
    echo "[✓] Distrob ox already installed"
fi

# Create project directory
mkdir -p ~/projects/speedscan
cd ~/projects

# Clone or update repo
if [ ! -d speedscan/.git ]; then
    echo "[1/5] Cloning repository..."
    git clone https://github.com/ewertonvasconcelos/speedscan.git speedscan || true
else
    echo "[1/5] Updating existing repository..."
    cd speedscan && git pull origin main
fi

# Create runtime container
if distrobox list | grep -q speedscan-runtime; then
    echo "[2/5] Using existing speedscan-runtime"
else
    echo "[2/5] Creating Fedora runtime container..."
    distrobox create \
        --name speedscan-runtime \
        --image fedora:39 \
        --volume ~/projects:/home/user/projects:rw \
        --additional-packages "python3-pip python3-tkinter git gcc gtk3-devel cairo pango mesa-libGL" || true
fi

# Install dependencies inside container
echo "[3/5] Installing Python dependencies..."
distrobox enter speedscan-runtime -- bash -c "cd /home/user/projects/speedscan && python3 -m ensurepip --upgrade && pip install customtkinter matplotlib psutil requests numpy --quiet" || true

# Configure launcher
echo "[4/5] Setting up CLI wrapper..."
mkdir -p ~/.local/bin
cat > ~/.local/bin/speedscan << 'CLIEOF'
#!/bin/bash
cd ~ || return
PROJECT_DIR="\${1:-\$HOME/projects/speedscan}"
exec /usr/bin/distrobox enter speedscan-runtime -- python3 "\$PROJECT_DIR/core/main.py" "\${@:2}"
CLIEOF
chmod +x ~/.local/bin/speedscan

# Desktop integration
echo "[5/5] Integrating to desktop environment..."
mkdir -p ~/.local/share/applications ~/.local/share/icons/hicolor/256x256/apps
cp ~/projects/speedscan/assets/icon.png ~/.local/share/icons/hicolor/256x256/apps/speedscan.png 2>/dev/null || true

cat > ~/.local/share/applications/com.github.ewertonvasconcelos.speedscan.desktop << DESKEOF
[Desktop Entry]
Type=Application
Name=SpeedScan
Comment=Modern system diagnostic tool
Exec=/usr/local/bin/speedscan
Icon=speedscan
Terminal=false
Categories=System;Performance;Utility;
StartupNotify=true
DESKEOF

echo ""
echo "✅ Installation Complete!"
echo ""
echo "Quick Start Guide:"
echo "  Command Line: speedscan"
echo "  Desktop Menu: Search 'SpeedScan'"
echo "  Development: Edit ~/projects/speedscan/"
echo "  Updates: cd ~/projects/speedscan && git pull"
echo ""
echo "Uninstall: rm ~/.local/bin/speedscan ~/.local/share/applications/*.desktop && distrobox rm speedscan-runtime"
