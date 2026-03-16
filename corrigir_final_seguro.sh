#!/bin/bash
# Restaura o backup mais recente e aplica apenas a correção de posicionamento do botão

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual (opcional)
source venv/bin/activate 2>/dev/null || true

echo "🔍 Procurando o backup mais recente..."

# Encontrar o backup mais recente (ordenar por data, pegar o último)
latest_backup=$(ls -t core/main.py.bak.* 2>/dev/null | head -1)

if [ -z "$latest_backup" ]; then
    echo "❌ Nenhum backup encontrado. Abortando."
    exit 1
fi

echo "✅ Restaurando $latest_backup para core/main.py"
cp "$latest_backup" core/main.py

echo "🔧 Aplicando correção de posicionamento do botão..."

# Adicionar action_mapper se não existir (necessário para DNS)
if ! grep -q "self.action_mapper" core/main.py; then
    echo "   + Adicionando action_mapper..."
    sed -i '/self.action_handler = ActionHandler(self)/a \        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)' core/main.py
fi

# Garantir importação do ActionMapper
if ! grep -q "from core.actions import .*ActionMapper" core/main.py; then
    echo "   + Corrigindo importação..."
    sed -i 's/from core.actions import CommandRunner, ActionHandler/from core.actions import CommandRunner, ActionMapper, ActionHandler/' core/main.py
fi

# Modificar run_card_action para posicionar o botão à direita (somente se ainda não estiver)
if ! grep -q "btn.pack(side=\"right\"" core/main.py; then
    echo "   + Inserindo pack com side='right' em run_card_action..."
    # Primeiro, remover qualquer pack antigo que possa existir (mas preservar o resto)
    sed -i '/btn.pack(/d' core/main.py
    # Agora inserir o pack correto dentro de run_card_action
    sed -i '/threading.Thread.*run_card_action/ {
        i \        # Mostra o botão de detalhes no canto direito
        i \        btn = self.detail_buttons.get(tag)
        i \        if btn and not btn.winfo_ismapped():
        i \            btn.pack(side="right", anchor="e", padx=10, pady=5)
        i 
    }' core/main.py
else
    echo "   + Botão já configurado com side='right'."
fi

echo "✅ Correção concluída!"
echo ""
echo "Execute o programa com:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Agora o botão 'Detalhes' deve aparecer no canto direito após executar um card."
