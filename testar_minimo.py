#!/usr/bin/env python3
# Versão mínima para testar se a janela abre

import customtkinter as ctk

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Teste")
        self.geometry("400x300")
        self.label = ctk.CTkLabel(self, text="Funcionou!")
        self.label.pack(pady=20)

if __name__ == "__main__":
    app = App()
    app.mainloop()
