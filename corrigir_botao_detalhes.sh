#!/bin/bash
# Corrige o comportamento do botão Detalhes conforme especificado:
# - Aparece só após execução do comando (ou após fallback de 2s)
# - Se exigir senha, aparece só após a senha (quando saída começa)
# - Clicar para abrir console muda texto para "Hide Details ▲"
# - Clicar para fechar console remove o botão completamente e reseta estado
# - Ao executar novo card, botão anterior é removido

set -e

cd ~/speedscan/speedscan

# Backup
backup_file="core/main.py.bak.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# ============================================================
# 1. Adicionar variável de controle _btn_shown no __init__
# ============================================================
if ! grep -q "self._btn_shown" core/main.py; then
    sed -i '/self.consoles_visible = {}/a \        self._btn_shown = False' core/main.py
fi

# ============================================================
# 2. Modificar run_card_action para remover empacotamento imediato,
#    resetar flag e esconder botão se visível
# ============================================================
# Remover o bloco que empacota o botão imediatamente
sed -i '/if btn and not btn.winfo_ismapped():/,/btn.pack/d' core/main.py

# Inserir no início de run_card_action (após obter o log) o reset e fechamento
sed -i '/log.delete/a \        # Reseta flag de botão mostrado para esta aba\n        self._btn_shown = False\n        # Se o botão estiver visível, escondê-lo\n        btn = self.detail_buttons.get(tag)\n        if btn and btn.winfo_ismapped():\n            btn.pack_forget()' core/main.py

# ============================================================
# 3. Adicionar método _show_detail_button (se não existir)
# ============================================================
if ! grep -q "def _show_detail_button" core/main.py; then
    sed -i '/def run_card_action/i \    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)\n            btn.configure(text=self._("Details ▼"))\n' core/main.py
fi

# ============================================================
# 4. Modificar _run_subprocess para mostrar botão na primeira linha
# ============================================================
# Adicionar parâmetro tag na definição (se não tiver)
sed -i 's/def _run_subprocess(self, cmd, log, use_sudo=False, shell=False):/def _run_subprocess(self, cmd, log, use_sudo=False, shell=False, tag=None):/' core/main.py

# Ajustar chamadas para passar tag (já fizemos antes, mas vamos garantir)
sed -i 's/self._run_subprocess(\(.*\), log/self._run_subprocess(\1, log, tag=tag/' core/main.py

# Inserir no loop de saída a chamada para mostrar botão
sed -i '/for line in proc.stdout:/i \            if not self._btn_shown:\n                self._show_detail_button(tag)\n                self._btn_shown = True' core/main.py

# ============================================================
# 5. Adicionar fallback de 2 segundos para comandos sem saída
# ============================================================
sed -i '/threading.Thread.*start()/a \        # Fallback: se não houver saída em 2s, mostra o botão\n        def fallback():\n            if not self._btn_shown:\n                self._show_detail_button(tag)\n                self._btn_shown = True\n        self.after(2000, fallback)' core/main.py

# ============================================================
# 6. Modificar toggle_console para esconder botão ao fechar console
# ============================================================
sed -i '/def toggle_console/,/^    def/ {
    /def toggle_console/,/^    def/ c\
    def toggle_console(self, tag):\n\
        btn = self.detail_buttons.get(tag)\n\
        log = self.logs.get(tag)\n\
        if not btn or not log:\n\
            return\n\
        if self.consoles_visible.get(tag, False):\n\
            log.pack_forget()\n\
            btn.pack_forget()\n\
            self._btn_shown = False\n\
            self.consoles_visible[tag] = False\n\
        else:\n\
            log.pack(fill="x", expand=True, padx=5, before=btn)\n\
            btn.configure(text=self._("Hide Details ▲"))\n\
            self.consoles_visible[tag] = True
}' core/main.py

echo "✅ Correções aplicadas."
echo "Execute o programa e teste:"
echo "- Clique em um card: o botão 'Details ▼' aparecerá após a primeira saída (ou após 2s)."
echo "- Se exigir senha, aparecerá depois da senha."
echo "- Clique no botão: console abre e texto muda para 'Hide Details ▲'."
echo "- Clique novamente: console fecha e botão some."
echo "- Execute outro card: o processo recomeça."
