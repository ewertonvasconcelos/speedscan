#!/usr/bin/env python3
"""
Script para configurar logging do SpeedScan para gravar em arquivo.
Adiciona configuração de logging com RotatingFileHandler no main.py.
Cria backup antes de modificar.
"""

import os
import re
import shutil
from datetime import datetime

def file_has_basic_config(filepath):
    """Verifica se o arquivo já contém logging.basicConfig."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return 'logging.basicConfig' in content

def add_logging_config(filepath):
    """
    Adiciona configuração de logging para arquivo no main.py.
    Assume que o arquivo já contém 'import logging'.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    in_imports = True
    imports_done = False

    # Linhas a adicionar
    config_lines = [
        "\n",
        "# Configuração de logging para arquivo\n",
        "LOG_DIR = Path.home() / \"speedscan\" / \"logs\"\n",
        "LOG_DIR.mkdir(parents=True, exist_ok=True)\n",
        "\n",
        "log_file = LOG_DIR / \"speedscan.log\"\n",
        "handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)\n",
        "formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')\n",
        "handler.setFormatter(formatter)\n",
        "logging.basicConfig(level=logging.ERROR, handlers=[handler])\n",
    ]

    for line in lines:
        new_lines.append(line)
        # Verifica se é uma linha de import
        if in_imports and line.strip().startswith(('import', 'from')):
            continue
        else:
            if in_imports:
                # Terminou os imports, adiciona configuração antes de prosseguir
                in_imports = False
                # Verifica se já não tem a configuração
                if not file_has_basic_config(filepath):
                    # Adiciona import adicional se necessário
                    if 'RotatingFileHandler' not in ''.join(lines):
                        # Adiciona import do RotatingFileHandler
                        new_lines.append("from logging.handlers import RotatingFileHandler\n")
                    new_lines.extend(config_lines)
                    modified = True
                    imports_done = True
    if not imports_done and not file_has_basic_config(filepath):
        # Se o arquivo não tiver imports ou a configuração não foi adicionada, adiciona no final
        new_lines.append("\n")
        new_lines.append("from logging.handlers import RotatingFileHandler\n")
        new_lines.extend(config_lines)
        modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

def ensure_path_import(filepath):
    """Garante que 'from pathlib import Path' exista no arquivo."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'from pathlib import Path' not in content:
        # Adiciona após outros imports
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = []
        added = False
        for line in lines:
            new_lines.append(line)
            if line.strip().startswith(('import', 'from')) and not added:
                # Após o último import, adiciona
                if 'from pathlib import Path' not in line:
                    new_lines.append("from pathlib import Path\n")
                    added = True
        if not added:
            new_lines.insert(0, "from pathlib import Path\n")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    main_py = os.path.join(os.getcwd(), 'core', 'main.py')
    if not os.path.isfile(main_py):
        print("Erro: core/main.py não encontrado.")
        return

    print("Arquivo alvo: core/main.py")
    resposta = input("Criar backup e configurar logging em arquivo? (s/N): ")
    if resposta.lower() != 's':
        print("Operação cancelada.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{main_py}.bak.{timestamp}"
    shutil.copy2(main_py, backup_file)
    print(f"Backup criado: {backup_file}")

    # Garantir que 'from pathlib import Path' exista
    path_added = ensure_path_import(main_py)
    if path_added:
        print("Import 'from pathlib import Path' adicionado.")

    # Adicionar configuração de logging
    modified = add_logging_config(main_py)

    if modified:
        print("Configuração de logging adicionada com sucesso.")
    else:
        print("Arquivo já continha logging.basicConfig. Nenhuma alteração necessária.")

    print("\n✅ Processo concluído. Revise as alterações com 'git diff' antes de commitar.")

if __name__ == '__main__':
    main()
