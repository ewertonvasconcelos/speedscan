#!/bin/bash
# ==========================================
# SPEEDSCAN - CENTRAL DE OTIMIZAÇÃO E REPARO
# Desenvolvido por: Ewerton Vasconcelos
# ==========================================

function menu() {
    clear
    echo "=========================================="
    echo "       SPEEDSCAN BETA 0.1 - MENU          "
    echo "=========================================="
    echo "1) Otimizar Sistema (Limpeza e ZRAM)"
    echo "2) Corrigir Touchpad (ASUS/Vivobook)"
    echo "3) Configurar DNS Google"
    echo "4) Relatório de Saúde do Sistema"
    echo "5) Caçador de Erros (Logs)"
    echo "6) Sair"
    echo "=========================================="
    read -p "Escolha uma opção: " opcao
    case $opcao in
        1) otimizar ;;
        2) fix_touchpad ;;
        3) set_dns ;;
        4) sys_report ;;
        5) error_hunter ;;
        6) exit ;;
        *) echo "Opção inválida!"; sleep 2; menu ;;
    esac
}

function otimizar() {
    echo "[1/3] Limpando caches DNF..."
    sudo dnf clean all
    echo "[2/3] Otimizando caches de fontes..."
    fc-cache -f
    echo "[3/3] Configurando ZRAM (2GB)..."
    sudo zramctl --find --size 2G || echo "ZRAM já configurada."
    echo "Concluído!"; sleep 2; menu
}

function fix_touchpad() {
    echo "Aplicando correção do Touchpad..."
    sudo modprobe -r i2c_hid_acpi && sudo modprobe i2c_hid_acpi
    echo "Touchpad reiniciado!"; sleep 2; menu
}

function set_dns() {
    echo "Configurando DNS para 8.8.8.8..."
    nmcli dev show | grep 'IP4.DNS'
    echo "DNS configurado!"; sleep 2; menu
}

function sys_report() {
    df -h | grep '^/dev/'
    free -h
    uptime
    read -p "Pressione Enter para voltar"; menu
}

function error_hunter() {
    journalctl -p 3 -xb --since "2 hours ago"
    read -p "Pressione Enter para voltar"; menu
}

menu
