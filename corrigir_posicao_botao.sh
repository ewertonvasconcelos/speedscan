#!/bin/bash
# Ajusta o posicionamento do botão "Detalhes" para o canto direito abaixo dos cards
# e garante que ele só apareça após a execução de um card.

set -e  # Para em caso de erro

cd ~/speedscan/speedscan

# Ativar ambiente virtual (opcional)
source venv/bin/activate 2>/dev/null || true

echo "🔧 Aplicando correção de posicionamento do botão Detalhes..."

# Fazer backup com timestamp
backup_file="core/main.py.bak.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# 1. Adicionar action_mapper se não existir (para DNS)
if ! grep -q "self.action_mapper" core/main.py; then
    echo "   + Adicionando action_mapper..."
    sed -i '/self.action_handler = ActionHandler(self)/a \        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)' core/main.py
fi

# 2. Garantir importação do ActionMapper
if ! grep -q "from core.actions import .*ActionMapper" core/main.py; then
    echo "   + Corrigindo importação..."
    sed -i 's/from core.actions import CommandRunner, ActionHandler/from core.actions import CommandRunner, ActionMapper, ActionHandler/' core/main.py
fi

# 3. Substituir o trecho que empacota o botão em run_card_action para usar side="right"
#    Vamos procurar o bloco onde btn.pack é chamado e substituir pelo comando correto.
#    O bloco atual deve ser algo como:
#        btn.pack(side="right", anchor="e", pady=5, before=self.logs.get(tag) if self.logs.get(tag) else None)
#    Mas se não existir, vamos inserir.
if ! grep -q "btn.pack(side=\"right\"" core/main.py; then
    echo "   + Inserindo pack com side='right' em run_card_action..."
    # Primeiro, remover qualquer pack antigo que possa existir (para evitar duplicação)
    sed -i '/btn.pack(/d' core/main.py
    # Agora inserir o pack correto no lugar certo
    sed -i '/threading.Thread.*run_card_action/ {
        i \        # Mostra o botão de detalhes no canto direito
        i \        btn = self.detail_buttons.get(tag)
        i \        if btn and not btn.winfo_ismapped():
        i \            btn.pack(side="right", anchor="e", padx=10, pady=5, before=self.logs.get(tag) if self.logs.get(tag) else None)
        i 
    }' core/main.py
else
    echo "   + Botão já configurado com side='right'. Verificando âncora..."
    # Garantir que anchor="e" e padx estejam presentes
    sed -i 's/btn.pack(side="right"[^)]*/btn.pack(side="right", anchor="e", padx=10, pady=5, before=self.logs.get(tag) if self.logs.get(tag) else None/' core/main.py
fi

# 4. Garantir que o console (log) seja empacotado com fill="x" e expand=True
#    Isso já deve estar assim em ui.add_console, mas vamos reforçar.
echo "   + Verificando empacotamento do console..."
sed -i 's/log.pack(/log.pack(fill="x", expand=True, /' core/ui.py 2>/dev/null || true

# 5. Recompilar traduções (para garantir)
echo "   + Atualizando traduções..."
mkdir -p locale
if command -v xgettext >/dev/null 2>&1; then
    xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 2>/dev/null || true
    for lang in pt_BR en_US es_ES; do
        mkdir -p locale/$lang/LC_MESSAGES
        if [ ! -f locale/$lang/LC_MESSAGES/speedscan.po ]; then
            msginit -i locale/speedscan.pot -o locale/$lang/LC_MESSAGES/speedscan.po -l $lang --no-translator -q 2>/dev/null || true
        fi
        msgfmt locale/$lang/LC_MESSAGES/speedscan.po -o locale/$lang/LC_MESSAGES/speedscan.mo 2>/dev/null || true
    done
    # Tradução exemplo para inglês (Dashboard)
    if [ -f locale/en_US/LC_MESSAGES/speedscan.po ]; then
        sed -i '/msgid "Dashboard"/{n;s/msgstr ""/msgstr "Dashboard"/}' locale/en_US/LC_MESSAGES/speedscan.po
        msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo
    fi
fi

echo "✅ Correção concluída!"
echo ""
echo "Execute o programa com:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Comportamento esperado:"
echo " - Botões 'Detalhes' aparecem no CANTO DIREITO abaixo dos cards SOMENTE após executar um card."
echo " - O console ocupa toda a largura restante à esquerda do botão."
echo " - A mudança de idioma para Inglês mostra 'Dashboard' traduzido."
