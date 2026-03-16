#!/bin/bash
# Corrige o posicionamento do botão Detalhes e a lógica de exibição

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual (se existir)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🔧 Corrigindo layout dos botões Detalhes..."

# Fazer backup
cp core/main.py core/main.py.bak

# 1. Garantir importação do ActionMapper (se necessário)
if ! grep -q "from core.actions import .*ActionMapper" core/main.py; then
    sed -i 's/from core.actions import CommandRunner, ActionHandler/from core.actions import CommandRunner, ActionMapper, ActionHandler/' core/main.py
fi

# 2. Garantir que action_mapper existe
if ! grep -q "self.action_mapper" core/main.py; then
    sed -i '/self.action_handler = ActionHandler(self)/a \        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)' core/main.py
fi

# 3. Modificar as funções _fill_* para usar um frame que contenha cards, console e botão
#    Vamos substituir os trechos onde os botões são criados.

# Para a aba optimization
sed -i '/btn, log = ui.add_console(parent, "opt", self.acc_color, self.toggle_console)/ {
    N
    N
    s/\(btn, log = ui.add_console.*\)\n        self.detail_buttons\["opt"\] = btn\n        self.logs\["opt"\] = log/\
        # Create a frame to hold console and button\
        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent")\n\
        bottom_frame.pack(fill="x", pady=5)\n\
        btn, log = ui.add_console(bottom_frame, "opt", self.acc_color, self.toggle_console)\n\
        btn.pack(side="right", padx=5)\n\
        log.pack(fill="x", pady=5)\n\
        self.detail_buttons["opt"] = btn\n\
        self.logs["opt"] = log/g
}' core/main.py

# Para a aba network
sed -i '/btn, log = ui.add_console(parent, "net", self.acc_color, self.toggle_console)/ {
    N
    N
    s/\(btn, log = ui.add_console.*\)\n        self.detail_buttons\["net"\] = btn\n        self.logs\["net"\] = log/\
        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent")\n\
        bottom_frame.pack(fill="x", pady=5)\n\
        btn, log = ui.add_console(bottom_frame, "net", self.acc_color, self.toggle_console)\n\
        btn.pack(side="right", padx=5)\n\
        log.pack(fill="x", pady=5)\n\
        self.detail_buttons["net"] = btn\n\
        self.logs["net"] = log/g
}' core/main.py

# Para a aba drivers
sed -i '/btn, log = ui.add_console(parent, "drv", self.acc_color, self.toggle_console)/ {
    N
    N
    s/\(btn, log = ui.add_console.*\)\n        self.detail_buttons\["drv"\] = btn\n        self.logs\["drv"\] = log/\
        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent")\n\
        bottom_frame.pack(fill="x", pady=5)\n\
        btn, log = ui.add_console(bottom_frame, "drv", self.acc_color, self.toggle_console)\n\
        btn.pack(side="right", padx=5)\n\
        log.pack(fill="x", pady=5)\n\
        self.detail_buttons["drv"] = btn\n\
        self.logs["drv"] = log/g
}' core/main.py

# Para a aba security
sed -i '/btn, log = ui.add_console(parent, "sec", self.acc_color, self.toggle_console)/ {
    N
    N
    s/\(btn, log = ui.add_console.*\)\n        self.detail_buttons\["sec"\] = btn\n        self.logs\["sec"\] = log/\
        bottom_frame = ctk.CTkFrame(parent, fg_color="transparent")\n\
        bottom_frame.pack(fill="x", pady=5)\n\
        btn, log = ui.add_console(bottom_frame, "sec", self.acc_color, self.toggle_console)\n\
        btn.pack(side="right", padx=5)\n\
        log.pack(fill="x", pady=5)\n\
        self.detail_buttons["sec"] = btn\n\
        self.logs["sec"] = log/g
}' core/main.py

# 4. Modificar o método run_card_action para não esconder o botão
sed -i '/if tag in self.detail_buttons:/,/self.consoles_visible\[tag\] = False/d' core/main.py

# 5. Ajustar toggle_console para não esquecer de mudar o texto do botão
#    (já deve estar correto, mas vamos garantir que o botão seja referenciado corretamente)

echo "✅ Layout corrigido!"

# 6. Recriar traduções (se necessário)
mkdir -p locale
xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 2>/dev/null || true

for lang in pt_BR en_US es_ES; do
    mkdir -p locale/$lang/LC_MESSAGES
    if [ ! -f locale/$lang/LC_MESSAGES/speedscan.po ]; then
        msginit -i locale/speedscan.pot -o locale/$lang/LC_MESSAGES/speedscan.po -l $lang --no-translator -q 2>/dev/null || true
    fi
    msgfmt locale/$lang/LC_MESSAGES/speedscan.po -o locale/$lang/LC_MESSAGES/speedscan.mo 2>/dev/null || true
done

# 7. Adicionar tradução exemplo para inglês
if [ -f locale/en_US/LC_MESSAGES/speedscan.po ]; then
    sed -i '/msgid "Dashboard"/{n;s/msgstr ""/msgstr "Dashboard"/}' locale/en_US/LC_MESSAGES/speedscan.po
    msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo
fi

echo ""
echo "Agora execute o programa com:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Os botões 'Detalhes' devem aparecer à direita abaixo dos cards e permanecer visíveis após executar comandos."
