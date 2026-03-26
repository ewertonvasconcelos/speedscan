#!/bin/bash
# Script direto para testar no container Ubuntu

echo "🚀 Testando SpeedScan..."

# Executar diretamente no container
distrobox enter speedscan-clean -c "
cd /home/ewerton/speedscan/speedscan && source venv/bin/activate && python -m core.main
"

echo "✅ Teste concluído!"
