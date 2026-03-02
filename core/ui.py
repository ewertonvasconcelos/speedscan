#!/usr/bin/env python3
# core/ui.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Funções auxiliares para interface do SpeedScan (com cursor="arrow")
# =============================================================================

import customtkinter as ctk

def create_card_grid(parent, items, tag_prefix, acc_color, bg_color, text_color, command_callback):
    """
    Cria uma grade de cards baseada na lista de itens.
    Retorna uma lista de labels de ping (se houver).
    Todos os botões com cursor="arrow".
    """
    grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
    grid_frame.pack(fill="x", pady=5)

    ping_labels = []
    for idx, (label, cmd, is_dns) in enumerate(items):
        row, col = divmod(idx, 3)
        card = ctk.CTkFrame(grid_frame, fg_color=bg_color, corner_radius=10,
                             border_width=1, border_color=acc_color)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.grid_propagate(False)
        card.configure(height=150)

        # Título do card (cor de destaque)
        title = ctk.CTkLabel(card, text=label, font=("Inter", 14, "bold"),
                              text_color=acc_color)
        title.pack(pady=(10,5))

        if cmd == "ping":
            # Card especial para ping: label dinâmico + botão
            ping_label = ctk.CTkLabel(card, text="-- ms", font=("Inter", 18, "bold"),
                                       text_color=text_color)
            ping_label.pack(expand=True)
            ping_labels.append(ping_label)
            # Botão para iniciar/parar ping (cursor arrow)
            btn = ctk.CTkButton(card, text="Iniciar", fg_color=acc_color,
                                 cursor="arrow",
                                 command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d))
            btn.pack(pady=5)
        else:
            # Botão de ação padrão (cursor arrow)
            btn = ctk.CTkButton(card, text="Executar", fg_color=acc_color,
                                 cursor="arrow",
                                 command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d))
            btn.pack(expand=True)

    # Configurar colunas do grid_frame para expandir igualmente
    for i in range(3):
        grid_frame.columnconfigure(i, weight=1)

    return ping_labels

def add_console(parent, tag_prefix, acc_color, toggle_callback):
    """
    Adiciona um botão "Detalhes" e uma área de console (inicialmente oculta).
    Retorna o botão e o console.
    """
    console = ctk.CTkTextbox(parent, height=150, fg_color="#1e1e1e", text_color="#ffffff",
                              font=("Consolas", 10), corner_radius=10)
    # Botão para mostrar/esconder console (cursor arrow)
    btn = ctk.CTkButton(parent, text="Detalhes ⌄", fg_color=acc_color,
                         cursor="arrow",
                         command=lambda: toggle_callback(tag_prefix))
    return btn, console
