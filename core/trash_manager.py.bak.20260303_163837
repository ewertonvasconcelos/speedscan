#!/usr/bin/env python3
# core/trash_manager.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Gerenciador de lixeira para arquivos deletados pelo SpeedScan
# Versão 0.3.0-beta
# =============================================================================

import shutil
import os
import time
import json
from pathlib import Path

TRASH_DIR = Path.home() / ".speedscan_trash"
TRASH_METADATA = TRASH_DIR / "metadata.json"

class TrashManager:
    def __init__(self):
        TRASH_DIR.mkdir(parents=True, exist_ok=True)
        if not TRASH_METADATA.exists():
            self._save_metadata({})

    def _load_metadata(self):
        with open(TRASH_METADATA) as f:
            return json.load(f)

    def _save_metadata(self, metadata):
        with open(TRASH_METADATA, "w") as f:
            json.dump(metadata, f, indent=2)

    def move_to_trash(self, path, original_path):
        """Move um arquivo/diretório para a lixeira, registrando origem."""
        if not os.path.exists(path):
            return False
        # Cria um nome único na lixeira
        trash_name = f"{int(time.time())}_{os.path.basename(path)}"
        trash_path = TRASH_DIR / trash_name
        shutil.move(path, trash_path)
        metadata = self._load_metadata()
        metadata[trash_name] = {
            'original': str(original_path),
            'time': time.time()
        }
        self._save_metadata(metadata)
        return True

    def restore(self, trash_name):
        """Restaura um item da lixeira para seu local original."""
        metadata = self._load_metadata()
        if trash_name not in metadata:
            return False
        info = metadata[trash_name]
        trash_path = TRASH_DIR / trash_name
        original = Path(info['original'])
        if not trash_path.exists():
            return False
        # Move de volta
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(trash_path), str(original))
        del metadata[trash_name]
        self._save_metadata(metadata)
        return True

    def empty_trash(self):
        """Esvazia a lixeira permanentemente."""
        shutil.rmtree(TRASH_DIR)
        TRASH_DIR.mkdir()
        self._save_metadata({})

    def list_trash(self):
        """Lista itens na lixeira com metadados."""
        metadata = self._load_metadata()
        items = []
        for name, info in metadata.items():
            items.append({
                'name': name,
                'original': info['original'],
                'time': info['time']
            })
        return items

    def get_trash_size(self):
        """Retorna o tamanho total da lixeira em bytes."""
        total = 0
        for root, dirs, files in os.walk(TRASH_DIR):
            for f in files:
                if f == 'metadata.json':
                    continue
                fp = Path(root) / f
                total += fp.stat().st_size
        return total
