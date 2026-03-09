#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp core/*.py "$BACKUP_DIR"/
echo "Backup salvo em $BACKUP_DIR"
