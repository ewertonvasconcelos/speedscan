#!/usr/bin/env python3
import shutil
import subprocess
import sys
from pathlib import Path

BACKUP_DIR = Path("backups")
CORE_DIR = Path("core")

def main():
    # Encontrar o backup mais recente
    backups = sorted(BACKUP_DIR.glob("core_*"))
    if not backups:
        print("❌ Nenhum backup encontrado em backups/")
        return
    latest = backups[-1]
    print(f"📦 Restaurando do backup: {latest}")

    # Remover core existente (se houver) e restaurar
    if CORE_DIR.exists():
        shutil.rmtree(CORE_DIR)
    shutil.copytree(latest, CORE_DIR)
    print("✅ Pasta core restaurada.")

    # Executar script de ajuste
    ajuste_script = Path("increase_button_spacing.py")
    if ajuste_script.exists():
        print("▶️ Executando increase_button_spacing.py...")
        subprocess.run([sys.executable, str(ajuste_script)])
    else:
        print("⚠️ Script increase_button_spacing.py não encontrado. Crie-o primeiro.")

if __name__ == "__main__":
    main()
