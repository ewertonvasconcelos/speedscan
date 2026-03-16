#!/bin/bash
# Substitui os métodos toggle_console e run_card_action por versões corrigidas
# e garante a geração das traduções.

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual (opcional)
source venv/bin/activate 2>/dev/null || true

echo "🔧 Aplicando correções nos métodos do main.py..."

# Backup
backup_file="core/main.py.bak.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# Criar um arquivo temporário com as correções
cat > /tmp/main_patch.py << 'EOF'
    # ------------------------------------------------------------------------
    # Card execution and console management (CORRIGIDO)
    # ------------------------------------------------------------------------
    def run_card_action(self, cmd, tag, is_dns):
        log = self.logs.get(tag)
        if not log:
            return
        log.delete("1.0", "end")

        # Se o console estiver visível, escondê-lo e resetar o botão
        btn = self.detail_buttons.get(tag)
        if btn and self.consoles_visible.get(tag, False):
            log.pack_forget()
            btn.configure(text="Details ▼")
            self.consoles_visible[tag] = False

        # Mostra o botão de detalhes no canto direito se ainda não estiver visível
        if btn and not btn.winfo_ismapped():
            btn.pack(side="right", anchor="e", padx=10, pady=5)

        self.consoles_visible[tag] = False
        threading.Thread(target=self._execute_command, args=(cmd, log, tag, is_dns), daemon=True).start()

    def toggle_console(self, tag):
        btn = self.detail_buttons.get(tag)
        log = self.logs.get(tag)
        if not btn or not log:
            return
        if self.consoles_visible.get(tag, False):
            log.pack_forget()
            btn.configure(text="Details ▼")
            self.consoles_visible[tag] = False
        else:
            log.pack(fill="x", expand=True, padx=5, before=btn)
            btn.configure(text="Hide Details ▲")
            self.consoles_visible[tag] = True
EOF

# Agora substituir os métodos no main.py
# Encontra as linhas que definem os métodos e substitui pelo conteúdo do patch

# Primeiro, remover as definições antigas (do começo até o final dos métodos)
# Vamos usar um truque: marcar com um padrão e substituir

# Marcar o início do método run_card_action
sed -i '/def run_card_action/,/def toggle_console/ {
    /def run_card_action/ {
        r /tmp/main_patch.py
        d
    }
    /def toggle_console/!d
}' core/main.py

# Agora remover a definição antiga de toggle_console (se ainda existir)
sed -i '/def toggle_console/,/^    def/ {
    /def toggle_console/ {
        d
    }
    /^    def/!d
}' core/main.py

# Como removemos, precisamos adicionar a nova versão no final do arquivo (ou próximo do local)
# Vamos adicionar no final da classe, antes do if __name__
sed -i '/if __name__ == "__main__":/i \
    # ------------------------------------------------------------------------\
    # Console toggling (CORRIGIDO)\
    # ------------------------------------------------------------------------\
    def toggle_console(self, tag):\
        btn = self.detail_buttons.get(tag)\
        log = self.logs.get(tag)\
        if not btn or not log:\
            return\
        if self.consoles_visible.get(tag, False):\
            log.pack_forget()\
            btn.configure(text="Details ▼")\
            self.consoles_visible[tag] = False\
        else:\
            log.pack(fill="x", expand=True, padx=5, before=btn)\
            btn.configure(text="Hide Details ▲")\
            self.consoles_visible[tag] = True\
\
' core/main.py

echo "✅ Métodos substituídos."

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
echo "Agora o botão 'Detalhes' alternará entre ▼ e ▲ e será resetado ao executar novo card."
