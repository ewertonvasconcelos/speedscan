#!/usr/bin/env python3
"""
Aumenta o espaçamento vertical entre os botões da sidebar.
Altera o valor de pady no pack do frame de cada botão.
Valor atual: 2. Pode ser alterado para 4, 5, 6, etc.
"""

import shutil
import re
import sys
from pathlib import Path
from datetime import datetime

CORE_DIR = Path("core")
MAIN_FILE = CORE_DIR / "main.py"
BACKUP_DIR = Path("backups")

def fazer_backup():
    """Cria um backup da pasta core com timestamp"""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"core_{timestamp}"
    if CORE_DIR.exists():
        shutil.copytree(CORE_DIR, backup_path)
        print(f"✅ Backup criado em: {backup_path}")
        return True
    else:
        print("❌ Pasta core não encontrada! Execute o script da raiz do projeto (onde fica a pasta 'core').")
        return False

def main():
    print("🔧 Aumentando espaçamento entre os botões da sidebar...")

    if not fazer_backup():
        sys.exit(1)

    if not MAIN_FILE.exists():
        print("❌ Arquivo core/main.py não encontrado!")
        sys.exit(1)

    # Defina o novo valor de espaçamento desejado (altere aqui)
    novo_pady = 5  # Experimente 4, 5, 6, etc.

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Substitui a linha que define o pack do frame do botão
    # Padrão atual: frame.pack(pady=2, fill="x", padx=10)
    novo_conteudo = re.sub(
        r'(frame\.pack\(pady=)\d+(, fill="x", padx=10\))',
        fr'\g<1>{novo_pady}\g<2>',
        content
    )

    if novo_conteudo == content:
        print("⚠️ Nenhuma alteração foi feita. Verifique se a linha 'frame.pack(pady=2, fill=\"x\", padx=10)' existe.")
    else:
        with open(MAIN_FILE, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        print(f"✅ Espaçamento entre botões ajustado para {novo_pady} pixels.")
        print("▶️ Execute 'python -m core.main' para testar o resultado.")

    print("🧹 Após testar, pode excluir este script.")

if __name__ == "__main__":
    main()
