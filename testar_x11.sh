#!/bin/bash
# Script para testar SpeedScan com suporte X11

echo "🚀 Configurando ambiente X11 para SpeedScan..."

# Entrar no container com suporte X11
export DISPLAY=$DISPLAY
export XAUTHORITY=$XAUTHORITY

distrobox enter speedscan-clean -c "
# Configurar variáveis de ambiente
export DISPLAY=unix\$DISPLAY
export XDG_RUNTIME_DIR=/tmp/runtime-1000
export XDG_SESSION_TYPE=x11

# Criar diretório se não existir
mkdir -p /tmp/.X11-unix

# Ir para o projeto
cd /home/ewerton/speedscan/speedscan

# Ativar ambiente virtual
source venv/bin/activate

# Testar se X11 está disponível
echo '🧪 Testando ambiente gráfico...'
xset q 2>/dev/null && echo '✅ X11 disponível' || echo '⚠️ X11 não configurado'

# Executar SpeedScan com tratamento de erro
echo '🚀 Iniciando SpeedScan...'
python -m core.main 2>&1 || echo '❌ Erro na execução'
"

echo "🎉 Teste concluído!"
