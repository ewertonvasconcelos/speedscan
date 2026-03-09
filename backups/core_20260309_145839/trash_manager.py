#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trash manager for SpeedScan - manages deleted files with metadata.
Version 1.0.0
"""

import shutil
import os
import time
import json
from pathlib import Path
import logging

from core import config

def _get_trash_dir():
    return Path.home() / ".speedscan_trash"

def _get_metadata_path():
    return _get_trash_dir() / "metadata.json"

TRASH_DIR = _get_trash_dir()
TRASH_METADATA = _get_metadata_path()


class TrashManager:
    """Manages a trash folder with metadata for restoring deleted files."""

    def __init__(self):
        """Initialize the trash directory and metadata file."""
        TRASH_DIR.mkdir(parents=True, exist_ok=True)
        if not TRASH_METADATA.exists():
            self._save_metadata({})

    def _load_metadata(self):
        """Load the metadata from JSON file."""
        with open(TRASH_METADATA, 'r') as f:
            return json.load(f)

    def _save_metadata(self, metadata):
        """Save the metadata to JSON file."""
        with open(TRASH_METADATA, 'w') as f:
            json.dump(metadata, f, indent=2)

    def move_to_trash(self, path, original_path):
        """Move a file or directory to the trash, storing its original path.

        Args:
            path (str): The current path of the item to be moved.
            original_path (str): The original location (where it came from).

        Returns:
            bool: True on success, False otherwise.
        """
        if not os.path.exists(path):
            return False
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
        """Restore an item from the trash to its original location.

        Args:
            trash_name (str): The name of the item in the trash.

        Returns:
            bool: True on success, False otherwise.
        """
        metadata = self._load_metadata()
        if trash_name not in metadata:
            return False
        info = metadata[trash_name]
        trash_path = TRASH_DIR / trash_name
        original = Path(info['original'])
        if not trash_path.exists():
            return False
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(trash_path), str(original))
        del metadata[trash_name]
        self._save_metadata(metadata)
        return True

    def empty_trash(self):
        """Empty the trash folder (delete all files and reset metadata)."""
        shutil.rmtree(TRASH_DIR)
        TRASH_DIR.mkdir()
        self._save_metadata({})

    def list_trash(self):
        """List all items in the trash with metadata.

        Returns:
            list: List of dictionaries each containing 'name', 'original', 'time'.
        """
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
        """Calculate the total size of the trash folder (excluding metadata).

        Returns:
            int: Total size in bytes.
        """
        total = 0
        for root, dirs, files in os.walk(TRASH_DIR):
            for f in files:
                if f == 'metadata.json':
                    continue
                fp = Path(root) / f
                total += fp.stat().st_size
        return total
