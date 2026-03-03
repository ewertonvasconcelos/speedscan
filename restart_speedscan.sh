#!/bin/bash
# Script de reinicialização do SpeedScan
# Versão 0.3.0-beta

PARENT_PID=$1

while kill -0 "$PARENT_PID" 2>/dev/null; do
    sleep 0.1
done

cd "$HOME/speedscan"
source speedscan-venv/bin/activate
python -m core.main

