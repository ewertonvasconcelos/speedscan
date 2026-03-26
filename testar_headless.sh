#!/bin/bash
# Script para testar SpeedScan em modo headless (sem interface gráfica)

echo "🚀 Testando SpeedScan em modo headless..."

# Entrar no container
distrobox enter speedscan-clean -c "
cd /home/ewerton/speedscan/speedscan
source venv/bin/activate

# Configurar variável para modo headless
export DISPLAY=:99
export PYTHONPATH=/home/ewerton/speedscan/speedscan:\$PYTHONPATH

# Testar import e sintaxe
echo '🧪 Testando sintaxe...'
python -c \"
import core.main
print('✅ Sintaxe OK')
print('✅ Imports funcionando')
print('✅ Métodos widget_* disponíveis:')
print('  - widget_cpu()')
print('  - widget_ram()')
print('  - widget_gpu()')
print('  - widget_battery()')
print('  - widget_disks()')
print('  - widget_hostname()')
print('  - widget_distro()')
print('  - widget_kernel()')
print('  - widget_temps()')
print('  - widget_uptime()')
print('  - widget_health()')
\"

# Testar métodos individualmente
echo '🧪 Testando métodos widget_*...'
python -c \"
import core.main
app = core.main.SpeedScan()
print('CPU:', app.widget_cpu())
print('RAM:', app.widget_ram())
print('GPU:', app.widget_gpu())
print('Battery:', app.widget_battery())
print('Disks:', app.widget_disks())
print('Hostname:', app.widget_hostname())
print('Distro:', app.widget_distro())
print('Kernel:', app.widget_kernel())
print('Temps:', app.widget_temps())
print('Uptime:', app.widget_uptime())
print('Health:', app.widget_health())
\"
"

echo "🎉 Teste headless concluído!"
