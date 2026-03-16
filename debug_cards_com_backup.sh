#!/bin/bash
# Script de depuração com backup prévio

set -e

BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp core/*.py "$BACKUP_DIR/" 2>/dev/null
echo "✅ Backup criado em $BACKUP_DIR"

echo "🔧 Adicionando prints de depuração..."

# 1. Print em run_card_action
sed -i '/def run_card_action(self, cmd, tag, is_dns):/a\        print(f"DEBUG: run_card_action chamado com cmd={cmd}, tag={tag}, is_dns={is_dns}")' core/main.py

# 2. Print em _execute_command
sed -i '/def _execute_command(self, cmd, log, tag, is_dns):/a\        print(f"DEBUG: _execute_command: cmd={cmd}, tag={tag}, is_dns={is_dns}")' core/main.py

# 3. Print em _run_ping (início)
sed -i '/def _run_ping(self, log, tag=None):/a\        print("DEBUG: _run_ping iniciado")' core/main.py

# 4. Print do tamanho da saída
sed -i '/output = result.stdout/a\        print(f"DEBUG: Tamanho da saída do ping: {len(output)} caracteres")' core/main.py

# 5. Print quando mostra o botão
sed -i '/if len(output) > 200:/a\                print("DEBUG: Saída longa, mostrando botão Detalhes")' core/main.py

# 6. Print em _after_command
sed -i '/def _after_command(self, tag, log):/a\        print(f"DEBUG: _after_command: tag={tag}, tamanho do log = {len(log.get(\"1.0\", \"end-1c\"))}")' core/main.py

# 7. Print em toggle_console
sed -i '/def toggle_console(self, tag):/a\        print(f"DEBUG: toggle_console chamado com tag={tag}, visível={self.consoles_visible.get(tag)}")' core/main.py

echo "✅ Prints adicionados."
echo "🚀 Execute o programa com: python -m core.main"
echo "📋 Cole aqui toda a saída do terminal após clicar no card Ping e no botão Detalhes."
