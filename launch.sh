#!/bin/bash
# SpeedScan Launcher - Script para rodar no ambiente correto
echo "🚀 SpeedScan Launcher v1.0"
echo "Detectando ambiente..."

# Verificar se estamos no KDE Linux
if [ -f /etc/os-release ] && grep -q "ID=kde-linux" /etc/os-release; then
    echo "⚠️  Detectado KDE Linux - ambiente com restrições GLIBC"
    
    # Tentar usar display do host para aplicações gráficas
    if [ -n "$WAYLAND_DISPLAY" ]; then
        echo "📺 Usando Wayland: $WAYLAND_DISPLAY"
        export GDK_BACKEND=wayland
        export QT_QPA_PLATFORM=wayland
    elif [ -n "$DISPLAY" ]; then
        echo "📺 Usando X11: $DISPLAY"
        export GDK_BACKEND=x11
        export QT_QPA_PLATFORM=xcb
    fi
    
    # Executar SpeedScan com Python do sistema
    echo "🚀 Iniciando SpeedScan com Python do sistema..."
    cd /home/ewerton/speedscan/speedscan
    
    # Configurar variáveis para evitar conflitos
    export PYTHONNOUSERSITE=1
    export PYTHONPATH="/home/ewerton/speedscan/speedscan:$PYTHONPATH"
    
    # Executar com tratamento de erro
    python3 -m core.main 2>&1
    
else
    echo "✅ Ambiente padrão detectado - executando normalmente"
    cd /home/ewerton/speedscan/speedscan
    source venv/bin/activate
    python -m core.main
fi

echo "🏁 SpeedScan encerrado"
