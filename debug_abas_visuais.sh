#!/bin/bash
# Adiciona prints para diagnosticar por que as abas não aparecem

set -e

cd ~/speedscan/speedscan

# Ativar ambiente virtual (opcional)
source venv/bin/activate 2>/dev/null || true

echo "🔧 Aplicando depuração visual..."

# Backup
backup_file="core/main.py.bak.visual.$(date +%s)"
cp core/main.py "$backup_file"
echo "✅ Backup criado: $backup_file"

# 1. Adicionar print no __init__ para confirmar que a classe é instanciada
sed -i '/def __init__(/a \        print("DEBUG: SpeedScan.__init__ iniciado")' core/main.py

# 2. Adicionar print no _build_sidebar para verificar se os botões são criados
sed -i '/def _build_sidebar(/a \        print("DEBUG: _build_sidebar iniciado")' core/main.py

# 3. Adicionar print no show_frame para ver se é chamado
sed -i '/def show_frame(/a \        print(f"DEBUG: show_frame chamado com target={target}")' core/main.py

# 4. Adicionar print nos métodos de preenchimento das abas
for aba in dashboard optimization network drivers processes history security agent settings about windows_cleaner; do
    sed -i "/def _fill_${aba}(/a \        print(\"DEBUG: _fill_${aba} executado\")" core/main.py
done

# 5. Substituir except: por except Exception as e: print(e) para ver erros ocultos
sed -i 's/^\( *\)except:/\1except Exception as e:\n\1    print(f"ERRO: {e}")/' core/main.py

# 6. Adicionar print no final do __init__ para confirmar que terminou
sed -i '/self.after(500, self._check_first_run)/a \        print("DEBUG: SpeedScan.__init__ finalizado")' core/main.py

echo "✅ Depuração inserida. Execute o programa:"
echo "   python3 -m core.main"
echo ""
echo "Observe as mensagens no terminal. Quando terminar, restaure com:"
echo "   cp \"$backup_file\" core/main.py"
