#!/usr/bin/env python3
"""
Ajuste final de espaçamento:
- Reduz pady inferior do center para 5 (antes era 38 ou 15)
- Reduz altura mínima da janela para 500 (antes 550)
- Faz backup automático da pasta core
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
    print("🔧 Aplicando ajuste final de espaçamento...")

    # Backup
    if not fazer_backup():
        sys.exit(1)

    if not MAIN_FILE.exists():
        print("❌ Arquivo core/main.py não encontrado!")
        sys.exit(1)

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Alterar pady do center para (38, 5)
    novo_conteudo = re.sub(
        r'(center\.pack\(expand=False, fill="x", pady=)\(38,\s*\d+\)',
        r'\g<1>(38, 5)',
        content
    )

    # 2. Alterar minsize para 900x500
    novo_conteudo = re.sub(
        r'self\.minsize\(900,\s*\d+\)',
        'self.minsize(900, 500)',
        novo_conteudo
    )

    if novo_conteudo == content:
        print("⚠️ Nenhuma alteração foi feita. Verifique se as linhas existem:")
        print('   - center.pack(expand=False, fill="x", pady=(38, ...))')
        print('   - self.minsize(900, 550)')
    else:
        with open(MAIN_FILE, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        print("✅ Ajustes aplicados:")
        print("   - pady inferior do center = 5")
        print("   - altura mínima da janela = 500")
        print("▶️ Execute 'python -m core.main' para testar.")

    print("🧹 Após testar, pode excluir este script.")

if __name__ == "__main__":
    main()
