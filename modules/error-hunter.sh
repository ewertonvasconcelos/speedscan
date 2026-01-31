#!/bin/bash
echo "--- Erros Críticos (Últimas 2h) ---"
journalctl --since "2 hours ago" -p 3..0 --no-pager
