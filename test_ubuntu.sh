#!/bin/bash
# Script para testar SpeedScan no container Ubuntu limpo

echo "🚀 Entrando no container Ubuntu speedscan-clean..."

# Entrar no container Ubuntu
distrobox enter speedscan-clean << 'EOF'
echo "✅ Dentro do container Ubuntu"
echo "📍 Diretório atual: $(pwd)"

# Ir para o projeto
cd /home/ewerton/speedscan/speedscan
echo "📁 Navegando para: $(pwd)"

# Clonar/atualizar o projeto
if [ ! -d ".git" ]; then
    echo "📥 Clonando repositório..."
    git clone https://github.com/ewertonvasconcelos/speedscan.git temp_speedscan
    cp -r temp_speedscan/* .
    rm -rf temp_speedscan
else
    echo "🔄 Atualizando repositório..."
    git pull origin master
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🐍 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências..."
pip install customtkinter psutil matplotlib requests speedtest-cli pillow

# Testar import
echo "🧪 Testando import do tkinter..."
python -c "import tkinter; print('✅ Tkinter funcionando!')"

# Executar SpeedScan
echo "🚀 Iniciando SpeedScan..."
python -m core.main

echo "🏁 SpeedScan encerrado"
EOF

echo "🎉 Teste concluído!"
