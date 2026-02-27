cat core/speedscan_app.py
#!/usr/bin/env python3
# speedscan-agent.py - Executa as tarefas agendadas do SpeedScan em segundo plano

import os
import sys
import json
import subprocess
import logging
from datetime import datetime

CONFIG_FILE = os.path.expanduser("~/.speedscan_conf")
LOG_DIR = os.path.expanduser("~/speedscan/logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configura o logger
log_file = os.path.join(LOG_DIR, f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Carrega a configuração do arquivo"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def run_action(cmd, elevated=False):
    """Executa um comando, com elevação se necessário"""
    full_cmd = cmd
    if elevated and sys.platform == "linux":
        full_cmd = f"pkexec bash -c '{cmd}'"
    # No Windows, schtasks já pode estar configurado com privilégios
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=300)
        logging.info(f"Comando: {cmd}\nSaída: {result.stdout}\nErro: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Erro ao executar {cmd}: {e}")
        return False

def main():
    logging.info("Iniciando execução agendada do SpeedScan")
    config = load_config().get("schedule", {})
    if not config.get("enabled"):
        logging.info("Agendamento desabilitado. Saindo.")
        return

    tasks = config.get("tasks", [])
    elevated = config.get("elevated", False)

    for task in tasks:
        logging.info(f"Executando tarefa: {task}")
        if task == "cache":
            run_action("sudo eopkg dc && sudo eopkg clean", elevated)
        elif task == "swap":
            run_action("sudo swapoff -a && sudo swapon -a", elevated)
        elif task == "check":
            run_action("sudo eopkg check", elevated)
        elif task == "update":
            # Detectar distribuição
            if os.path.exists("/etc/eopkg/repositories"):  # Solus
                run_action("sudo eopkg upgrade -y", elevated)
            elif os.path.exists("/etc/debian_version"):
                run_action("sudo apt update && sudo apt upgrade -y", elevated)
            elif os.path.exists("/etc/redhat-release"):
                run_action("sudo dnf upgrade -y", elevated)
            else:
                logging.warning(f"Atualização não suportada para esta distribuição")
        elif task == "turbo":
            # Modo turbo temporário – requer cuidado
            logging.warning("Modo turbo automático não implementado")
        else:
            logging.warning(f"Tarefa desconhecida: {task}")

    logging.info("Execução agendada concluída")

if __name__ == "__main__":
    main()

