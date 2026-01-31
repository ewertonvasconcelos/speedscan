#!/bin/bash
echo "======= RELATÓRIO DE SISTEMA ======="
echo "Tempo de atividade: $(uptime -p)"
echo "Memória Livre: $(free -h | awk '/^Mem:/{print $4}')"
echo "===================================="
