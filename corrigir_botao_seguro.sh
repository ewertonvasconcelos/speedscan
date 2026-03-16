#!/bin/bash
# Corrige action_mapper e posicionamento do botão sem quebrar as abas

set -e

cd /app/speedscan/speedscan

echo "🔧 Aplicando correções seguras..."

# 1. Adicionar action_mapper se não existir
if ! grep -q "self.action_mapper" core/main.py; then
    echo "   + Adicionando action_mapper..."
    sed -i '/self.action_handler = ActionHandler(self)/a \        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)' core/main.py
fi

# 2. Garantir importação do ActionMapper
if ! grep -q "from core.actions import .*ActionMapper" core/main.py; then
    echo "   + Corrigindo importação..."
    sed -i 's/from core.actions import CommandRunner, ActionHandler/from core.actions import CommandRunner, ActionMapper, ActionHandler/' core/main.py
fi

# 3. Inserir o pack do botão no lugar correto (run_card_action) com side="right"
#    Primeiro, remover qualquer pack antigo que possa existir
sed -i '/btn.pack(/d' core/main.py

#    Agora inserir o novo pack dentro de run_card_action (após obter o log)
sed -i '/log = self.logs.get(tag)/ {
    n
    i \        # Mostra o botão de detalhes no canto direito se não estiver visível
    i \        btn = self.detail_buttons.get(tag)
    i \        if btn and not btn.winfo_ismapped():
    i \            btn.pack(side="right", anchor="e", padx=10, pady=5)
    i 
}' core/main.py

echo "✅ Correções aplicadas!"
echo "Agora saia do container (exit) e execute no host:"
echo "   cd ~/speedscan/speedscan"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
