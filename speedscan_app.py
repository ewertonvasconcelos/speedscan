import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import os

def get_auth_command():
    # Detecta qual programa de senha (GUI) está disponível no sistema
    for cmd in ['pkexec', 'kdesu', 'gksu']:
        if subprocess.run(f"which {cmd}", shell=True, capture_output=True).returncode == 0:
            return cmd
    return "sudo"

def run_cmd(command, needs_sudo=True, is_report=False):
    auth = get_auth_command()
    
    if is_report:
        try:
            # Execução universal de relatório via subprocess para não depender de terminal específico
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            show_report(result)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório: {e}")
        return

    final_cmd = f"{auth} bash -c '{command}'" if needs_sudo else command
    try:
        subprocess.run(final_cmd, shell=True, check=True)
        messagebox.showinfo("Sucesso", "Operação concluída!")
    except:
        messagebox.showwarning("Aviso", "Ação cancelada ou falhou.")

def show_report(text):
    rep_win = tk.Toplevel(root)
    rep_win.title("Relatório SpeedScan")
    rep_win.geometry("600x400")
    txt = scrolledtext.ScrolledText(rep_win, width=70, height=20, font=("Monospace", 10))
    txt.insert(tk.INSERT, text)
    txt.config(state='disabled')
    txt.pack(padx=10, pady=10)

root = tk.Tk()
root.title("SpeedScan Beta 0.1")
root.geometry("400x550")
root.configure(bg="#212121")

label = tk.Label(root, text="SPEEDSCAN MULTI-OS", fg="#00FF00", bg="#212121", font=("Arial", 14, "bold"))
label.pack(pady=20)

dns_cmd = "nmcli device modify \$(nmcli -t -f DEVICE,STATE dev | grep :connected | cut -d: -f1 | head -n1) ipv4.dns '8.8.8.8 8.8.4.4'"

buttons = [
    ("Otimizar Sistema", "dnf clean all && zramctl --find --size 2G", True, False),
    ("Corrigir Touchpad", "modprobe -r i2c_hid_acpi && modprobe i2c_hid_acpi", True, False),
    ("Configurar DNS Google", dns_cmd, True, False),
    ("Limpar Cache de Apps", "rm -rf ~/.cache/* && echo 'Cache limpo'", False, False),
    ("Relatório de Sistema", "df -h && free -h && uptime", False, True),
    ("Caçador de Erros (Logs)", "journalctl -p 3 -xb --no-pager | tail -n 20", False, True)
]

for text, cmd, sudo, report in buttons:
    tk.Button(root, text=text, command=lambda c=cmd, s=sudo, r=report: run_cmd(c, s, r), 
              width=25, height=2, bg="#333333", fg="white", activebackground="#444444").pack(pady=5)

tk.Button(root, text="Sair", command=root.quit, bg="#b71c1c", fg="white", width=10).pack(pady=20)
root.mainloop()
