# core/ui.py
import customtkinter as ctk

def create_card_grid(parent, items, tag, acc_color, bg_color, command_callback):
    """Cria um grid de cards (3 colunas) com título e botão."""
    grid = ctk.CTkFrame(parent, fg_color="transparent")
    grid.pack(fill="both", expand=True, pady=10)
    for i in range(3):
        grid.columnconfigure(i, weight=1)

    for idx, (title, cmd, is_dns) in enumerate(items):
        row, col = divmod(idx, 3)
        card = ctk.CTkFrame(grid, fg_color=bg_color, corner_radius=10,
                             border_width=1, border_color=acc_color)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)
        card.configure(height=150)

        ctk.CTkLabel(card, text=title, font=("Inter",14,"bold"),
                     text_color=acc_color).pack(pady=(10,5))

        if title == "Ping":
            btn = ctk.CTkButton(card, text="Iniciar", fg_color=acc_color,
                                 command=lambda: command_callback("ping", tag, False), cursor="hand2")
            btn.pack(pady=5)
            # Será preciso um label de ping separado; faremos depois
        else:
            btn_text = "Aplicar" if is_dns else "Executar"
            btn = ctk.CTkButton(card, text=btn_text, fg_color=acc_color,
                                 command=lambda c=cmd, t=tag, d=is_dns: command_callback(c, t, d),
                                 cursor="hand2")
            btn.pack(pady=5)

def add_console(parent, tag, acc_color, toggle_callback):
    """Adiciona um console expansível."""
    btn = ctk.CTkButton(parent, text="Detalhes ⌄", fg_color="transparent",
                         text_color=acc_color, hover_color=acc_color,
                         corner_radius=20, command=lambda: toggle_callback(tag),
                         cursor="hand2")
    btn.pack(anchor="e", pady=5)
    log = ctk.CTkTextbox(parent, height=150, fg_color="#000000",
                          text_color="#10b981", font=("Consolas",11))
    return btn, log

