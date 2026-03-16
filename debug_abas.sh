#!/bin/bash
# Script de depuração para identificar por que as abas não aparecem

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual
source venv/bin/activate

echo "🔍 Iniciando depuração das abas..."

# Fazer backup do main.py original
backup_file="core/main.py.bak.debug.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# Adicionar prints nos métodos de preenchimento das abas e no show_frame
echo "   + Adicionando mensagens de depuração..."

# show_frame
sed -i '/def show_frame(/a \        print(f"DEBUG: show_frame chamado com target={target}")' core/main.py

# _fill_dashboard
sed -i '/def _fill_dashboard(/a \        print("DEBUG: _fill_dashboard executado")' core/main.py

# _fill_optimization
sed -i '/def _fill_optimization(/a \        print("DEBUG: _fill_optimization executado")' core/main.py

# _fill_network
sed -i '/def _fill_network(/a \        print("DEBUG: _fill_network executado")' core/main.py

# _fill_drivers
sed -i '/def _fill_drivers(/a \        print("DEBUG: _fill_drivers executado")' core/main.py

# _fill_processes
sed -i '/def _fill_processes(/a \        print("DEBUG: _fill_processes executado")' core/main.py

# _fill_history
sed -i '/def _fill_history(/a \        print("DEBUG: _fill_history executado")' core/main.py

# _fill_security
sed -i '/def _fill_security(/a \        print("DEBUG: _fill_security executado")' core/main.py

# _fill_agent
sed -i '/def _fill_agent(/a \        print("DEBUG: _fill_agent executado")' core/main.py

# _fill_settings
sed -i '/def _fill_settings(/a \        print("DEBUG: _fill_settings executado")' core/main.py

# _fill_about
sed -i '/def _fill_about(/a \        print("DEBUG: _fill_about executado")' core/main.py

# _fill_windows_cleaner
sed -i '/def _fill_windows_cleaner(/a \        print("DEBUG: _fill_windows_cleaner executado")' core/main.py

# Remover possíveis try/except que escondem erros (opcional, mas útil)
# Isso substitui "except:" por "except Exception as e: print(e)" temporariamente
sed -i 's/except:/except Exception as e: print(f"ERRO: {e}")/g' core/main.py

echo "✅ Modificações concluídas. Execute o programa agora:"
echo "   python3 -m core.main"
echo ""
echo "Observe as mensagens no terminal. Quando terminar, restaure o backup com:"
echo "   cp \"$backup_file\" core/main.py"
