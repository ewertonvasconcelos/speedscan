#!/usr/bin/env python3
"""
Ajusta o espaçamento inferior da sidebar para aproximar a aba Sobre da borda inferior.
Altera o pady do center de (38,38) para (38,15).
"""

import shutil
import re
from pathlib import Path

MAIN_FILE = Path("core/main.py")
BACKUP_FILE = Path("core/main.py.bak.spacing")

def main():
    print("🔧 Ajustando espaçamento inferior da sidebar...")

    if not MAIN_FILE.exists():
        print("❌ Arquivo core/main.py não encontrado!")
        return

    shutil.copy(MAIN_FILE, BACKUP_FILE)
    print(f"✅ Backup criado: {BACKUP_FILE}")

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Substituir a linha que contém center.pack com pady=(38,38)
    # Padrão: center.pack(expand=False, fill="x", pady=(38, 38))
    new_content = re.sub(
        r'(center\.pack\(expand=False, fill="x", pady=)\(38,\s*38\)',
        r'\g<1>(38, 15)',
        content
    )

    if new_content == content:
        print("⚠️ Padrão não encontrado. Verifique se a linha é exatamente: center.pack(expand=False, fill=\"x\", pady=(38, 38))")
    else:
        with open(MAIN_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ Espaçamento ajustado para (38, 15).")
        print("▶️ Execute 'python -m core.main' para ver o resultado.")

    print("🧹 Após testar, pode excluir este script.")

if __name__ == "__main__":
    main()
