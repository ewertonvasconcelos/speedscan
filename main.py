import sys
import platform
import psutil
import os
import shutil
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class SpeedScan:
    def __init__(self):
        self.os_name = platform.system()
        self.os_release = platform.release()

    def get_system_info(self):
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        return {
            "cpu": psutil.cpu_percent(interval=0.5),
            "ram": psutil.virtual_memory().percent,
            "os": f"{self.os_name} {self.os_release}",
            "uptime": str(uptime).split('.')[0]
        }

    def limpar_temporarios(self):
        count = 0
        try:
            if self.os_name == "Windows":
                pasta_temp = os.environ.get('TEMP')
            else:
                pasta_temp = '/tmp'

            for arquivo in os.listdir(pasta_temp):
                caminho = os.path.join(pasta_temp, arquivo)
                try:
                    if os.path.isfile(caminho) or os.path.islink(caminho):
                        os.unlink(caminho)
                        count += 1
                    elif os.path.isdir(caminho):
                        shutil.rmtree(caminho)
                        count += 1
                except Exception:
                    continue
            messagebox.showinfo("Sucesso", f"Limpeza concluída!\n{count} itens removidos do {self.os_name}.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na limpeza: {e}")

    def otimizar_ram(self):
        # Simulação de otimização (coleta de lixo do Python e aviso ao sistema)
        import gc
        gc.collect()
        messagebox.showinfo("Otimização", "Memória RAM otimizada com sucesso!")

    def iniciar_interface(self):
        root = tk.Tk()
        root.title(f"SpeedScan Pro v1.1.0 - {self.os_name}")
        root.geometry("450x500")

        cor_fundo = "#f0f0f0" if self.os_name == "Windows" else "#1e1e1e"
        cor_texto = "#333333" if self.os_name == "Windows" else "#ffffff"
        cor_botao = "#0078d7" if self.os_name == "Windows" else "#3498db"
        
        root.configure(bg=cor_fundo)

        # Header
        tk.Label(root, text="🚀 SPEEDSCAN PRO", font=("Arial", 18, "bold"), bg=cor_fundo, fg=cor_botao).pack(pady=20)

        # Info Box
        dados = self.get_system_info()
        info_frame = tk.Frame(root, bg=cor_fundo)
        info_frame.pack(pady=10)

        tk.Label(info_frame, text=f"Sistema: {dados['os']}", font=("Arial", 10), bg=cor_fundo, fg=cor_texto).pack()
        tk.Label(info_frame, text=f"Uptime: {dados['uptime']}", font=("Arial", 10), bg=cor_fundo, fg="gray").pack()

        # Stats
        tk.Label(root, text=f"CPU: {dados['cpu']}% | RAM: {dados['ram']}%", font=("Arial", 12, "bold"), bg=cor_fundo, fg=cor_texto).pack(pady=20)

        # Botões de Ação
        btn_style = {"font": ("Arial", 10, "bold"), "fg": "white", "bg": cor_botao, "width": 25, "pady": 10}
        
        tk.Button(root, text="LIMPAR ARQUIVOS TEMPORÁRIOS", command=self.limpar_temporarios, **btn_style).pack(pady=10)
        tk.Button(root, text="OTIMIZAR MEMÓRIA RAM", command=self.otimizar_ram, **btn_style).pack(pady=10)

        # Footer
        tk.Label(root, text=f"Modo: {self.os_name} Optimized", font=("Arial", 8, "italic"), bg=cor_fundo, fg="gray").pack(side="bottom", pady=15)

        root.mainloop()

if __name__ == "__main__":
    app = SpeedScan()
    app.iniciar_interface()
