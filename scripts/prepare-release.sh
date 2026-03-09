#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SpeedScan - Script de Preparação de Release${NC}"
echo -e "${GREEN}========================================${NC}"

# Verifica se está no diretório correto
if [ ! -d ".git" ]; then
    echo -e "${RED}Erro: Execute o script da raiz do repositório.${NC}"
    exit 1
fi

# 1. Verificar se há mudanças não commitadas
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Existem mudanças não commitadas.${NC}"
    read -p "Deseja continuar mesmo assim? (s/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

# 2. Limpeza (remover arquivos desnecessários)
echo -e "${GREEN}Passo 1: Limpando arquivos temporários e pastas de build...${NC}"

# Pastas para remover (excluindo scripts e outras essenciais)
folders_to_remove=(
    "AppDir"
    "artifacts"
    "core-backup-*"
    "speedscan_modules"
    "squashfs-root"
    "snap"
    "SpeedScan-Linux"
    # "scripts"  # <-- COMENTADO para não remover a si mesmo
)

for pattern in "${folders_to_remove[@]}"; do
    for folder in $pattern; do
        if [ -d "$folder" ]; then
            echo -e "${YELLOW}Removendo pasta: $folder${NC}"
            rm -rf "$folder"
        fi
    done
done

# Arquivos para remover
files_to_remove=(
    "fix_*.py"
    "debug_*.py"
    "rebuild_*.py"
    "setup_*.py"
    "parte*"
    "*.b64"
    "*.patch"
    "main_corrigido.b64"
    "main.py.b64.part*"
    "parte_??"
    "metrics.db"
    "todos_os_modulos.txt"
    "restart_speedscan.sh.bak.*"
    "io.github.ewertonvasconcelos.speedscan.yml"
    "settings.py"
    "*.AppImage"
    "*.deb"
    "*.rpm"
    "*.exe"
    "*.dmg"
)

for pattern in "${files_to_remove[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            echo -e "${YELLOW}Removendo arquivo: $file${NC}"
            rm -f "$file"
        fi
    done
done

# 3. Atualizar .gitignore (se necessário)
echo -e "${GREEN}Passo 2: Verificando .gitignore...${NC}"
if ! grep -q "# Artefatos de build" .gitignore; then
    cat >> .gitignore << 'EOF'

# Artefatos de build
dist/
build/
*.spec
*.db
*.log
*.deb
*.rpm
*.exe
*.dmg
*.AppImage

# Scripts temporários
fix_*.py
debug_*.py
temp_*.py
*.bak
*.b64
*.patch
parte_*
EOF
    echo -e "${GREEN}.gitignore atualizado.${NC}"
else
    echo -e ".gitignore já contém as entradas necessárias."
fi

# 4. Adicionar e commitar mudanças
echo -e "${GREEN}Passo 3: Commit das alterações...${NC}"
git add .
git add -u
git commit -m "chore: limpeza automática para release" || echo "Nada para commitar."

# 5. Perguntar versão da tag
echo -e "${GREEN}Passo 4: Criando tag de versão${NC}"
current_version=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -n "$current_version" ]; then
    echo -e "Última tag: ${YELLOW}$current_version${NC}"
fi
read -p "Digite a nova versão (ex: v1.0.1): " tag_version

if [ -z "$tag_version" ]; then
    echo -e "${RED}Versão não informada. Abortando.${NC}"
    exit 1
fi

# 6. Criar tag
git tag -a "$tag_version" -m "Versão $tag_version"
if [ $? -ne 0 ]; then
    echo -e "${RED}Erro ao criar tag. Verifique se ela já existe.${NC}"
    exit 1
fi

# 7. Push
echo -e "${GREEN}Passo 5: Enviando para o GitHub...${NC}"
git push origin main
git push origin "$tag_version"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Release $tag_version preparada e enviada!${NC}"
echo -e "${GREEN}Acesse o GitHub Actions para acompanhar o build:${NC}"
echo -e "${YELLOW}https://github.com/ewertonvasconcelos/speedscan/actions${NC}"
echo -e "${GREEN}========================================${NC}"
