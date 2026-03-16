#!/bin/bash
# Corrige o fallback do botão e adiciona traduções manuais para os títulos das abas

set -e

cd ~/speedscan/speedscan

# Backup
cp core/main.py core/main.py.bak.fallback.$(date +%s)
echo "✅ Backup do main.py criado."

# ============================================================
# 1. Corrigir o fallback (tag não definida)
# ============================================================
echo "   + Corrigindo fallback..."

# Substituir o bloco que cria a função fallback por uma versão que captura tag
# Vamos procurar por "def fallback():" dentro de run_card_action e modificar
# Como é mais seguro, vamos usar perl para substituir todo o trecho do fallback
perl -i -pe 'BEGIN{undef $/;} s/def fallback\(\):\n            if not self\._btn_shown:\n                self\._show_detail_button\(tag\)\n                self\._btn_shown = True\n        self\.after\(10000, fallback\)/def fallback(tag=tag):\n            if not self._btn_shown:\n                self._show_detail_button(tag)\n                self._btn_shown = True\n        self.after(10000, lambda: fallback(tag))/g' core/main.py

# ============================================================
# 2. Adicionar traduções manuais para os títulos principais
# ============================================================
echo "   + Inserindo traduções de exemplo..."

# pt_BR
cat >> locale/pt_BR/LC_MESSAGES/speedscan.po << 'EOF'

msgid "Dashboard"
msgstr "Painel"

msgid "Network"
msgstr "Rede"

msgid "Optimization"
msgstr "Otimização"

msgid "Drivers"
msgstr "Drivers"

msgid "Process Manager"
msgstr "Gerenciador de Processos"

msgid "Historical Performance"
msgstr "Desempenho Histórico"

msgid "System Security"
msgstr "Segurança do Sistema"

msgid "AI Agent"
msgstr "Agente IA"

msgid "Settings"
msgstr "Configurações"

msgid "About"
msgstr "Sobre"

msgid "Windows Cleaner"
msgstr "Limpeza do Windows"
EOF

# es_ES
cat >> locale/es_ES/LC_MESSAGES/speedscan.po << 'EOF'

msgid "Dashboard"
msgstr "Panel"

msgid "Network"
msgstr "Red"

msgid "Optimization"
msgstr "Optimización"

msgid "Drivers"
msgstr "Controladores"

msgid "Process Manager"
msgstr "Administrador de Procesos"

msgid "Historical Performance"
msgstr "Rendimiento Histórico"

msgid "System Security"
msgstr "Seguridad del Sistema"

msgid "AI Agent"
msgstr "Agente IA"

msgid "Settings"
msgstr "Ajustes"

msgid "About"
msgstr "Acerca de"

msgid "Windows Cleaner"
msgstr "Limpiador de Windows"
EOF

# en_US (já está em inglês, mas vamos garantir que as strings existam)
cat >> locale/en_US/LC_MESSAGES/speedscan.po << 'EOF'

msgid "Dashboard"
msgstr "Dashboard"

msgid "Network"
msgstr "Network"

msgid "Optimization"
msgstr "Optimization"

msgid "Drivers"
msgstr "Drivers"

msgid "Process Manager"
msgstr "Process Manager"

msgid "Historical Performance"
msgstr "Historical Performance"

msgid "System Security"
msgstr "System Security"

msgid "AI Agent"
msgstr "AI Agent"

msgid "Settings"
msgstr "Settings"

msgid "About"
msgstr "About"

msgid "Windows Cleaner"
msgstr "Windows Cleaner"
EOF

# ============================================================
# 3. Compilar os arquivos .mo
# ============================================================
echo "   + Compilando arquivos .mo..."
msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo

echo "✅ Traduções de exemplo compiladas."

# ============================================================
# 4. Finalizar
# ============================================================
echo ""
echo "🎉 Correções aplicadas!"
echo ""
echo "Execute o programa:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Agora o botão 'Detalhes' não deve mais causar erro e as traduções"
echo "dos títulos das abas devem funcionar nos três idiomas."
