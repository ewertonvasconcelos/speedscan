#!/bin/bash
# build_rpm.sh - Gera o pacote .rpm do SpeedScan (versão final corrigida)

set -e

cd "$(dirname "$0")"

# ============================================
# CONFIGURAÇÕES
# ============================================
APP_NAME="speedscan"
VERSION="0.9.0"
RELEASE="1"
ARCH="x86_64"
MAINTAINER="Ewerton Vasconcelos <ewerton@consertop6.com>"
SUMMARY="Ferramenta de diagnóstico e otimização de sistemas"
LICENSE="MIT"
URL="https://github.com/ewertonvasconcelos/speedscan"
EXECUTABLE="dist/$APP_NAME"
ICON_PATH="icon.png"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}=== Iniciando build do pacote .rpm ===${NC}"

# ============================================
# VERIFICAÇÕES INICIAIS
# ============================================
if [ ! -f "$EXECUTABLE" ]; then
    echo -e "${RED}Erro: executável não encontrado em $EXECUTABLE. Execute primeiro o build do PyInstaller.${NC}"
    exit 1
fi

if ! command -v rpmbuild &> /dev/null; then
    echo -e "${RED}Erro: rpmbuild não encontrado. Instale com: sudo dnf install rpm-build${NC}"
    exit 1
fi

# ============================================
# PREPARAÇÃO DO DIRETÓRIO DE BUILD
# ============================================
RPM_BUILD_ROOT="$HOME/rpmbuild"
mkdir -p "$RPM_BUILD_ROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# ============================================
# COPIA OS ARQUIVOS PARA O DIRETÓRIO SOURCES
# ============================================
cp "$EXECUTABLE" "$RPM_BUILD_ROOT/SOURCES/speedscan"

# Verifica se o ícone existe e copia
if [ -f "$ICON_PATH" ]; then
    cp "$ICON_PATH" "$RPM_BUILD_ROOT/SOURCES/icon.png"
    HAS_ICON=1
else
    echo -e "${RED}Aviso: ícone não encontrado. O pacote será gerado sem ícone.${NC}"
    HAS_ICON=0
fi

# Cria o arquivo .desktop
cat > "$RPM_BUILD_ROOT/SOURCES/speedscan.desktop" << EOF
[Desktop Entry]
Name=SpeedScan
Comment=$SUMMARY
Exec=$APP_NAME
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Utility;System;
EOF

# ============================================
# CRIAÇÃO DO ARQUIVO SPEC
# ============================================
SPEC_FILE="$RPM_BUILD_ROOT/SPECS/$APP_NAME.spec"

CHANGELOG_DATE=$(LC_ALL=C date +"%a %b %d %Y")

# Monta a lista de arquivos do %files
FILES_LIST="/usr/bin/$APP_NAME
/usr/share/applications/$APP_NAME.desktop"

if [ $HAS_ICON -eq 1 ]; then
    FILES_LIST="$FILES_LIST
/usr/share/icons/hicolor/48x48/apps/$APP_NAME.png
/usr/share/icons/hicolor/96x96/apps/$APP_NAME.png
/usr/share/icons/hicolor/128x128/apps/$APP_NAME.png"
fi

cat > "$SPEC_FILE" << EOF
Name: $APP_NAME
Version: $VERSION
Release: $RELEASE
Summary: $SUMMARY
License: $LICENSE
URL: $URL
BuildArch: $ARCH
Requires: python3
AutoReqProv: no

Source0: speedscan
Source1: icon.png
Source2: speedscan.desktop

%description
SpeedScan é uma ferramenta de diagnóstico e otimização de sistemas
desenvolvida em Python com CustomTkinter. Oferece monitoramento em tempo
real, otimização de desempenho, configuração de rede e diagnóstico de
drivers.

%prep
# Não há necessidade de preparar

%build
# Não há compilação

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/48x48/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/96x96/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/128x128/apps

install -m 755 %{SOURCE0} %{buildroot}/usr/bin/$APP_NAME

if [ -f %{SOURCE1} ]; then
    install -m 644 %{SOURCE1} %{buildroot}/usr/share/icons/hicolor/48x48/apps/$APP_NAME.png
    install -m 644 %{SOURCE1} %{buildroot}/usr/share/icons/hicolor/96x96/apps/$APP_NAME.png
    install -m 644 %{SOURCE1} %{buildroot}/usr/share/icons/hicolor/128x128/apps/$APP_NAME.png
fi

install -m 644 %{SOURCE2} %{buildroot}/usr/share/applications/$APP_NAME.desktop

%files
$FILES_LIST

%changelog
* $CHANGELOG_DATE $MAINTAINER - $VERSION-$RELEASE
- Primeira versão empacotada.
EOF

# ============================================
# EXECUÇÃO DO RPMBUILD
# ============================================
rpmbuild -bb "$SPEC_FILE" --define "_topdir $RPM_BUILD_ROOT"

# ============================================
# MOVENDO O RPM GERADO
# ============================================
RPM_FILE="$RPM_BUILD_ROOT/RPMS/$ARCH/${APP_NAME}-${VERSION}-${RELEASE}.${ARCH}.rpm"
if [ -f "$RPM_FILE" ]; then
    cp "$RPM_FILE" .
    echo -e "${GREEN}Pacote RPM gerado com sucesso: $(basename "$RPM_FILE")${NC}"
else
    echo -e "${RED}Falha ao gerar o RPM. Verifique os logs acima.${NC}"
    exit 1
fi

echo -e "${GREEN}=== Build concluído! ===${NC}"
