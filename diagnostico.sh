#!/bin/bash
# Diagnóstico do SpeedScan

cd ~/speedscan/speedscan
source venv/bin/activate

echo "=== VERIFICANDO ARQUIVOS DE TRADUÇÃO ==="
ls -la locale/
echo ""

echo "=== VERIFICANDO CONFIGURAÇÃO DE IDIOMA ==="
cat ~/.speedscan_config | grep language
echo ""

echo "=== EXECUTANDO PROGRAMA COM LOGS ==="
python3 -m core.main
