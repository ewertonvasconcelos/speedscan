#!/bin/bash
# Correção final do botão Detalhes e sintaxe

set -e

cd ~/speedscan/speedscan

echo "🔧 Aplicando correção final..."

# Restaurar o último backup funcional (o que foi criado antes do erro)
# Usaremos o backup com timestamp 1773534450 (criado antes do erro)
if [ -f core/main.py.bak.1773534450 ]; then
    cp core/main.py.bak.1773534450 core/main.py
    echo "✅ Backup restaurado: core/main.py.bak.1773534450"
else
    echo "⚠️ Backup não encontrado. Criando novo backup do atual."
    cp core/main.py core/main.py.bak.$(date +%s)
fi

# ============================================================
# 1. Corrigir erro de sintaxe (argumento tag duplicado)
# ============================================================
echo "   + Corrigindo chamadas com tag duplicada..."
sed -i 's/, tag=tag, tag=/, tag=/' core/main.py
sed -i 's/, tag=tag)/, tag=tag)/' core/main.py  # (não altera, mas mantém)

# ============================================================
# 2. Ajustar toggle_console para esconder o botão ao fechar
# ============================================================
echo "   + Ajustando toggle_console..."
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

# ============================================================
# 3. Garantir que run_card_action esconda o console e botão se abertos
# ============================================================
echo "   + Ajustando run_card_action..."
# Procurar o bloco que fecha o console (se existir) e garantir que também esconda o botão
sed -i '/if tag in self.consoles_visible and self.consoles_visible\[tag\]/ {
    n
    s/log.pack_forget()/log.pack_forget()\n            btn.pack_forget()/
}' core/main.py

# Se não existir, adicionar o bloco
if ! grep -q "consoles_visible.*log.pack_forget" core/main.py; then
    sed -i '/log.delete/a \        if tag in self.consoles_visible and self.consoles_visible[tag]:\n            log.pack_forget()\n            btn = self.detail_buttons.get(tag)\n            if btn:\n                btn.pack_forget()\n                btn.configure(text=self._("Details ▼"))\n            self.consoles_visible[tag] = False' core/main.py
fi

# ============================================================
# 4. Garantir que o botão seja mostrado na primeira saída (ou fallback)
#    (já deve estar funcionando, mas vamos reforçar)
# ============================================================
# Já deve haver um método _show_detail_button e chamada em _run_subprocess
# Vamos verificar e adicionar se necessário
if ! grep -q "def _show_detail_button" core/main.py; then
    sed -i '/def run_card_action/i \    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)\n' core/main.py
fi

# Garantir que _run_subprocess chame _show_detail_button na primeira linha
if ! grep -q "self._show_detail_button" core/main.py; then
    sed -i '/for line in proc.stdout:/i \            if tag:\n                self._show_detail_button(tag)' core/main.py
fi

# ============================================================
# 5. Finalizar
# ============================================================
echo ""
echo "✅ Correções aplicadas com sucesso!"
echo ""
echo "Agora execute o programa:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Teste o botão Detalhes:"
echo "- Clique em um card (ex: 'Cloudflare DNS')."
echo "  * Se não exigir senha, o botão aparecerá imediatamente."
echo "  * Se exigir senha, aparecerá após a autenticação."
echo "- Clique no botão: console abre, texto vira 'Hide Details ▲'."
echo "- Clique novamente: console fecha E O BOTÃO DESAPARECE."
echo "- Execute outro card: o botão reaparecerá (se houver saída)."
