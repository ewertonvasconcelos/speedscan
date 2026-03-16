#!/bin/bash
# Script para corrigir de uma vez todos os problemas do SpeedScan
# Executar no diretório raiz do projeto (onde fica a pasta core/)

set -e  # Para em caso de erro

echo "🔧 Iniciando correção do SpeedScan..."

# 1. Verificar se está no diretório correto
if [ ! -d "core" ]; then
    echo "❌ Erro: execute este script dentro da pasta que contém a subpasta 'core/'"
    exit 1
fi

# 2. Ativar ambiente virtual (criar se não existir)
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Instalar/atualizar dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install customtkinter psutil matplotlib requests speedtest-cli pillow

# 4. Verificar Tkinter (necessário para CustomTkinter)
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "🖥️ Instalando python3-tk (será pedida a senha sudo)..."
    sudo apt update && sudo apt install -y python3-tk
fi

# 5. Corrigir main.py: adicionar action_mapper se não existir
echo "🔧 Verificando main.py..."
if ! grep -q "self.action_mapper" core/main.py; then
    echo "   - Adicionando action_mapper..."
    # Faz backup
    cp core/main.py core/main.py.bak
    # Insere a linha após a criação do action_handler
    sed -i '/self.action_handler = ActionHandler(self)/a \        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)' core/main.py
else
    echo "   - action_mapper já presente."
fi

# 6. Garantir que a importação do ActionMapper existe
if ! grep -q "from core.actions import .*ActionMapper" core/main.py; then
    echo "   - Corrigindo importação do ActionMapper..."
    sed -i 's/from core.actions import CommandRunner, ActionHandler/from core.actions import CommandRunner, ActionMapper, ActionHandler/' core/main.py
fi

# 7. Criar diretório locale e gerar arquivos de tradução (se não existirem)
echo "🌐 Configurando internacionalização..."
mkdir -p locale

if [ ! -f "locale/speedscan.pot" ]; then
    echo "   - Extraindo strings..."
    xgettext -d speedscan -o locale/speedscan.pot core/*.py
fi

# Função para criar .po e .mo para um idioma
criar_idioma() {
    local lang=$1
    local locale_dir="locale/${lang}/LC_MESSAGES"
    mkdir -p "$locale_dir"
    if [ ! -f "${locale_dir}/speedscan.po" ]; then
        echo "   - Criando arquivo .po para ${lang}..."
        msginit -i locale/speedscan.pot -o "${locale_dir}/speedscan.po" -l "${lang}" --no-translator -q
    fi
    # Compilar .mo (se o .po existir)
    if [ -f "${locale_dir}/speedscan.po" ]; then
        echo "   - Compilando .mo para ${lang}..."
        msgfmt "${locale_dir}/speedscan.po" -o "${locale_dir}/speedscan.mo"
    fi
}

# Criar para pt_BR, en_US, es_ES
criar_idioma "pt_BR"
criar_idioma "en_US"
criar_idioma "es_ES"

# 8. Adicionar uma tradução de exemplo para inglês (para teste)
echo "   - Adicionando tradução exemplo para 'Dashboard' em inglês..."
PO_EN="locale/en_US/LC_MESSAGES/speedscan.po"
if [ -f "$PO_EN" ]; then
    # Substituir a linha msgstr "Dashboard" se existir
    sed -i '/msgid "Dashboard"/{n;s/msgstr ""/msgstr "Dashboard"/}' "$PO_EN"
    msgfmt "$PO_EN" -o "locale/en_US/LC_MESSAGES/speedscan.mo"
fi

# 9. Ajustar permissões para pkexec (opcional, mas pode ajudar)
echo "🔐 Verificando pkexec..."
if command -v pkexec >/dev/null 2>&1; then
    echo "   - pkexec está disponível."
else
    echo "   ⚠️ pkexec não encontrado. Comandos com sudo podem não abrir janela gráfica."
fi

echo ""
echo "✅ Correção concluída!"
echo ""
echo "Agora execute o programa com:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Teste:"
echo "  - Aba Rede → clique em 'Cloudflare DNS' (deve aparecer mensagem no console)"
echo "  - Configurações → mude o idioma para 'English (US)' e reinicie (agora 'Dashboard' deve aparecer em inglês)"
