#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

# Backup
shutil.copy2("core/ui.py", "core/ui.py.bak_detalhes")
print("Backup de ui.py criado")

with open("core/ui.py", "r") as f:
    conteudo = f.read()

# Substituir a função create_card_grid para incluir um label de resultado
novo_create_card_grid = '''def create_card_grid(parent, items, tag_prefix, acc_color, bg_color, text_color, command_callback):
    """Create a grid of cards from a list of items.

    Each item is a tuple (label, command, is_dns).
    The grid has 3 columns; cards are placed row by row.

    Args:
        parent: Parent widget.
        items (list): List of tuples (label, cmd, is_dns).
        tag_prefix (str): Prefix used in callbacks to identify the card group.
        acc_color (str): Color for accent (e.g., buttons, borders).
        bg_color (str): Background color for cards.
        text_color (str): Text color.
        command_callback (callable): Function that takes (cmd, tag, is_dns).

    Returns:
        list: List of ping label widgets (if any).
    """
    grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
    grid_frame.pack(fill="x", pady=5)

    ping_labels = []
    result_labels = {}  # dicionário para armazenar labels de resultado por comando
    for idx, (label, cmd, is_dns) in enumerate(items):
        row, col = divmod(idx, 3)
        card = ctk.CTkFrame(grid_frame, fg_color=bg_color, corner_radius=10,
                             border_width=1, border_color=acc_color)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.grid_propagate(False)
        card.configure(height=150)

        title = ctk.CTkLabel(card, text=label, font=("Inter", 14, "bold"),
                              text_color=acc_color)
        title.pack(pady=(10,5))

        # Label para exibir resultado pequeno
        result_label = ctk.CTkLabel(card, text="", font=("Inter", 10), text_color=text_color, wraplength=180)
        result_label.pack(expand=True, fill="both", padx=5, pady=5)
        result_labels[cmd] = result_label

        if cmd == "ping":
            ping_label = ctk.CTkLabel(card, text="-- ms", font=("Inter", 18, "bold"),
                                       text_color=text_color)
            ping_label.pack(expand=True)
            ping_labels.append(ping_label)
            # Substituir o label de resultado pelo ping_label (para ping específico)
            result_labels[cmd] = ping_label

        btn = ctk.CTkButton(card, text="Run", fg_color=acc_color,
                             command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d),
                             cursor="hand2")
        btn.pack(pady=5)

    for i in range(3):
        grid_frame.columnconfigure(i, weight=1)

    return ping_labels, result_labels'''

# Substituir na função
padrao = r'def create_card_grid\(.*?return ping_labels\)'
conteudo = re.sub(padrao, novo_create_card_grid, conteudo, flags=re.DOTALL)

# Ajustar a função add_console para que o botão "Detalhes" seja criado mas não empacotado inicialmente
# Vamos modificar para retornar o botão sem pack, e o pack será feito depois se necessário
# Mas manteremos como está, pois o pack será feito em main.py condicionalmente

with open("core/ui.py", "w") as f:
    f.write(conteudo)

print("ui.py modificado com sucesso.")
