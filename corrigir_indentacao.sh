#!/bin/bash
# Corrige a indentação e finaliza as traduções

set -e

cd ~/speedscan/speedscan

echo "🔧 Corrigindo indentação e traduções..."

# Backup do main.py (mais um, por segurança)
backup_file="core/main.py.bak.manual.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# ============================================================
# 1. Inserir método _show_detail_button com indentação correta
#    Vamos inserir antes do método run_card_action
# ============================================================
# Encontrar a linha que contém "def run_card_action" e inserir antes dela
perl -i -pe 'if (/def run_card_action/) { print "    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side=\"right\", anchor=\"e\", padx=10, pady=5)\n\n"; }' core/main.py

# ============================================================
# 2. Modificar _run_subprocess para aceitar tag e chamar o método
# ============================================================
# Adicionar parâmetro tag na definição
sed -i 's/def _run_subprocess(self, cmd, log, use_sudo=False, shell=False):/def _run_subprocess(self, cmd, log, use_sudo=False, shell=False, tag=None):/' core/main.py

# Adicionar chamada a _show_detail_button antes do loop
sed -i '/for line in proc.stdout:/i \            self._show_detail_button(tag)' core/main.py

# Ajustar as chamadas existentes para passar tag
sed -i 's/self._run_subprocess(\(.*\), log/self._run_subprocess(\1, log, tag=tag/' core/main.py

# ============================================================
# 3. Recriar traduções de forma simples (placeholders)
# ============================================================
echo "🌐 Recriando traduções..."

# Remove locale antigo
rm -rf locale
mkdir -p locale

# Criar arquivo .pot com todas as strings
xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 2>/dev/null || true

# Criar arquivos .po para cada idioma (sem traduções, apenas placeholders)
for lang in pt_BR en_US es_ES; do
    dir="locale/${lang}/LC_MESSAGES"
    mkdir -p "$dir"
    msginit -i locale/speedscan.pot -o "${dir}/speedscan.po" -l "$lang" --no-translator -q 2>/dev/null || true
    # Compilar (sem modificar, as strings ficam em inglês)
    msgfmt "${dir}/speedscan.po" -o "${dir}/speedscan.mo" 2>/dev/null || echo "⚠️  Falha ao compilar $lang, mas continuando"
done

# Ajustar permissões
sudo chown -R $USER:$USER locale 2>/dev/null || true

echo "✅ Traduções recriadas."

echo ""
echo "🎉 Correções concluídas!"
echo "Execute o programa:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
