#!/bin/bash
# Script para corrigir action_mapper e gerar tradução em inglês para teste

set -e  # parar em caso de erro

cd ~/speedscan/speedscan  # ajuste se o caminho for diferente

echo "🔧 Ativando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "📦 Instalando dependências (se necessário)..."
pip install --quiet customtkinter psutil matplotlib requests speedtest-cli pillow

echo "🛠️ Corrigindo main.py (adicionando action_mapper)..."
MAIN_FILE="core/main.py"

# Verifica se a linha já existe
if ! grep -q "self.action_mapper = ActionMapper" "$MAIN_FILE"; then
    # Faz backup
    cp "$MAIN_FILE" "$MAIN_FILE.bak"
    # Insere a linha após a criação do action_handler
    sed -i '/self.action_handler = ActionHandler(self)/a \        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)' "$MAIN_FILE"
    echo "✅ action_mapper adicionado."
else
    echo "⏩ action_mapper já existe."
fi

# Verifica importação
if ! grep -q "^from core.actions import .*ActionMapper" "$MAIN_FILE"; then
    sed -i 's/^from core.actions import \(.*\)/from core.actions import \1, ActionMapper/' "$MAIN_FILE"
    echo "✅ Importação do ActionMapper adicionada."
fi

echo "🌐 Gerando arquivo de tradução em inglês para teste..."
mkdir -p locale/en_US/LC_MESSAGES

# Se o arquivo .pot não existir, cria
if [ ! -f "locale/speedscan.pot" ]; then
    xgettext -d speedscan -o locale/speedscan.pot core/*.py
fi

# Cria .po para inglês se não existir
if [ ! -f "locale/en_US/LC_MESSAGES/speedscan.po" ]; then
    msginit -i locale/speedscan.pot -o locale/en_US/LC_MESSAGES/speedscan.po -l en_US --no-translator
fi

# Faz backup do .po original
cp locale/en_US/LC_MESSAGES/speedscan.po locale/en_US/LC_MESSAGES/speedscan.po.bak

# Gera um arquivo .po com todas as msgstr iguais às msgid (tradução = original)
# Isso permite testar a troca de idioma sem precisar traduzir manualmente
msggrep --msgid -e "." locale/en_US/LC_MESSAGES/speedscan.po | \
    sed 's/^msgstr ".*"/msgstr ""/' | \
    awk 'BEGIN {in_msgid=0} /^msgid / {in_msgid=1; print; next} /^$/ {in_msgid=0; print; next} in_msgid && /^"/ {gsub(/"/, "", $0); print "msgstr \"" $0 "\""; next} {print}' \
    > locale/en_US/LC_MESSAGES/speedscan_temp.po

# Substitui o arquivo original
mv locale/en_US/LC_MESSAGES/speedscan_temp.po locale/en_US/LC_MESSAGES/speedscan.po

# Compila
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo

echo "✅ Tradução em inglês gerada (msgstr = msgid)."

echo "🚀 Iniciando SpeedScan..."
python3 -m core.main
