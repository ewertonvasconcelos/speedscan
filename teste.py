import customtkinter as ctk
app = ctk.CTk()
app.geometry("300x200")
app.title("Teste")
ctk.CTkLabel(app, text="Funciona!").pack()
app.mainloop()
