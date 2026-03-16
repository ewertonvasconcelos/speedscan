#!/bin/bash
# Remove fallback e garante que botão só apareça na primeira saída real

set -e

cd ~/speedscan/speedscan

# Backup do main.py atual
cp core/main.py core/main.py.bak.antes_sem_fallback
echo "✅ Backup criado."

echo "🔧 Removendo fallback e ajustando lógica do botão..."

# Remove qualquer bloco de fallback (função fallback e self.after)
perl -i -0777 -pe 's/def fallback\(\):.*?self\.after\(\d+, fallback\)//s' core/main.py

# Adiciona a variável _btn_shown no __init__ se não existir
if ! grep -q "self._btn_shown" core/main.py; then
    sed -i '/self.consoles_visible = {}/a \        self._btn_shown = False' core/main.py
    echo "   + Variável _btn_shown adicionada."
fi

# Modifica run_card_action para resetar _btn_shown no início
sed -i '/def run_card_action/,/threading.Thread/ {
    /log.delete/a \        self._btn_shown = False
}' core/main.py
echo "   + _btn_shown resetado a cada execução."

# Garante que _run_subprocess chame _show_detail_button apenas na primeira linha de saída
sed -i '/for line in proc.stdout:/i \            if not self._btn_shown:\n                self._show_detail_button(tag)\n                self._btn_shown = True' core/main.py
echo "   + Botão ativado apenas na primeira saída."

echo "✅ Correções concluídas."
echo ""
echo "Agora o botão 'Detalhes' só aparecerá quando o comando produzir saída real."
echo "Se o usuário cancelar a senha (ou o comando falhar sem saída), o botão NÃO aparecerá."
