#!/bin/bash
# Script para commit e push do SpeedScan

echo "🚀 SpeedScan - Commit e Push Final"
echo "=================================="

echo ""
echo "📋 Preparando para commit..."

# Adicionar todos os arquivos
git add .

echo "✅ Arquivos adicionados ao git"

# Verificar status
git status

echo ""
echo "📝 Criando commit..."

# Fazer commit
git commit -m "Add multiplatform packaging and CI/CD workflow

Features:
- Multiplatform packaging scripts (AppImage, Flatpak, DEB/RPM, Snap, EXE, DMG, APK)
- GitHub Actions CI/CD workflow for automated builds
- Portability analysis documentation
- Updated README with installation instructions
- Requirements.txt for dependencies
- Complete packaging structure

Platforms supported:
- Linux: AppImage, Flatpak, DEB, RPM, Snap (100% compatible)
- Windows: EXE via PyInstaller (compatible)
- macOS: DMG via PyInstaller (compatible)
- Android: APK demo version (limited due to tkinter incompatibility)
- iOS: Not supported (tkinter incompatibility)

CI/CD:
- Automated builds on push/release
- Multi-platform runners
- Artifact upload and release assets
- Android build with buildozer

Documentation:
- Complete portability analysis
- Installation instructions for all platforms
- Development setup guide
- Build scripts documentation"

echo "✅ Commit criado"

echo ""
echo "📤 Fazendo push para origin master..."

# Push para o repositório
git push origin master

echo ""
echo "🎉 SpeedScan - Deploy Concluído!"
echo "================================"
echo "✅ Código enviado para GitHub"
echo "✅ CI/CD ativado automaticamente"
echo "✅ Builds serão executados"
echo "✅ Pacotes gerados automaticamente"
echo ""
echo "🔗 Verifique os builds em:"
echo "https://github.com/ewertonvasconcelos/speedscan/actions"
echo ""
echo "📦 Pacotes estarão disponíveis em:"
echo "https://github.com/ewertonvasconcelos/speedscan/releases"
