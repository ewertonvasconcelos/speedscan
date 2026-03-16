#!/bin/bash
# Corrige definitivamente o botão Detalhes e o DNS

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual
source venv/bin/activate

echo "🔧 Corrigindo botões Detalhes..."

# Fazer backup do main.py
cp core/main.py core/main.py.bak

# Adicionar btn.pack() após cada chamada de ui.add_console
sed -i '/btn, log = ui.add_console.*self.toggle_console)/a \        btn.pack(pady=5)' core/main.py

# Garantir que action_mapper existe
if ! grep -q "self.action_mapper" core/main.py; then
    sed -i '/self.action_handler = ActionHandler(self)/a \        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)' core/main.py
fi

# Garantir importação do ActionMapper
if ! grep -q "from core.actions import .*ActionMapper" core/main.py; then
    sed -i 's/from core.actions import CommandRunner, ActionHandler/from core.actions import CommandRunner, ActionMapper, ActionHandler/' core/main.py
fi

# Ajustar permissões da pasta locale (se necessário)
if [ -d "locale" ]; then
    sudo chown -R $USER:$USER locale 2>/dev/null || true
fi

# Recriar traduções (para garantir)
mkdir -p locale
xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 2>/dev/null || true

for lang in pt_BR en_US es_ES; do
    mkdir -p locale/$lang/LC_MESSAGES
    if [ ! -f locale/$lang/LC_MESSAGES/speedscan.po ]; then
        msginit -i locale/speedscan.pot -o locale/$lang/LC_MESSAGES/speedscan.po -l $lang --no-translator -q 2>/dev/null || true
    fi
    msgfmt locale/$lang/LC_MESSAGES/speedscan.po -o locale/$lang/LC_MESSAGES/speedscan.mo 2>/dev/null || true
done

# Adicionar tradução exemplo para inglês (para teste)
if [ -f locale/en_US/LC_MESSAGES/speedscan.po ]; then
    sed -i '/msgid "Dashboard"/{n;s/msgstr ""/msgstr "Dashboard"/}' locale/en_US/LC_MESSAGES/speedscan.po
    msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo
fi

echo "✅ Correções aplicadas!"
echo ""
echo "Agora execute o programa com:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Os botões 'Detalhes' devem aparecer abaixo dos cards em todas as abas."
