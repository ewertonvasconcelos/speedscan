import customtkinter as ctk
import subprocess
import threading

ctk.set_appearance_mode("Dark")

class SpeedScanPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpeedScan Pro - Beta 0.1")
        self.geometry("1100x850")
        self.configure(fg_color="#0f172a")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.console_visible = False
        self.details_btn_exists = False 

        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#1e293b")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="SPEEDSCAN", font=("Inter", 24, "bold"), text_color="#38bdf8").grid(row=0, column=0, padx=20, pady=40)
        self.create_nav("Dashboard", 1, "📊", self.show_dashboard)
        self.create_nav("Ajustes", 2, "⚙️", self.show_settings)
        self.create_nav("Sobre", 3, "ℹ️", self.show_about)

        self.content = ctk.CTkFrame(self, corner_radius=25, fg_color="transparent")
        self.content.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")
        self.show_dashboard()

    def create_nav(self, text, row, icon, cmd):
        btn = ctk.CTkButton(self.sidebar, text=f"{icon}  {text}", anchor="w", height=45, fg_color="transparent", hover_color="#334155", font=("Inter", 15), command=cmd)
        btn.grid(row=row, column=0, padx=15, pady=8, sticky="ew")

    def show_dashboard(self):
        self.clear_frame()
        self.content.columnconfigure(0, weight=1)
        self.details_btn_exists = False 
        ctk.CTkLabel(self.content, text="Painel de Controle", font=("Inter", 30, "bold")).grid(row=0, column=0, pady=(10, 20))
        self.grid_btns = ctk.CTkFrame(self.content, fg_color="transparent")
        self.grid_btns.grid(row=1, column=0, pady=10)
        
        # COMANDOS ATUALIZADOS COM ECHO PARA MOSTRAR NOS DETALHES
        items = [
            ("DNS", "DNS_ACTION", "#0369a1", "🌐"),
            ("Status CPU", "top -bn1 | head -n 20", "#b45309", "🌡"),
            ("Limpar Cache", "rm -rfv ~/.cache/* && echo '--- Limpeza de Cache concluída com sucesso! ---'", "#b91c1c", "🧹"),
            ("Otimização", "sync; echo 3 > /proc/sys/vm/drop_caches && echo '--- RAM Otimizada! ---'", "#15803d", "🚀"),
            ("Limpar Apps", "dnf clean all && echo '--- Cache de pacotes DNF limpo! ---'", "#334155", "📦"),
            ("Uso de Disco", "df -h", "#7e22ce", "📊")
        ]
        
        r, c = 0, 0
        for name, cmd, color, icon in items:
            card = ctk.CTkButton(self.grid_btns, text=f"{icon}\n\n{name}", width=230, height=130, corner_radius=22, fg_color=color, font=("Inter", 16, "bold"), command=lambda x=cmd: self.handle_action(x))
            card.grid(row=r, column=c, padx=15, pady=15); c += 1
            if c > 2: c = 0; r += 1
        
        self.header_bar = ctk.CTkFrame(self.content, fg_color="transparent", height=40)
        self.toggle_btn = ctk.CTkButton(self.header_bar, text="Detalhes ▲", width=120, height=32, fg_color="transparent", text_color="#94a3b8", hover_color="#1e293b", font=("Inter", 14, "bold"), command=self.toggle_console)
        self.toggle_btn.pack()
        self.log_box = ctk.CTkTextbox(self.content, fg_color="#1e293b", text_color="#10b981", font=("Monospace", 12), state="disabled", height=250)

    def toggle_console(self):
        if not self.console_visible:
            self.log_box.grid(row=3, column=0, sticky="ew", padx=40, pady=(10, 0))
            self.toggle_btn.configure(text="Detalhes ▼")
            self.console_visible = True
        else:
            self.log_box.grid_forget()
            self.toggle_btn.configure(text="Detalhes ▲")
            self.console_visible = False

    def handle_action(self, action):
        if action == "DNS_ACTION": self.dns_dialog()
        else: threading.Thread(target=self.run_cmd, args=(action,), daemon=True).start()

    def run_cmd(self, cmd):
        try:
            process = subprocess.Popen(f"pkexec bash -c '{cmd}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            self.log_box.configure(state="normal"); self.log_box.delete("0.0", "end")
            first_output = True
            
            # Lê a saída em tempo real
            for line in iter(process.stdout.readline, ""):
                if first_output and not self.details_btn_exists:
                    self.after(0, self.reveal_details_button)
                    first_output = False
                self.log_box.insert("end", line)
                self.log_box.see("end")
            
            process.stdout.close()
            return_code = process.wait()
            
            stderr = process.stderr.read()
            if stderr:
                if not self.details_btn_exists: self.after(0, self.reveal_details_button)
                self.log_box.insert("end", f"\nErro/Status: {stderr}")
            
            self.log_box.configure(state="disabled")
        except Exception as e: print(f"Erro: {e}")

    def reveal_details_button(self):
        self.header_bar.grid(row=2, column=0, sticky="e", padx=40, pady=(20, 0))
        self.details_btn_exists = True

    def show_settings(self): self.clear_frame(); ctk.CTkLabel(self.content, text="Ajustes", font=("Inter", 28, "bold")).pack(pady=40)
    def show_about(self): self.clear_frame(); ctk.CTkLabel(self.content, text="Sobre", font=("Inter", 28, "bold")).pack(pady=40); ctk.CTkLabel(self.content, text="SpeedScan Pro\nEwerton Vasconcelos", font=("Inter", 18)).pack()
    def clear_frame(self):
        for widget in self.content.winfo_children(): widget.destroy()
    def dns_dialog(self):
        dialog = ctk.CTkToplevel(self); dialog.title("DNS"); dialog.geometry("300x200"); dialog.attributes("-topmost", True)
        ctk.CTkButton(dialog, text="Google", command=lambda: [self.handle_action("echo 'nameserver 8.8.8.8' > /etc/resolv.conf && echo 'DNS alterado para Google!'"), dialog.destroy()]).pack(pady=10)
        ctk.CTkButton(dialog, text="Cloudflare", command=lambda: [self.handle_action("echo 'nameserver 1.1.1.1' > /etc/resolv.conf && echo 'DNS alterado para Cloudflare!'"), dialog.destroy()]).pack(pady=10)

if __name__ == "__main__":
    app = SpeedScanPro(); app.mainloop()
