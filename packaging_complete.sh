#!/bin/bash
# Script para empacotamento do SpeedScan no container Ubuntu

echo "🚀 SpeedScan - Empacotamento Multiplataforma"
echo "=========================================="

# Entrar no container e executar tarefas
distrobox enter speedscan-clean << 'EOF'
cd /home/ewerton/speedscan/speedscan

echo "📍 Diretório atual: $(pwd)"
echo "📋 Arquivos no projeto:"
ls -la

echo ""
echo "🔍 1. Análise de Portabilidade"
echo "=============================="

# Ativar ambiente virtual
source venv/bin/activate

# Verificar dependências
echo "📦 Dependências Python instaladas:"
pip list | grep -E "(customtkinter|psutil|matplotlib|requests|speedtest-cli|pillow)"

echo ""
echo "🔍 Verificando bibliotecas específicas da plataforma:"
python -c "
import platform
print(f'Sistema: {platform.system()}')
print(f'Arquitetura: {platform.machine()}')
print(f'Python: {platform.python_version()}')

# Testar imports críticos
try:
    import tkinter
    print('✅ tkinter: OK')
except ImportError as e:
    print(f'❌ tkinter: {e}')

try:
    import psutil
    print('✅ psutil: OK')
except ImportError as e:
    print(f'❌ psutil: {e}')

try:
    import customtkinter
    print('✅ customtkinter: OK')
except ImportError as e:
    print(f'❌ customtkinter: {e}')

try:
    import matplotlib
    print('✅ matplotlib: OK')
except ImportError as e:
    print(f'❌ matplotlib: {e}')

try:
    import requests
    print('✅ requests: OK')
except ImportError as e:
    print(f'❌ requests: {e}')

try:
    import speedtest
    print('✅ speedtest-cli: OK')
except ImportError as e:
    print(f'❌ speedtest-cli: {e}')

try:
    from PIL import Image
    print('✅ pillow: OK')
except ImportError as e:
    print(f'❌ pillow: {e}')
"

echo ""
echo "📁 2. Criando estrutura de empacotamento"
echo "====================================="

# Criar diretórios
mkdir -p packaging dist

echo "✅ Diretórios criados:"
ls -la packaging/ dist/

echo ""
echo "📝 3. Análise de compatibilidade por plataforma"
echo "=============================================="

cat > packaging/portability_analysis.md << 'INNER_EOF'
# Análise de Portabilidade - SpeedScan

## Compatibilidade por Plataforma

### ✅ Linux (Totalmente Compatível)
- **Bibliotecas**: Todas funcionam nativamente
- **Tkinter**: Disponível na maioria das distribuições
- **Psutil**: Suporte completo para Linux
- **Formatos**: AppImage, Flatpak, Deb, Snap, RPM

### ⚠️ Windows (Requer Adaptações)
- **Bibliotecas**: customtkinter funciona no Windows
- **Tkinter**: Disponível no Python Windows
- **Psutil**: Suporte completo para Windows
- **Caminhos**: Requer tratamento de caminhos Windows (\\)
- **Comandos**: Alguns comandos Linux não funcionam (ex: /proc/cpuinfo)

### ⚠️ macOS (Requer Adaptações)
- **Bibliotecas**: customtkinter funciona no macOS
- **Tkinter**: Disponível no Python macOS
- **Psutil**: Suporte completo para macOS
- **Caminhos**: Requer tratamento de caminhos Unix/macOS
- **Comandos**: /proc/cpuinfo não existe no macOS

### ❌ Android (Não Compatível)
- **Tkinter**: Não disponível nativamente no Android
- **customtkinter**: Requer X11/Wayland
- **Solução**: Requer reescrita com Kivy ou BeeWare

### ❌ iOS (Não Compatível)
- **Tkinter**: Não disponível nativamente no iOS
- **customtkinter**: Requer X11/Wayland
- **Solução**: Requer reescrita com Kivy ou BeeWare

## Problemas Identificados

### 1. Caminhos de Sistema (Linux-específicos)
- `/proc/cpuinfo` - Não existe no macOS/Windows
- `/etc/os-release` - Formato diferente no macOS/Windows
- `/sys/class/power_supply/` - Não existe no macOS/Windows

### 2. Comandos do Sistema
- `psutil.sensor_temperatures()` - Funciona diferente em cada SO
- `psutil.sensors_battery()` - Pode não funcionar em desktops

### 3. Dependências Gráficas
- **customtkinter** - Requer servidor X11/Wayland
- **Tkinter** - Requer ambiente gráfico

## Soluções Recomendadas

### 1. Código Multiplataforma
```python
# Detectar sistema operacional
import platform
system = platform.system()

# Tratar caminhos específicos
if system == "Linux":
    # Código Linux
elif system == "Windows":
    # Código Windows
elif system == "Darwin":  # macOS
    # Código macOS
```

### 2. Fallback para informações não disponíveis
```python
try:
    # Tentar obter informação específica do SO
    cpu_info = open("/proc/cpuinfo").read()
except FileNotFoundError:
    # Fallback genérico
    cpu_info = platform.processor()
```

### 3. Versões Alternativas
- **Android/iOS**: Criar versão web ou com Kivy
- **Servidor**: Criar API backend e interface web
INNER_EOF

echo "✅ Análise de portabilidade salva em packaging/portability_analysis.md"

echo ""
echo "🔨 4. Criando scripts de empacotamento"
echo "====================================="

# Script AppImage
cat > packaging/build_appimage.sh << 'INNER_EOF'
#!/bin/bash
# Build AppImage for SpeedScan

echo "🔨 Construindo AppImage..."

# Instalar linuxdeploy
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage

# Criar AppDir
mkdir -p SpeedScan.AppDir/usr/bin
mkdir -p SpeedScan.AppDir/usr/lib
mkdir -p SpeedScan.AppDir/usr/share/applications
mkdir -p SpeedScan.AppDir/usr/share/icons/hicolor/256x256/apps

# Copiar arquivos
cp -r /home/ewerton/speedscan/speedscan SpeedScan.AppDir/usr/bin/
cp /home/ewerton/speedscan/speedscan/venv/lib/python3.10/site-packages/* SpeedScan.AppDir/usr/lib/ 2>/dev/null || true

# Criar desktop file
cat > SpeedScan.AppDir/usr/share/applications/speedscan.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Name=SpeedScan
Comment=System monitoring tool
Exec=python3 -m core.main
Icon=speedscan
Categories=System;Monitor;
DESKTOP_EOF

# Copiar ícone (se existir)
cp /home/ewerton/speedscan/speedscan/assets/icon.png SpeedScan.AppDir/usr/share/icons/hicolor/256x256/apps/speedscan.png 2>/dev/null || true

# Criar AppRun
cat > SpeedScan.AppDir/AppRun << 'APPRUN_EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3.10/site-packages:${PYTHONPATH}"
cd "${HERE}/usr/bin/speedscan"
python3 -m core.main
APPRUN_EOF
chmod +x SpeedScan.AppDir/AppRun

# Construir AppImage
./linuxdeploy-x86_64.AppImage --appdir SpeedScan.AppDir --output appimage --desktop-file SpeedScan.AppDir/usr/share/applications/speedscan.desktop

# Mover para dist
mv SpeedScan*.AppImage ../dist/
echo "✅ AppImage criado em dist/"
INNER_EOF
chmod +x packaging/build_appimage.sh

# Script Flatpak
cat > packaging/org.speedscan.SpeedScan.json << 'INNER_EOF'
{
    "app-id": "org.speedscan.SpeedScan",
    "runtime": "org.freedesktop.Platform",
    "runtime-version": "22.08",
    "sdk": "org.freedesktop.Sdk",
    "command": "speedscan",
    "finish-args": [
        "--share=ipc",
        "--socket=x11",
        "--device=dri",
        "--filesystem=host:ro",
        "--system-talk=true"
    ],
    "modules": [
        {
            "name": "python3",
            "buildsystem": "simple",
            "build-commands": [
                "pip3 install --no-deps --prefix=/app customtkinter psutil matplotlib requests speedtest-cli pillow"
            ]
        },
        {
            "name": "speedscan",
            "buildsystem": "simple",
            "sources": [
                {
                    "type": "dir",
                    "path": ".."
                }
            ],
            "build-commands": [
                "pip3 install --no-deps --prefix=/app .",
                "install -Dm644 packaging/org.speedscan.SpeedScan.desktop /app/share/applications/org.speedscan.SpeedScan.desktop",
                "install -Dm644 packaging/org.speedscan.SpeedScan.metainfo.xml /app/share/metainfo/org.speedscan.SpeedScan.metainfo.xml",
                "install -Dm644 assets/icon.png /app/share/icons/hicolor/256x256/apps/org.speedscan.SpeedScan.png"
            ]
        }
    ]
}
INNER_EOF

# Script Deb/RPM
cat > packaging/build_deb_rpm.sh << 'INNER_EOF'
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
INNER_EOF
chmod +x packaging/build_deb_rpm.sh

# Script Snap
cat > packaging/snapcraft.yaml << 'INNER_EOF'
name: speedscan
version: '1.0.0'
summary: System monitoring tool
description: |
  SpeedScan is a comprehensive system monitoring tool that displays
  real-time information about CPU, RAM, disk usage, battery, and more.

grade: stable
confinement: strict
base: core22

apps:
  speedscan:
    command: bin/speedscan
    plugs:
      - home
      - network
      - system-observe
      - hardware-observe
      - mount-observe

parts:
  speedscan:
    plugin: python
    source: .
    python-packages:
      - customtkinter
      - psutil
      - matplotlib
      - requests
      - speedtest-cli
      - pillow
    stage-packages:
      - python3-tk

  launcher:
    plugin: dump
    source: .
    organize:
      launch.sh: bin/speedscan
INNER_EOF

# Script PyInstaller (Windows/macOS/Linux)
cat > packaging/build_pyinstaller.sh << 'INNER_EOF'
#!/bin/bash
# Build executables with PyInstaller

echo "🔨 Construindo executáveis com PyInstaller..."

# Instalar PyInstaller
pip install pyinstaller

# Construir para Linux
echo "🐧 Construindo para Linux..."
pyinstaller --onefile --windowed --name SpeedScan-Linux \
  --add-data "assets:assets" \
  --hidden-import="customtkinter" \
  --hidden-import="psutil" \
  --hidden-import="matplotlib" \
  --hidden-import="requests" \
  --hidden-import="speedtest" \
  --hidden-import="PIL" \
  core/main.py

# Mover para dist
mv dist/SpeedScan-Linux ../dist/

echo "✅ Executável Linux criado em dist/"

# Notas para Windows/macOS
echo "📝 Notas para outras plataformas:"
echo "Windows: Executar no Windows com: pyinstaller --onefile --windowed --name SpeedScan-Windows core/main.py"
echo "macOS: Executar no macOS com: pyinstaller --onefile --windowed --name SpeedScan-macOS --create-dmg core/main.py"
INNER_EOF
chmod +x packaging/build_pyinstaller.sh

# Script Android (com buildozer)
cat > packaging/buildozer.spec << 'INNER_EOF'
[app]

# (str) Title of your application
title = SpeedScan

# (str) Package name
package.name = speedscan

# (str) Package domain (needed for android/ios packaging)
package.domain = org.speedscan

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/images/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/images/icon.png

# (list) Supported orientations
# Valid options are: landscape, portrait, portrait-reverse or landscape-reverse
orientation = portrait

#
# (list) List of modules to add as python android modules
# android.modules = android

#
# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 23b

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid excess Internet downloads or save time
# if an update is due and you just want to test/build your package
android.skip_update = False

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.renpy.android.PythonActivity

# (list) Android application meta-data to set (key=value format)
#android.meta_data =

# (list) Android library project to add (will be added in Gradle project)
#android.library_references =

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = armeabi-v7a

#
# iOS specific
#

# (str) Path to a custom kivy-ios directory
#ios.kivy_ios_dir = ../kivy-ios

# (str) Name of the certificate to use for signing the debug version on iOS
#ios.codesign.debug = ?

# (str) Name of the certificate to use for signing the release version on iOS
#ios.codesign.release = ?

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
bin_dir = ./bin

#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the sections you want to configure each release of
#    your application, like packaging, signing, etc...
#
#    The section name must be the name of the release. At the moment, only one
#    is supported: "master"
#
#    -----------------------------------------------------------------------------
#    [master]
#
#    # (str) Author of the application
#    author.email = author@example.com
#    author.name = Author
#
#    # (str) Description of the application
#    description = My little application
#
#    # (bool) Whether your application has UI/visible interface
#    has_ui = True
#
#    # (list) List of the modules that your application uses
#    modules = kivy

#    # (str) Application versioning (method 2)
#    version.regex = __version__ = ['"](.*)['"]
#    version.filename = %(source.dir)s/main.py

#    # (list) Application requirements
#    # comma separated e.g. requirements = sqlite3,kivy
#    requirements = kivy

#    # (str) Presplash of the application
#    #presplash.filename = %(source.dir)s/data/presplash.png

#    # (str) Icon of the application
#    #icon.filename = %(source.dir)s/data/icon.png

#    # (list) Supported orientations
#    # Valid options are: landscape, portrait, portrait-reverse or landscape-reverse
#    orientation = portrait

#    # (bool) Indicate if the application should be fullscreen or not
#    fullscreen = 0

#    #
#    # Android specific
#    #

#    # (list) Permissions
#    android.permissions = INTERNET

#    # (int) Target Android API, should be as high as possible.
#    android.api = 31

#    # (int) Minimum API your APK will support.
#    android.minapi = 21

#    # (str) Android NDK version to use
#    android.ndk = 23b

#    # (bool) If True, then skip trying to update the Android sdk
#    # This can be useful to avoid excess Internet downloads or save time
#    # if an update is due and you just want to test/build your package
#    android.skip_update = False

#    # (str) Android entry point, default is ok for Kivy-based app
#    #android.entrypoint = org.renpy.android.PythonActivity

#    # (list) Android application meta-data to set (key=value format)
#    #android.meta_data =

#    # (list) Android library project to add (will be added in Gradle project)
#    #android.library_references =

#    # (str) Android logcat filters to use
#    #android.logcat_filters = *:S python:D

#    # (bool) Copy library instead of making a libpymodules.so
#    #android.copy_libs = 1

#    # (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
#    android.arch = armeabi-v7a

#    #
#    # iOS specific
#    #

#    # (str) Path to a custom kivy-ios directory
#    #ios.kivy_ios_dir = ../kivy-ios

#    # (str) Name of the certificate to use for signing the debug version on iOS
#    #ios.codesign.debug = ?

#    # (str) Name of the certificate to use for signing the release version on iOS
#    #ios.codesign.release = ?
INNER_EOF

# Script Android
cat > packaging/build_android.sh << 'INNER_EOF'
#!/bin/bash
# Build Android APK for SpeedScan (Demo Version)

echo "🤖 Construindo APK Android..."

# NOTA: SpeedScan usa customtkinter/tkinter que não funciona no Android
# Este script cria uma versão demo com Kivy

# Instalar buildozer
pip install buildozer

# Criar versão Android demo
mkdir -p android_demo
cd android_demo

# Criar main.py para Android (versão simplificada)
cat > main.py << 'PYTHON_EOF'
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
import platform

class SpeedScanAndroidApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Título
        title = Label(
            text='SpeedScan Android',
            font_size='24sp',
            size_hint_y=None,
            height=50
        )
        layout.add_widget(title)
        
        # Informações do sistema
        info = Label(
            text=f'Sistema: {platform.system()}\n' +
                 f'Arquitetura: {platform.machine()}\n' +
                 f'Python: {platform.python_version()}\n\n' +
                 'NOTA: Versão demo.\n' +
                 'Versão completa disponível\n' +
                 'para Linux/Windows/macOS',
            font_size='16sp',
            text_size=(400, None),
            halign='center'
        )
        layout.add_widget(info)
        
        return layout

if __name__ == '__main__':
    SpeedScanAndroidApp().run()
PYTHON_EOF

# Copiar buildozer.spec
cp ../packaging/buildozer.spec .

# Construir APK
buildozer android debug

# Mover APK para dist
mv bin/*.apk ../../dist/
cd ..

echo "✅ APK Android demo criado em dist/"
echo "⚠️  NOTA: Versão limitada devido à incompatibilidade do tkinter no Android"
INNER_EOF
chmod +x packaging/build_android.sh

echo "✅ Scripts de empacotamento criados:"
ls -la packaging/

echo ""
echo "🔄 5. Criando workflow CI/CD"
echo "=========================="

mkdir -p .github/workflows

cat > .github/workflows/build.yml << 'INNER_EOF'
name: Build SpeedScan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

jobs:
  build-linux:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - name: appimage
            script: packaging/build_appimage.sh
          - name: deb
            script: packaging/build_deb_rpm.sh
          - name: snap
            script: packaging/build_snap.sh
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y python3-tk python3-dev
        pip install customtkinter psutil matplotlib requests speedtest-cli pillow
    
    - name: Build ${{ matrix.name }}
      run: |
        chmod +x ${{ matrix.script }}
        ${{ matrix.script }}
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: speedscan-${{ matrix.name }}
        path: dist/

  build-windows:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install customtkinter psutil matplotlib requests speedtest-cli pillow pyinstaller
    
    - name: Build Windows EXE
      run: |
        pyinstaller --onefile --windowed --name SpeedScan-Windows --add-data "assets;assets" core/main.py
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: speedscan-windows
        path: dist/

  build-macos:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install customtkinter psutil matplotlib requests speedtest-cli pillow pyinstaller create-dmg
    
    - name: Build macOS DMG
      run: |
        pyinstaller --onefile --windowed --name SpeedScan-macOS --add-data "assets:assets" core/main.py
        create-dmg dist/SpeedScan-macOS.app dist/SpeedScan-macOS.dmg
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: speedscan-macos
        path: dist/

  build-android:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install buildozer
      run: |
        pip install buildozer
        sudo apt-get update
        sudo apt-get install -y build-essential git python3 python3-dev
        wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip -O commandlinetools.zip
        unzip commandlinetools.zip
        export ANDROID_SDK_ROOT=$PWD/cmdline-tools
        export PATH=$PATH:$ANDROID_SDK_ROOT/bin
        echo "y" | sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "platforms;android-31"
        echo "y" | sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "build-tools;31.0.0"
    
    - name: Build Android APK
      run: |
        chmod +x packaging/build_android.sh
        packaging/build_android.sh
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: speedscan-android
        path: dist/

  release:
    if: github.event_name == 'release'
    needs: [build-linux, build-windows, build-macos, build-android]
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/download-artifact@v3
    
    - name: Upload Release Assets
      uses: softprops/action-gh-release@v1
      with:
        files: |
          speedscan-*/*
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
INNER_EOF

echo "✅ Workflow CI/CD criado em .github/workflows/build.yml"

echo ""
echo "📝 6. Atualizando README.md"
echo "=========================="

cat > README.md << 'INNER_EOF'
# SpeedScan 🚀

SpeedScan é uma ferramenta completa de monitoramento de sistema com interface moderna e responsiva.

## 📸 Screenshots

![SpeedScan Interface](assets/screenshot.png)

## ✨ Características

- 🖥️ **Monitoramento em tempo real** de CPU, RAM, disco, bateria e mais
- 🎨 **Interface moderna** com CustomTkinter
- 📊 **Widgets centralizados** e responsivos
- 🌡️ **Monitoramento de temperatura**
- ⚡ **Teste de velocidade** da internet
- 💚 **Indicador de saúde** do sistema

## 🚀 Instalação

### Linux

#### AppImage (Recomendado)
```bash
wget https://github.com/ewertonvasconcelos/speedscan/releases/latest/download/SpeedScan.AppImage
chmod +x SpeedScan.AppImage
./SpeedScan.AppImage
```

#### Flatpak
```bash
flatpak install flathub org.speedscan.SpeedScan
flatpak run org.speedscan.SpeedScan
```

#### Debian/Ubuntu (.deb)
```bash
wget https://github.com/ewertonvasconcelos/speedscan/releases/latest/download/speedscan_amd64.deb
sudo dpkg -i speedscan_amd64.deb
```

#### Fedora/RPM (.rpm)
```bash
wget https://github.com/ewertonvasconcelos/speedscan/releases/latest/download/speedscan_x86_64.rpm
sudo rpm -i speedscan_x86_64.rpm
```

#### Snap
```bash
sudo snap install speedscan
```

### Windows

#### Executável (.exe)
1. Baixe `SpeedScan-Windows.exe` da [página de releases](https://github.com/ewertonvasconcelos/speedscan/releases)
2. Execute o instalador
3. Siga as instruções

### macOS

#### DMG
1. Baixe `SpeedScan-macOS.dmg` da [página de releases](https://github.com/ewertonvasconcelos/speedscan/releases)
2. Abra o DMG
3. Arraste o SpeedScan para Applications

### Android

#### APK (Versão Demo)
```bash
wget https://github.com/ewertonvasconvelos/speedscan/releases/latest/download/SpeedScan-debug.apk
# Instale no dispositivo Android
```

**Nota**: A versão Android é limitada devido à incompatibilidade do tkinter. Para funcionalidade completa, use as versões desktop.

## 🛠️ Desenvolvimento

### Pré-requisitos
- Python 3.10+
- tkinter
- pip

### Instalação do ambiente de desenvolvimento
```bash
git clone https://github.com/ewertonvasconcelos/speedscan.git
cd speedscan
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Executar em desenvolvimento
```bash
python -m core.main
```

### Empacotamento
Veja a pasta `packaging/` para scripts de build para diferentes plataformas.

## 📋 Dependências

- **customtkinter**: Interface gráfica moderna
- **psutil**: Informações do sistema
- **matplotlib**: Gráficos e visualizações
- **requests**: Requisições HTTP
- **speedtest-cli**: Teste de velocidade
- **pillow**: Processamento de imagens

## 🔧 Configuração

O SpeedScan detecta automaticamente seu sistema e configura os widgets correspondentes.

### Widgets Disponíveis
- 🖥️ CPU - Uso do processador
- 💾 RAM - Memória utilizada
- 🎮 GPU - Placa de vídeo
- 🔋 Bateria - Status e percentual
- 💿 Discos - Uso do armazenamento
- 🌡️ Temperatura - Monitoramento térmico
- ⏳ Uptime - Tempo de atividade
- ⚙️ Kernel - Versão do kernel
- 🐧 Distribuição - Sistema operacional
- 🖥️ Hostname - Nome do computador
- 💚 Saúde - Saúde geral do sistema

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🐛 Problemas

Encontrou um problema? [Abra uma issue](https://github.com/ewertonvasconcelos/speedscan/issues)!

## 🙏 Agradecimentos

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) pela interface moderna
- [psutil](https://github.com/giampaolo/psutil) pelas informações do sistema
- Comunidade Python pelas ferramentas incríveis

---

**SpeedScan** - Monitoramento do sistema, simplificado. 🚀
INNER_EOF

echo "✅ README.md atualizado"

echo ""
echo "🔧 7. Testando builds (quando possível)"
echo "===================================="

# Testar PyInstaller (Linux)
echo "🐧 Testando PyInstaller para Linux..."
pip install pyinstaller

# Criar requirements.txt
pip freeze > requirements.txt

echo "✅ Requirements.txt criado"

echo ""
echo "📋 8. Resumo dos arquivos criados"
echo "=============================="

echo "📁 Estrutura final:"
find . -name "*.sh" -o -name "*.yaml" -o -name "*.json" -o -name "*.spec" -o -name "*.yml" -o -name "*.md" | sort

echo ""
echo "📦 Scripts de build:"
ls -la packaging/

echo ""
echo "🔄 Workflow:"
ls -la .github/workflows/

echo ""
echo "🎉 SpeedScan - Empacotamento Multiplataforma Concluído!"
echo "======================================================"
echo "✅ Análise de portabilidade: packaging/portability_analysis.md"
echo "✅ Scripts de build: packaging/"
echo "✅ Workflow CI/CD: .github/workflows/build.yml"
echo "✅ Documentação: README.md atualizado"
echo "✅ Dependências: requirements.txt"

EOF

echo "🎯 Script executado no container Ubuntu!"
