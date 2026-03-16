#!/bin/bash
# Script para implementar o novo comportamento do card Ping
# Deve ser executado no diretório ~/speedscan/speedscan com o ambiente virtual ativado

set -e

echo "Aplicando modificações para o card Ping..."

# 1. Modificar ui.py para que create_card_grid retorne também um dicionário de labels de resultado
# Vamos substituir a função create_card_grid por uma versão que cria um label genérico para cada card
# e retorna um dicionário com eles.

cp core/ui.py core/ui.py.bak_ping
sed -i '/def create_card_grid/,/return ping_labels/c\
def create_card_grid(parent, items, tag_prefix, acc_color, bg_color, text_color, command_callback):\
    """Create a grid of cards from a list of items.\
\
    Each item is a tuple (label, command, is_dns).\
    The grid has 3 columns; cards are placed row by row.\
\
    Args:\
        parent: Parent widget.\
        items (list): List of tuples (label, cmd, is_dns).\
        tag_prefix (str): Prefix used in callbacks to identify the card group.\
        acc_color (str): Color for accent (e.g., buttons, borders).\
        bg_color (str): Background color for cards.\
        text_color (str): Text color.\
        command_callback (callable): Function that takes (cmd, tag, is_dns).\
\
    Returns:\
        tuple: (ping_labels, result_labels) where ping_labels is a list of ping label widgets,\
               and result_labels is a dict mapping cmd to the result label widget.\
    """\
    grid_frame = ctk.CTkFrame(parent, fg_color="transparent")\
    grid_frame.pack(fill="x", pady=5)\
\
    ping_labels = []\
    result_labels = {}\
    for idx, (label, cmd, is_dns) in enumerate(items):\
        row, col = divmod(idx, 3)\
        card = ctk.CTkFrame(grid_frame, fg_color=bg_color, corner_radius=10,\
                             border_width=1, border_color=acc_color)\
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")\
        card.grid_propagate(False)\
        card.configure(height=150)\
\
        title = ctk.CTkLabel(card, text=label, font=("Inter", 14, "bold"),\
                              text_color=acc_color)\
        title.pack(pady=(10,5))\
\
        # Create a result label inside the card\
        result_label = ctk.CTkLabel(card, text="", font=("Inter", 10), text_color=text_color, wraplength=180)\
        result_label.pack(expand=True, fill="both", padx=5, pady=5)\
        result_labels[cmd] = result_label\
\
        if cmd == "ping":\
            ping_label = ctk.CTkLabel(card, text="-- ms", font=("Inter", 18, "bold"),\
                                       text_color=text_color)\
            ping_label.pack(expand=True)\
            ping_labels.append(ping_label)\
            # Replace result_label with ping_label for ping\
            result_labels[cmd] = ping_label\
\
        btn = ctk.CTkButton(card, text="Run", fg_color=acc_color,\
                             command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d),\
                             cursor="hand2")\
        btn.pack(pady=5)\
\
    for i in range(3):\
        grid_frame.columnconfigure(i, weight=1)\
\
    return ping_labels, result_labels' core/ui.py

# 2. Modificar main.py para armazenar os result_labels e usá-los no _run_ping
cp core/main.py core/main.py.bak_ping

# Adicionar um atributo self.result_labels no __init__
sed -i '/self.logs = {}/a\        self.result_labels = {}' core/main.py

# Modificar _fill_rede para capturar os result_labels
# Vamos substituir a linha que chama ui.create_card_grid para receber dois retornos
sed -i '/ping_labels = ui.create_card_grid(/c\        ping_labels, result_labels = ui.create_card_grid(parent, items, "net", self.acc_color, self.bg_color, self.text_color, self.run_card_action)' core/main.py
sed -i '/if ping_labels:/a\        self.result_labels.update(result_labels)' core/main.py

# Modificar _run_ping para executar o ping, calcular média e atualizar o label
# Vamos substituir a função _run_ping inteira
sed -i '/def _run_ping(self, log):/,/^    def/ c\
    def _run_ping(self, log):\
        import subprocess\
        import re\
        log.insert("end", self._("Executando ping (10 pacotes)...\\n"))\
        try:\
            result = subprocess.run(["ping", "-c", "10", "google.com"], capture_output=True, text=True, timeout=30)\
            output = result.stdout\
            log.insert("end", output)\
            # Extrair tempos e calcular média\
            times = re.findall(r"time=(\d+\.?\d*)", output)\
            if times:\
                avg = sum(float(t) for t in times) / len(times)\
                # Atualizar o label do card Ping\
                ping_label = self.result_labels.get("ping")\
                if ping_label:\
                    ping_label.configure(text=f"{avg:.1f} ms")\
            # Verificar se a saída é longa (>200 chars) e mostrar botão Detalhes\
            if len(output) > 200:\
                btn = self.detail_buttons.get("net")\
                if btn:\
                    btn.pack(anchor="e", padx=5, pady=5)\
            else:\
                # Se for curta, esconder o botão (se estiver visível)\
                btn = self.detail_buttons.get("net")\
                if btn and btn.winfo_ismapped():\
                    btn.pack_forget()\
        except Exception as e:\
            log.insert("end", self._("Erro no ping: {e}\\n").format(e=e))' core/main.py

# 3. Modificar o método toggle_console para que o botão mude de seta (opcional)
# Vamos adicionar um ícone de seta (podemos usar texto Unicode)
sed -i '/def toggle_console(self, tag):/,/^    def/ c\
    def toggle_console(self, tag):\
        print(f"DEBUG toggle_console: tag={tag}")\
        btn = self.detail_buttons.get(tag)\
        log = self.logs.get(tag)\
        if not btn or not log:\
            return\
        if self.consoles_visible.get(tag, False):\
            log.pack_forget()\
            btn.configure(text="Detalhes ▼")\
            self.consoles_visible[tag] = False\
        else:\
            log.pack(fill="x", padx=5, before=btn)\
            btn.configure(text="Detalhes ▲")\
            self.consoles_visible[tag] = True' core/main.py

echo "Modificações concluídas. Execute o programa com: python -m core.main"
