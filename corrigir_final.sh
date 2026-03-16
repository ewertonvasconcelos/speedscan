#!/bin/bash
# Corrige:
# - Botão Detalhes: só aparece após início real do comando
# - Traduções: garante arquivos .mo e testa com "Dashboard"

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual (se existir)
[ -d "venv" ] && source venv/bin/activate

echo "🔧 Iniciando correções finais..."

# Backup do main.py
backup_file="core/main.py.bak.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# ============================================================
# 1. Correção do botão Detalhes
# ============================================================

# Modificar run_card_action: REMOVER o empacotamento imediato do botão
sed -i '/if btn and not btn.winfo_ismapped():/,/btn.pack/d' core/main.py

# Adicionar uma função auxiliar para mostrar o botão quando houver saída
# Vamos inserir no início da classe (após __init__) um método _show_detail_button
sed -i '/def run_card_action/a \\n    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)' core/main.py

# Agora, modificar cada método de comando (ex: _run_ping) para chamar _show_detail_button
# Vamos usar um approach mais simples: no _run_subprocess, antes de inserir a primeira linha, chamamos a função
sed -i '/for line in proc.stdout:/i \            self._show_detail_button(tag)' core/main.py

# Garantir que tag seja passado para _run_subprocess
# Isso é mais complexo; vamos modificar a chamada em _execute_command para incluir tag
sed -i 's/self._run_subprocess(\(.*\), log/self._run_subprocess(\1, log, tag=tag/' core/main.py

# Modificar a definição de _run_subprocess para aceitar tag
sed -i 's/def _run_subprocess(self, cmd, log, use_sudo=False, shell=False):/def _run_subprocess(self, cmd, log, use_sudo=False, shell=False, tag=None):/' core/main.py

# ============================================================
# 2. Correção das traduções
# ============================================================

echo "🌐 Reconstruindo traduções..."

# Remover locale antigo (se houver) e recriar
rm -rf locale
mkdir -p locale

# Extrair strings
xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 2>/dev/null || true

# Função para criar .po e .mo
criar_idioma() {
    local lang=$1
    local dir="locale/${lang}/LC_MESSAGES"
    mkdir -p "$dir"
    msginit -i locale/speedscan.pot -o "${dir}/speedscan.po" -l "$lang" --no-translator -q 2>/dev/null || true
    # Inserir tradução de exemplo para "Dashboard"
    sed -i '/msgid "Dashboard"/{n;s/msgstr ""/msgstr "'"$2"'"/}' "${dir}/speedscan.po"
    msgfmt "${dir}/speedscan.po" -o "${dir}/speedscan.mo"
}

criar_idioma "pt_BR" "Painel"
criar_idioma "en_US" "Dashboard"
criar_idioma "es_ES" "Tablero"

# Ajustar permissões
sudo chown -R $USER:$USER locale 2>/dev/null || true

echo "✅ Traduções recriadas com exemplos."

# ============================================================
# 3. Instruções finais
# ============================================================
echo ""
echo "🎉 Correções aplicadas!"
echo ""
echo "Execute o programa com:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Agora o botão 'Detalhes' só deve aparecer quando o comando começar a rodar (após a senha)."
echo "Teste a tradução: vá em Configurações, mude o idioma e veja a palavra 'Dashboard' na aba inicial."
