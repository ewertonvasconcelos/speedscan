import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import threading
import os

class SpeedScanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SpeedScan Beta 0.1 - ASUS S46CA")
        self.root.geometry("600x500")
        self.root.configure(bg="#121212")

        # Título
        tk.Label(root, text="SPEEDSCAN PRO", font=("Ubuntu", 24, "bold"), fg="#00ff00", bg="#121212").pack(pady=15)
        
        # Botões Superiores
        btn_frame = tk.Frame(root, bg="#121212")
        btn_frame.pack(pady=10)

        btn_style = {"font": ("Ubuntu", 10, "bold"), "width": 22, "height": 2, "cursor": "hand2", "fg": "white"}

        self.btn_speed = tk.Button(btn_frame, text="🚀 ACELERAR SISTEMA", command=lambda: self.start_thread("SpeedScan.sh"), 
                                   bg="#27ae60", activebackground="#2ecc71", **btn_style)
        self.btn_speed.grid(row=0, column=0, padx=10)

        self.btn_touch = tk.Button(btn_frame, text="🖱️ CORRIGIR TOUCHPAD", command=lambda: self.start_thread("fazer_touchpad.sh"), 
                                   bg="#2980b9", activebackground="#3498db", **btn_style)
        self.btn_touch.grid(row=0, column=1, padx=10)

        # Console incorporado
        tk.Label(root, text="DETALHES DA EXECUÇÃO:", font=("Ubuntu", 9), fg="#aaaaaa", bg="#121212").pack(anchor="w", padx=25, pady=(15, 0))
        
        self.console_frame = tk.Frame(root, bg="#000000", bd=2, relief="flat")
        self.console_frame.pack(padx=20, pady=5, fill="both", expand=True)

        self.console = tk.Text(self.console_frame, bg="#000000", fg="#00ff00", font=("Monospace", 9), state="disabled", insertbackground="white")
        self.console.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Barra de rolagem do console
        self.scrollbar = tk.Scrollbar(self.console_frame, command=self.console.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.console.config(yscrollcommand=self.scrollbar.set)

        self.password = ""

    def log(self, text):
        self.console.config(state="normal")
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        self.console.config(state="disabled")

    def start_thread(self, script):
        if not self.password:
            # Pede a senha usando uma janelinha do próprio app
            self.password = simpledialog.askstring("Autenticação", "Digite sua senha (sudo):", show='*')
        
        if self.password:
            self.log(f">>> Preparando: {script}...")
            thread = threading.Thread(target=self.execute_script, args=(script,))
            thread.daemon = True
            thread.start()

    def execute_script(self, script_name):
        path = os.path.expanduser(f"~/speedscan/{script_name}")
        self.log(f">>> EXECUTANDO: {script_name}")
        
        # O comando envia a senha automaticamente para o sudo
        cmd = f"echo '{self.password}' | sudo -S bash {path}"
        
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in process.stdout:
            self.log(line.strip())
        
        process.wait()
        if process.returncode == 0:
            self.log(f"\n[OK] {script_name} CONCLUÍDO!")
        else:
            self.log("\n[ERRO] Falha na execução. Verifique sua senha.")
            self.password = "" # Limpa a senha para tentar de novo se errar

if __name__ == "__main__":
    root = tk.Tk()
    app = SpeedScanApp(root)
    root.mainloop()
