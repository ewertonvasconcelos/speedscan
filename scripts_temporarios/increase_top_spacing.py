#!/usr/bin/env python3
"""
Aumenta a distância entre a logo e a primeira aba (Dashboard).
Isso desloca todas as abas para baixo, aproximando a aba Sobre da borda inferior.
Altera o pady superior do center para 60 (ou outro valor) e mantém o inferior em 5.
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
        print("❌ Pasta core não encontrada!")
        return False

def main():
    print("🔧 Ajustando distância superior da sidebar...")

    # Faz backup antes de qualquer modificação
    if not fazer_backup():
        sys.exit(1)

    if not MAIN_FILE.exists():
        print("❌ Arquivo core/main.py não encontrado!")
        sys.exit(1)

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Valor desejado para o pady superior (altere aqui se quiser outro número)
    novo_pady_superior = 70  # Experimente 50, 100, etc.

    # Substitui a linha que define o pack do center
    # Exemplo atual: center.pack(expand=False, fill="x", pady=(38, 5))
    novo_conteudo = re.sub(
        r'(center\.pack\(expand=False, fill="x", pady=)\(\d+,\s*(\d+)\)',
        fr'\g<1>({novo_pady_superior}, \g<2>)',
        content
    )

    if novo_conteudo == content:
        print("⚠️ Nenhuma alteração foi feita. Verifique se a linha existe no formato esperado.")
    else:
        with open(MAIN_FILE, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        print(f"✅ Distância superior ajustada para {novo_pady_superior} pixels.")
        print("▶️ Execute 'python -m core.main' para testar o resultado.")

    print("🧹 Após testar, pode excluir este script.")

if __name__ == "__main__":
    main()
