#!/bin/bash
# Script de reinicialização do SpeedScan
# Opção C: aguarda o processo pai morrer e reinicia

# Pega o PID do processo pai (SpeedScan)
PARENT_PID=$1

# Aguarda até que o processo pai não exista mais
while kill -0 "$PARENT_PID" 2>/dev/null; do
    sleep 0.1
done

# Reinicia o aplicativo com o mesmo ambiente
cd "$HOME/speedscan"
source speedscan-venv/bin/activate
python -m core.main
