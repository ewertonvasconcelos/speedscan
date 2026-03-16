#!/bin/bash
# Correção emergencial: botão visível e tradução de exemplo

set -e

cd ~/speedscan/speedscan
source venv/bin/activate

# Backup
cp core/main.py core/main.py.bak.emergencia

echo "🔧 Aplicando correção emergencial..."

# 1. Restaurar empacotamento imediato do botão (remove a lógica de aparecer só depois)
sed -i '/_show_detail_button/d' core/main.py
sed -i '/if tag:/d' core/main.py
sed -i '/self._show_detail_button/d' core/main.py
sed -i '/def _show_detail_button/,/^    def/d' core/main.py

# Reinserir o pack imediato em run_card_action
sed -i '/log.delete/a \        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)' core/main.py

# 2. Adicionar traduções de exemplo para "Dashboard"
mkdir -p locale/pt_BR/LC_MESSAGES locale/en_US/LC_MESSAGES locale/es_ES/LC_MESSAGES

cat > locale/pt_BR/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: pt_BR\n"

msgid "Dashboard"
msgstr "Painel"
EOF

cat > locale/en_US/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: en_US\n"

msgid "Dashboard"
msgstr "Dashboard"
EOF

cat > locale/es_ES/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: es_ES\n"

msgid "Dashboard"
msgstr "Tablero"
EOF

# Compilar
msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo

echo "✅ Traduções de exemplo inseridas."

echo "🎉 Correção aplicada! Execute o programa novamente."

