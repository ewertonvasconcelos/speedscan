#!/bin/bash
# Corrige:
# - Botão Detalhes: seta para baixo/para cima e esconde console ao executar novo card
# - Gera arquivos de tradução para pt_BR, en_US, es_ES

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual (opcional)
source venv/bin/activate 2>/dev/null || true

echo "🔧 Aplicando correções de comportamento..."

# Fazer backup do main.py
backup_file="core/main.py.bak.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# 1. Modificar toggle_console para alterar texto do botão
sed -i '/def toggle_console/,/^    def/ {
    /if self.consoles_visible.get(tag, False):/,/else:/ {
        s/log.pack_forget()/log.pack_forget()\n            btn.configure(text="Details ▼")/
        s/log.pack(.*before=btn)/log.pack(fill="x", expand=True, padx=5, before=btn)\n            btn.configure(text="Hide Details ▲")/
    }
}' core/main.py

# 2. Adicionar ocultação do console ao executar novo card em run_card_action
#    Procuramos a linha onde o botão é empacotado e inserimos antes
sed -i '/if btn and not btn.winfo_ismapped():/ {
    i \        # Se o console estiver visível, escondê-lo e resetar o botão
    i \        if tag in self.consoles_visible and self.consoles_visible[tag]:
    i \            log.pack_forget()
    i \            btn.configure(text="Details ▼")
    i \            self.consoles_visible[tag] = False
    i 
}' core/main.py

echo "✅ Código do botão corrigido."

# 3. Gerar arquivos de tradução
echo "🌐 Gerando traduções..."

# Verificar se gettext está instalado
if ! command -v msgfmt >/dev/null 2>&1; then
    echo "⚠️  msgfmt não encontrado. Instale gettext com: sudo apt install gettext"
    exit 1
fi

mkdir -p locale

# Extrair strings (se necessário)
if [ ! -f locale/speedscan.pot ]; then
    xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 2>/dev/null || true
fi

# Função para criar/atualizar .po e .mo
criar_idioma() {
    local lang=$1
    local dir="locale/${lang}/LC_MESSAGES"
    mkdir -p "$dir"
    if [ ! -f "${dir}/speedscan.po" ]; then
        echo "   - Criando .po para ${lang}..."
        msginit -i locale/speedscan.pot -o "${dir}/speedscan.po" -l "$lang" --no-translator -q 2>/dev/null || true
    fi
    # Compilar .mo
    echo "   - Compilando .mo para ${lang}..."
    msgfmt "${dir}/speedscan.po" -o "${dir}/speedscan.mo" 2>/dev/null || true
}

criar_idioma "pt_BR"
criar_idioma "en_US"
criar_idioma "es_ES"

# Adicionar tradução de exemplo para inglês (opcional)
if [ -f locale/en_US/LC_MESSAGES/speedscan.po ]; then
    sed -i '/msgid "Dashboard"/{n;s/msgstr ""/msgstr "Dashboard"/}' locale/en_US/LC_MESSAGES/speedscan.po
    msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo
fi

echo "✅ Traduções geradas."

echo ""
echo "🎉 Correções aplicadas!"
echo "Execute o programa com:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Agora o botão 'Detalhes' terá seta para baixo ▼ (fechado) e para cima ▲ (aberto)."
echo "Ao executar um novo card, o console anterior será fechado automaticamente."
echo "As opções de idioma devem funcionar (pt_BR, en_US, es_ES)."
