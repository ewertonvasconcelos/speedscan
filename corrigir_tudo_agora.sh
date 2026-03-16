#!/bin/bash
# Script final: corrige botão Detalhes e gera traduções completas

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual (se existir)
[ -d "venv" ] && source venv/bin/activate

echo "🔧 Iniciando correção final e tradução automática..."

# ============================================================
# 1. Backup do main.py atual
# ============================================================
cp core/main.py core/main.py.bak.ultimo.$(date +%s)
echo "✅ Backup do main.py criado."

# ============================================================
# 2. Remover qualquer fallback e ajustar botão
# ============================================================
echo "   + Corrigindo botão Detalhes..."

# Remove qualquer função fallback e chamada self.after
perl -i -0777 -pe 's/def fallback\(\):.*?self\.after\(\d+,.*?\)//gs' core/main.py

# Garante que a variável _btn_shown exista e seja resetada
if ! grep -q "self._btn_shown" core/main.py; then
    sed -i '/self.consoles_visible = {}/a \        self._btn_shown = False' core/main.py
fi

# Reseta _btn_shown no início de run_card_action
sed -i '/def run_card_action/,/threading.Thread/ {
    /log.delete/a \        self._btn_shown = False
}' core/main.py

# Garante que _show_detail_button exista
if ! grep -q "def _show_detail_button" core/main.py; then
    sed -i '/def run_card_action/i \    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)\n' core/main.py
fi

# Modifica _run_subprocess para mostrar botão apenas na primeira saída
sed -i '/for line in proc.stdout:/i \            if not self._btn_shown:\n                self._show_detail_button(tag)\n                self._btn_shown = True' core/main.py

# Ajusta toggle_console para que ao fechar, o botão suma
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

echo "   ✅ Botão corrigido."

# ============================================================
# 3. Verificar/instalar deep-translator
# ============================================================
if ! python -c "import deep_translator" 2>/dev/null; then
    echo "   + Instalando deep-translator..."
    pip install deep-translator
fi

# ============================================================
# 4. Gerar traduções automáticas com Python
# ============================================================
echo "🌐 Gerando traduções automáticas (pode levar alguns minutos)..."

# Criar script Python temporário
cat > traduzir_po.py << 'EOF'
#!/usr/bin/env python3
import sys
import re
from deep_translator import GoogleTranslator

def traduzir_arquivo(po_path, idioma_destino):
    with open(po_path, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    translator = GoogleTranslator(source='en', target=idioma_destino)
    novas_linhas = []
    msgid_atual = None
    linha_msgid = None

    for i, linha in enumerate(linhas):
        if linha.startswith('msgid "') and not linha.startswith('msgid ""'):
            # Extrai o texto entre aspas
            match = re.search(r'msgid "(.*)"', linha)
            if match:
                msgid_atual = match.group(1)
                linha_msgid = i
            novas_linhas.append(linha)
        elif linha.startswith('msgstr "') and msgid_atual is not None:
            if linha == 'msgstr ""\n' and msgid_atual.strip():
                # Traduz apenas se msgstr estiver vazia
                try:
                    traducao = translator.translate(msgid_atual)
                    # Escapa aspas duplas
                    traducao = traducao.replace('"', '\\"')
                    novas_linhas.append(f'msgstr "{traducao}"\n')
                    print(f'Traduzido: {msgid_atual[:40]}... -> {traducao[:40]}...')
                except Exception as e:
                    print(f'Erro ao traduzir "{msgid_atual}": {e}')
                    novas_linhas.append(linha)
            else:
                novas_linhas.append(linha)
            msgid_atual = None
        else:
            novas_linhas.append(linha)

    with open(po_path, 'w', encoding='utf-8') as f:
        f.writelines(novas_linhas)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python traduzir_po.py <arquivo.po> <idioma>")
        sys.exit(1)
    traduzir_arquivo(sys.argv[1], sys.argv[2])
EOF

# Traduzir pt_BR
if [ -f locale/pt_BR/LC_MESSAGES/speedscan.po ]; then
    echo "   + Traduzindo para português..."
    python traduzir_po.py locale/pt_BR/LC_MESSAGES/speedscan.po pt
else
    echo "   ⚠️ Arquivo pt_BR não encontrado. Pulando."
fi

# Traduzir es_ES
if [ -f locale/es_ES/LC_MESSAGES/speedscan.po ]; then
    echo "   + Traduzindo para espanhol..."
    python traduzir_po.py locale/es_ES/LC_MESSAGES/speedscan.po es
else
    echo "   ⚠️ Arquivo es_ES não encontrado. Pulando."
fi

# Opcional: en_US (já em inglês, não precisa traduzir)
echo "   + Mantendo en_US como original."

# ============================================================
# 5. Compilar os arquivos .mo
# ============================================================
echo "   + Compilando arquivos .mo..."
msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo 2>/dev/null || echo "   ⚠️ Falha ao compilar pt_BR (pode não ter traduções)"
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo 2>/dev/null || echo "   ⚠️ Falha ao compilar es_ES"
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo 2>/dev/null || echo "   ⚠️ Falha ao compilar en_US"

# ============================================================
# 6. Limpeza
# ============================================================
rm -f traduzir_po.py

echo ""
echo "🎉 Tudo concluído!"
echo ""
echo "Agora execute o programa:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Teste o botão Detalhes:"
echo "- Clique em um card sem senha → botão aparece imediatamente."
echo "- Clique em um card com senha → botão só aparece após autenticação."
echo "- Cancele a senha → botão NÃO aparece."
echo "- Clique no botão para abrir/fechar → ao fechar, o botão some."
echo "- Execute outro card → o processo recomeça."
echo ""
echo "As traduções devem estar completas (pode haver pequenas imperfeições,"
echo "pois são automáticas). Se quiser ajustar, edite os arquivos .po com Poedit."
