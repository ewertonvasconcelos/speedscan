import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import os

def get_auth_command():
    for cmd in ['pkexec', 'kdesu', 'gksu']:
        if subprocess.run(f"which {cmd}", shell=True, capture_output=True).returncode == 0:
            return cmd
    return "sudo"

def run_cmd(command, needs_sudo=True, is_report=False):
    auth = get_auth_command()
    if is_report:
        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            show_report(result)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório: {e}")
        return

    final_cmd = f"{auth} bash -c \"{command}\"" if needs_sudo else command
    try:
        subprocess.run(final_cmd, shell=True, check=True)
        messagebox.showinfo("Sucesso", "Ação concluída com sucesso!")
    except:
        messagebox.showwarning("Aviso", "Ação cancelada ou falhou.")

def show_report(text):
    rep_win = tk.Toplevel(root)
    rep_win.title("Relatório SpeedScan")
    rep_win.geometry("600x450")
    rep_win.configure(bg="#1a1a1a")
    txt = scrolledtext.ScrolledText(rep_win, width=70, height=20, font=("Monospace", 10), bg="#2d2d2d", fg="#ffffff")
    txt.insert(tk.INSERT, text)
    txt.config(state='disabled')
    txt.pack(padx=15, pady=15)
    tk.Button(rep_win, text="Fechar", command=rep_win.destroy, bg="#444", fg="white").pack(pady=5)

root = tk.Tk()
root.title("SpeedScan Beta 0.2")
root.geometry("420x650")
root.configure(bg="#121212")

tk.Label(root, text="SPEEDSCAN CONTROL", fg="#00FF00", bg="#121212", font=("Arial", 16, "bold")).pack(pady=20)

# COMANDO DE OTIMIZAÇÃO REAL (Combo de limpeza)
# 1. Limpa Cache DNF | 2. Limpa Cache do Sistema | 3. Libera RAM (Drop Caches) | 4. Limpa Logs velhos
optimize_logic = (
    "dnf clean all && "
    "sync; echo 3 > /proc/sys/vm/drop_caches && "
    "journalctl --vacuum-time=1d && "
    "find /var/tmp/ -type f -atime +1 -delete"
)

dns_cmd = "nmcli device modify $(nmcli -t -f DEVICE,STATE dev | grep :connected | cut -d: -f1 | head -n1) ipv4.dns '8.8.8.8 8.8.4.4'"
kernel_cmd = "dnf repoquery --installonly --latest-limit=-2 -q | xargs dnf remove -y"

buttons = [
    ("🚀 OTIMIZAÇÃO TOTAL", optimize_logic, True, False),
    ("🖱 Corrigir Touchpad", "modprobe -r i2c_hid_acpi && modprobe i2c_hid_acpi", True, False),
    ("🌐 Configurar DNS Google", dns_cmd, True, False),
    ("🧹 Limpar Cache do Usuário", "rm -rf ~/.cache/*", False, False),
    ("📦 Remover Kernels Antigos", kernel_cmd, True, False),
    ("🌡 Ver Temperatura CPU", "sensors | grep 'Core'", False, True),
    ("📋 Relatório de Disco/RAM", "df -h && echo '---' && free -h", False, True),
    ("🔍 Ver Logs de Erro", "journalctl -p 3 -xb --no-pager | tail -n 15", False, True)
]

for text, cmd, sudo, report in buttons:
    bg_color = "#1f1f1f" if "OTIMIZAÇÃO" not in text else "#004d40"
    tk.Button(root, text=text, command=lambda c=cmd, s=sudo, r=report: run_cmd(c, s, r),  
              width=30, height=2, bg=bg_color, fg="white", font=("Arial", 10),  
              activebackground="#333", relief="flat").pack(pady=4)

tk.Button(root, text="SAIR", command=root.quit, bg="#cf6679", fg="black", width=10, font=("Arial", 10, "bold")).pack(pady=15)

root.mainloop()
