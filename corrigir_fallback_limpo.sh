#!/bin/bash
# Corrige fallback e traduções sem duplicatas

set -e

cd ~/speedscan/speedscan

# Backup do main.py atual (caso algo dê errado)
cp core/main.py core/main.py.bak.$(date +%s)
echo "✅ Backup do main.py criado."

# ============================================================
# 1. Corrigir o fallback usando lambda diretamente
# ============================================================
echo "   + Corrigindo fallback..."

# Remover a definição da função fallback e o self.after anterior
# Vamos substituir todo o bloco de fallback por um único lambda
# Primeiro, encontrar a linha que contém "def fallback()" e apagar até o self.after
# Como é arriscado com sed, vamos usar perl para maior precisão.

perl -i -pe '
    if (/def fallback\(\):/) {
        $_ = "";
        while (<>) {
            last if /self\.after\(10000, fallback\)/;
        }
        $_ = "        self.after(10000, lambda: self._show_detail_button(tag) if not self._btn_shown else None)\n";
    }
' core/main.py

# ============================================================
# 2. Limpar e recriar arquivos .po sem duplicatas
# ============================================================
echo "   + Recriando arquivos .po com traduções básicas..."

# Apagar locale antigo e recriar estrutura
rm -rf locale
mkdir -p locale/pt_BR/LC_MESSAGES locale/en_US/LC_MESSAGES locale/es_ES/LC_MESSAGES

# Função para criar .po com traduções básicas
criar_po() {
    local lang=$1
    local file="locale/${lang}/LC_MESSAGES/speedscan.po"
    cat > "$file" << EOF
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: ${lang}\n"

EOF
    # Adicionar traduções conforme o idioma
    case $lang in
        pt_BR)
            cat >> "$file" << 'EOF'
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
            ;;
        es_ES)
            cat >> "$file" << 'EOF'
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
            ;;
        en_US)
            cat >> "$file" << 'EOF'
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
            ;;
    esac
}

criar_po "pt_BR"
criar_po "es_ES"
criar_po "en_US"

echo "   + Compilando arquivos .mo..."
msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo

echo "✅ Traduções compiladas."

# ============================================================
# 3. Finalizar
# ============================================================
echo ""
echo "🎉 Correções aplicadas!"
echo ""
echo "Execute o programa:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Agora:"
echo "- O erro do fallback deve ter sumido."
echo "- Os títulos das abas devem aparecer traduzidos conforme o idioma selecionado."
