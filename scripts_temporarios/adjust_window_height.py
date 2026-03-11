#!/usr/bin/env python3
"""
Reduz a altura da janela e ajusta o topo para aproximar as abas inferiores.
"""

import shutil
import re
from pathlib import Path

MAIN_FILE = Path("core/main.py")
BACKUP_FILE = Path("core/main.py.bak")

def main():
    print("📏 Ajustando altura da janela e topo...")

    if not MAIN_FILE.exists():
        print("❌ core/main.py não encontrado!")
        return

    shutil.copy(MAIN_FILE, BACKUP_FILE)
    print(f"✅ Backup: {BACKUP_FILE}")

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Reduzir minsize para 900x420
    content = re.sub(
        r'self\.minsize\(900,\s*\d+\)',
        'self.minsize(900, 420)',
        content
    )

    # 2. Ajustar padding da logo para (15, 10)
    content = re.sub(
        r'(top\.pack\(pady=)\$\{?[^)]*\)?',
        r'top.pack(pady=(15, 10))',
        content
    )

    # 3. Garantir que o center continue expandindo e com pady zero
    content = re.sub(
        r'center\.pack\(expand=False, fill="x", pady=\(\d+, \d+\)\)',
        'center.pack(expand=True, fill="x", pady=(0, 0))',
        content
    )

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Ajustes aplicados!")
    print("▶️ Execute 'python -m core.main' e veja o resultado.")
    print("🧹 Após testar, pode excluir este script.")

if __name__ == "__main__":
    main()
