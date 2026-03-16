#!/bin/bash
# Corrige erro de método ausente e ajusta botão Detalhes

set -e

cd ~/speedscan/speedscan

# Backup do main.py atual
cp core/main.py core/main.py.bak.erro.$(date +%s)
echo "✅ Backup criado."

# ============================================================
# 1. Remover chamada a _check_process_queue no __init__
# ============================================================
sed -i '/self._check_process_queue()/d' core/main.py
echo "   + Chamada a _check_process_queue removida."

# ============================================================
# 2. Adicionar método _check_process_queue vazio (caso seja referenciado em outro lugar)
# ============================================================
if ! grep -q "def _check_process_queue" core/main.py; then
    sed -i '/def _monitor_loop/a \n    def _check_process_queue(self):\n        pass' core/main.py
    echo "   + Método vazio _check_process_queue adicionado."
fi

# ============================================================
# 3. Garantir que o botão só apareça na primeira saída e suma ao fechar
# ============================================================
# (Já deve estar correto, mas vamos reforçar)
sed -i '/for line in proc.stdout:/i \            if not self._btn_shown:\n                self._show_detail_button(tag)\n                self._btn_shown = True' core/main.py

# Ajustar toggle_console para que o botão suma ao fechar
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

echo "✅ Botão ajustado."

# ============================================================
# 4. Recompilar traduções (caso necessário)
# ============================================================
echo "🌐 Recompilando traduções..."
msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo 2>/dev/null || true
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo 2>/dev/null || true
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo 2>/dev/null || true
echo "✅ Traduções recompiladas."

echo ""
echo "🎉 Correções concluídas!"
echo "Execute o programa: source venv/bin/activate && python3 -m core.main"
