#!/bin/bash
# Script final para o botão Detalhes (comportamento exato)

set -e

cd ~/speedscan/speedscan

# Backup do main.py atual
cp core/main.py core/main.py.bak.ultimo
echo "✅ Backup criado: core/main.py.bak.ultimo"

echo "🔧 Aplicando correção definitiva..."

# ============================================================
# 1. Remover qualquer fallback existente
# ============================================================
perl -i -0777 -pe 's/def fallback\(\):.*?self\.after\(\d+,.*?\)//gs' core/main.py

# ============================================================
# 2. Garantir que a variável _btn_shown exista e seja resetada
# ============================================================
if ! grep -q "self._btn_shown" core/main.py; then
    sed -i '/self.consoles_visible = {}/a \        self._btn_shown = False' core/main.py
fi

sed -i '/def run_card_action/,/threading.Thread/ {
    /log.delete/a \        self._btn_shown = False
}' core/main.py

# ============================================================
# 3. Garantir que _show_detail_button exista
# ============================================================
if ! grep -q "def _show_detail_button" core/main.py; then
    sed -i '/def run_card_action/i \    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)\n' core/main.py
fi

# ============================================================
# 4. Modificar _run_subprocess para chamar _show_detail_button na primeira saída
# ============================================================
sed -i '/for line in proc.stdout:/i \            if not self._btn_shown:\n                self._show_detail_button(tag)\n                self._btn_shown = True' core/main.py

# ============================================================
# 5. Ajustar toggle_console para que ao fechar, o botão suma
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
            btn.configure(text=self._("Details ▼"))\n\
            self.consoles_visible[tag] = False\n\
        else:\n\
            log.pack(fill="x", expand=True, padx=5, before=btn)\n\
            btn.configure(text=self._("Hide Details ▲"))\n\
            self.consoles_visible[tag] = True
}' core/main.py

echo "✅ Botão corrigido."

# ============================================================
# 6. Garantir que as traduções básicas estejam presentes (já temos)
# ============================================================
echo "🌐 Verificando traduções..."
if [ -d locale ]; then
    msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo 2>/dev/null || true
    msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo 2>/dev/null || true
    msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo 2>/dev/null || true
    echo "✅ Traduções recompiladas."
else
    echo "⚠️ Pasta locale não encontrada. As traduções podem não funcionar."
fi

echo ""
echo "🎉 Correções aplicadas!"
echo "Execute o programa e teste:"
echo "- Clique em um card sem senha → botão aparece imediatamente."
echo "- Clique em um card com senha → botão só aparece após autenticação."
echo "- Clique no botão para abrir/fechar → ao fechar, o botão some."
echo "- Execute outro card → o botão anterior some e o novo segue a regra."
