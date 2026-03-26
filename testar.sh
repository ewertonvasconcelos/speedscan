#!/bin/bash
# Script simplificado para testar SpeedScan no container Ubuntu

echo "🚀 Testando SpeedScan no container Ubuntu speedscan-clean..."

# Entrar no container e executar comandos
distrobox enter speedscan-clean -c "
cd /home/ewerton/speedscan/speedscan

# Clonar/atualizar repositório
if [ ! -d '.git' ]; then
    git clone https://github.com/ewertonvasconcelos/speedscan.git temp_repo
    cp -r temp_repo/* .
    rm -rf temp_repo
else
    git pull origin master
fi

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install customtkinter psutil matplotlib requests speedtest-cli pillow

# Testar import
python -c 'import tkinter; print(\"✅ Tkinter OK\")'

# Executar SpeedScan
echo '🚀 Iniciando SpeedScan...'
python -m core.main
"

echo "🎉 Teste concluído!"
