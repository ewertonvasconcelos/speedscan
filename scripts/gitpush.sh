#!/bin/bash
cd "$(dirname "$0")"
git add .
git commit -m "${1:-Atualização automática do SpeedScan}"
git push
