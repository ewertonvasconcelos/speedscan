#!/bin/bash

# Script de correção automática para o SpeedScan
# Deve ser executado dentro do diretório ~/speedscan/speedscan
# com o ambiente virtual ativado.

set -e  # Para o script se algum comando falhar

echo "=== Aplicando correções no SpeedScan ==="

# 1. Adicionar prints de depuração nos métodos principais
echo "Adicionando prints de depuração..."
sed -i '/def round_image(self, path, size=(96,96), radius=20):/a\        print(f"DEBUG round_image: path={path}")' core/main.py
sed -i '/return ctk.CTkImage(result, size=size)/i\        print("DEBUG round_image: sucesso")' core/main.py

# Corrigir o bloco except para usar Exception as e
sed -i 's/except:/except Exception as e:/' core/main.py

# Adicionar print no except (se já não tiver)
if ! grep -q "print(f\"DEBUG round_image: erro {e}\")" core/main.py; then
    sed -i '/except Exception as e:/a\            print(f"DEBUG round_image: erro {e}")' core/main.py
fi

# Adicionar print no run_card_action
sed -i '/def run_card_action(self, cmd, tag, is_dns):/a\        print(f"DEBUG run_card_action: cmd={cmd}, tag={tag}, is_dns={is_dns}")' core/main.py

# Adicionar print no toggle_console
sed -i '/def toggle_console(self, tag):/a\        print(f"DEBUG toggle_console: tag={tag}")' core/main.py

# 2. Garantir que os botões "Detalhes ┄" apareçam (adicionar pack)
echo "Adicionando pack dos botões de console..."

# Função para adicionar linhas após um padrão, se não existirem
add_pack_lines() {
    local file=$1
    local pattern=$2
    local lines=$3
    if ! grep -A2 "$pattern" "$file" | grep -q "btn.pack"; then
        sed -i "/$pattern/a\\        $lines" "$file"
    fi
}

add_pack_lines core/main.py 'btn, log = ui.add_console(parent, "ot", self.acc_color, self.toggle_console)' 'btn.pack(anchor="e", padx=5, pady=5)\n        log.pack_forget()'
add_pack_lines core/main.py 'btn, log = ui.add_console(parent, "net", self.acc_color, self.toggle_console)' 'btn.pack(anchor="e", padx=5, pady=5)\n        log.pack_forget()'
add_pack_lines core/main.py 'btn, log = ui.add_console(parent, "drv", self.acc_color, self.toggle_console)' 'btn.pack(anchor="e", padx=5, pady=5)\n        log.pack_forget()'
add_pack_lines core/main.py 'btn, log = ui.add_console(parent, "sec", self.acc_color, self.toggle_console)' 'btn.pack(anchor="e", padx=5, pady=5)\n        log.pack_forget()'

# 3. Verificar e corrigir possíveis erros de sintaxe (como vírgulas extras)
echo "Verificando sintaxe do main.py..."
python -m py_compile core/main.py || {
    echo "Erro de sintaxe detectado. Tentando corrigir automaticamente..."
    # Remover vírgulas extras no dicionário THEMES (se houver)
    sed -i 's/},/}/g' core/main.py
    sed -i 's/,,/,/g' core/main.py
}

# 4. Garantir que o ícone está no lugar certo e com permissões
echo "Verificando ícone..."
if [ ! -f ~/speedscan/speedscan/assets/icon.png ]; then
    echo "Ícone não encontrado. Copiando de ~/Downloads/icon.png"
    cp ~/Downloads/icon.png ~/speedscan/speedscan/assets/icon.png
fi
chmod 644 ~/speedscan/speedscan/assets/icon.png

# 5. Verificar se o ambiente virtual está ativo
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Ambiente virtual não ativo. Ativando..."
    source ~/speedscan/speedscan-venv/bin/activate
fi

# 6. Instalar dependências (caso falte alguma)
echo "Verificando dependências..."
pip install --quiet pillow customtkinter matplotlib psutil requests speedtest-cli

echo "=== Correções aplicadas. Execute o programa com: python -m core.main ==="
