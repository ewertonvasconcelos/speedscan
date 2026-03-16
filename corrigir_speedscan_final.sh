#!/bin/bash
# Script definitivo para corrigir permissões, botão Detalhes e traduções

set -e

echo "🔧 Iniciando correção final do SpeedScan..."

# 1. Verificar diretório
if [ ! -d "core" ]; then
    echo "❌ Erro: execute este script dentro da pasta que contém a subpasta 'core/'"
    exit 1
fi

# 2. Ativar ambiente virtual (ou criar)
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Instalar dependências (caso falte)
pip install --upgrade pip > /dev/null
pip install customtkinter psutil matplotlib requests speedtest-cli pillow > /dev/null

# 4. Corrigir permissões da pasta locale (se foi criada pelo container)
if [ -d "locale" ]; then
    echo "🔐 Ajustando permissões da pasta locale..."
    sudo chown -R $USER:$USER locale
fi

# 5. Garantir que action_mapper existe (já deve estar, mas reforça)
if ! grep -q "self.action_mapper" core/main.py; then
    echo "   - Adicionando action_mapper..."
    cp core/main.py core/main.py.bak
    sed -i '/self.action_handler = ActionHandler(self)/a \        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)' core/main.py
fi

# 6. Garantir importação do ActionMapper
if ! grep -q "from core.actions import .*ActionMapper" core/main.py; then
    echo "   - Corrigindo importação..."
    sed -i 's/from core.actions import CommandRunner, ActionHandler/from core.actions import CommandRunner, ActionMapper, ActionHandler/' core/main.py
fi

# 7. CORRIGIR BOTÃO DETALHES: adicionar btn.pack() após cada ui.add_console
echo "🖱️ Corrigindo botões Detalhes (empacotamento)..."
for aba in optimization network drivers security; do
    sed -i "/btn, log = ui.add_console(parent, \"$aba\"/a \        btn.pack(pady=5)" core/main.py
done

# 8. Recriar arquivos de tradução (se necessário) e compilar
echo "🌐 Atualizando traduções..."
mkdir -p locale

# Extrair strings (se .pot não existir ou estiver desatualizado)
xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 2>/dev/null || true

# Função para criar/atualizar .po e .mo
criar_idioma() {
    local lang=$1
    local dir="locale/${lang}/LC_MESSAGES"
    mkdir -p "$dir"
    if [ ! -f "${dir}/speedscan.po" ]; then
        msginit -i locale/speedscan.pot -o "${dir}/speedscan.po" -l "$lang" --no-translator -q
    fi
    # Atualizar .po com novas strings (opcional)
    msgmerge --update "${dir}/speedscan.po" locale/speedscan.pot 2>/dev/null || true
    # Compilar
    msgfmt "${dir}/speedscan.po" -o "${dir}/speedscan.mo"
}

criar_idioma "pt_BR"
criar_idioma "en_US"
criar_idioma "es_ES"

# 9. Inserir uma tradução de exemplo para inglês (para teste)
PO_EN="locale/en_US/LC_MESSAGES/speedscan.po"
if [ -f "$PO_EN" ]; then
    sed -i '/msgid "Dashboard"/{n;s/msgstr ""/msgstr "Dashboard"/}' "$PO_EN"
    msgfmt "$PO_EN" -o "locale/en_US/LC_MESSAGES/speedscan.mo"
fi

echo "✅ Correção concluída!"
echo ""
echo "Agora execute:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Após abrir o programa, você verá o botão 'Detalhes' abaixo dos cards."
echo "Clique nele para exibir o console e veja a saída dos comandos."
