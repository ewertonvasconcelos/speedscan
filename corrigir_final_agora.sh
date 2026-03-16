#!/bin/bash
# Corrige botão Detalhes e gera traduções com placeholders

set -e

cd ~/speedscan/speedscan

[ -d "venv" ] && source venv/bin/activate

echo "🔧 Aplicando correções finais..."

# Backup do main.py
backup_file="core/main.py.bak.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# ============================================================
# 1. Modificar run_card_action: remover empacotamento imediato
# ============================================================
sed -i '/if btn and not btn.winfo_ismapped():/,/btn.pack/d' core/main.py

# ============================================================
# 2. Adicionar método auxiliar _show_detail_button
# ============================================================
# Verificar se o método já existe para evitar duplicação
if ! grep -q "def _show_detail_button" core/main.py; then
    sed -i '/def run_card_action/a \\n    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)' core/main.py
fi

# ============================================================
# 3. Modificar _run_subprocess para chamar _show_detail_button
# ============================================================
sed -i 's/def _run_subprocess(self, cmd, log, use_sudo=False, shell=False):/def _run_subprocess(self, cmd, log, use_sudo=False, shell=False, tag=None):/' core/main.py
sed -i 's/self._run_subprocess(\(.*\), log/self._run_subprocess(\1, log, tag=tag/' core/main.py
# Inserir a chamada dentro do loop
sed -i '/for line in proc.stdout:/i \            self._show_detail_button(tag)' core/main.py

# ============================================================
# 4. Gerar traduções completas (extrair todas as strings e criar placeholders)
# ============================================================
echo "🌐 Gerando arquivos de tradução completos..."

# Remover locale antigo
rm -rf locale
mkdir -p locale

# Extrair todas as strings para um arquivo .pot
if command -v xgettext >/dev/null 2>&1; then
    xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 2>/dev/null || echo "⚠️ xgettext falhou, criando .pot vazio"
else
    echo "⚠️ xgettext não encontrado. Criando .pot vazio."
fi

# Se o .pot não foi criado ou está vazio, criar um manualmente
if [ ! -s locale/speedscan.pot ]; then
    cat > locale/speedscan.pot << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"

EOF
fi

# Função para criar .po e .mo com placeholders (msgstr = msgid)
criar_idioma() {
    local lang=$1
    local dir="locale/${lang}/LC_MESSAGES"
    mkdir -p "$dir"
    if command -v msginit >/dev/null 2>&1; then
        msginit -i locale/speedscan.pot -o "${dir}/speedscan.po" -l "$lang" --no-translator -q 2>/dev/null || true
    fi
    # Se msginit falhou ou não existe, criar .po manualmente
    if [ ! -f "${dir}/speedscan.po" ]; then
        cp locale/speedscan.pot "${dir}/speedscan.po"
        sed -i "1s/^/\"Language: ${lang}\\n\"/" "${dir}/speedscan.po"
    fi
    # Substituir todas as msgstr vazias pelo mesmo valor de msgid (placeholders)
    # Isso é mais seguro com awk
    awk '/^msgid / {id=$0; getline; if ($0 ~ /^msgstr ""/) {sub(/msgid/, "msgstr", id); print id} else {print id; print}}' "${dir}/speedscan.po" > "${dir}/speedscan.tmp"
    mv "${dir}/speedscan.tmp" "${dir}/speedscan.po"
    msgfmt "${dir}/speedscan.po" -o "${dir}/speedscan.mo" 2>/dev/null || echo "⚠️ Falha ao compilar ${lang}"
}

criar_idioma "pt_BR"
criar_idioma "en_US"
criar_idioma "es_ES"

sudo chown -R $USER:$USER locale 2>/dev/null || true

echo "✅ Traduções geradas (placeholders em inglês)."
echo ""
echo "🎉 Correções aplicadas!"
echo ""
echo "Agora execute o programa:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"

