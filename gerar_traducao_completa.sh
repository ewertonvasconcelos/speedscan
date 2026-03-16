#!/bin/bash
# Passo 2: Extrair todas as strings e criar .po para pt_BR e es_ES

set -e

cd ~/speedscan/speedscan

# Backup dos .po existentes (se houver)
if [ -d locale ]; then
    mv locale locale.bak.$(date +%s)
fi

mkdir -p locale

echo "🔍 Extraindo strings do código..."
xgettext -d speedscan -o locale/speedscan.pot core/*.py --from-code=UTF-8 --keyword=_ 2>/dev/null || true

echo "🌐 Criando arquivo .po para pt_BR..."
msginit -i locale/speedscan.pot -o locale/pt_BR.po -l pt_BR --no-translator

echo "🌐 Criando arquivo .po para es_ES..."
msginit -i locale/speedscan.pot -o locale/es_ES.po -l es_ES --no-translator

# Mover para as pastas LC_MESSAGES (estrutura correta)
mkdir -p locale/pt_BR/LC_MESSAGES locale/es_ES/LC_MESSAGES
mv locale/pt_BR.po locale/pt_BR/LC_MESSAGES/speedscan.po
mv locale/es_ES.po locale/es_ES/LC_MESSAGES/speedscan.po

# (Opcional) Copiar o mesmo para en_US, se não existir
if [ ! -f locale/en_US/LC_MESSAGES/speedscan.po ]; then
    mkdir -p locale/en_US/LC_MESSAGES
    cp locale/speedscan.pot locale/en_US/LC_MESSAGES/speedscan.po
fi

echo "✅ Arquivos .po gerados em:"
echo "   locale/pt_BR/LC_MESSAGES/speedscan.po"
echo "   locale/es_ES/LC_MESSAGES/speedscan.po"
echo "   locale/en_US/LC_MESSAGES/speedscan.po (cópia do template)"
