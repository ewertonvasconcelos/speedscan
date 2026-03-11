#!/usr/bin/env python3
"""
Adiciona os métodos _check_process_queue e relacionados à classe SpeedScan.
"""

import shutil
from pathlib import Path
from datetime import datetime

MAIN_FILE = Path("core/main.py")
BACKUP_DIR = Path("backups")

# Métodos a serem inseridos (com indentação de 4 espaços)
METHODS = '''

    # =========================================================================
    # Métodos do gerenciador de processos
    # =========================================================================
    def _check_process_queue(self):
        try:
            while True:
                procs = self.proc_manager.callback_queue.get_nowait()
                self._update_process_tree(procs)
        except:
            pass
        self.after(500, self._check_process_queue)

    def _update_process_tree(self, procs):
        if not hasattr(self, 'process_tree'):
            return
        for row in self.process_tree.get_children():
            self.process_tree.delete(row)
        for p in procs:
            values = (
                p['pid'], p['name'],
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_percent']:.1f}",
                p['status'], p['username'] or '', p['nice'],
                p.get('create_time_str', '')
            )
            self.process_tree.insert('', 'end', iid=str(p['pid']), values=values)

    def _refresh_process_list(self):
        procs = self.proc_manager.get_process_list()
        self._update_process_tree(procs)

    def _on_filter_change(self, event=None):
        if hasattr(self, 'filter_entry'):
            term = self.filter_entry.get()
            self.proc_manager.set_filter(term)

    def _on_sort_change(self, choice=None):
        self.proc_manager.set_sort(self.sort_var.get(), self.reverse_var.get())

    def _sort_by_column(self, col):
        current_sort = self.proc_manager.sort_by
        if current_sort == col:
            self.proc_manager.reverse = not self.proc_manager.reverse
        else:
            self.proc_manager.sort_by = col
            self.proc_manager.reverse = True
        self.sort_var.set(col)
        self.reverse_var.set(self.proc_manager.reverse)

    def _kill_selected_process(self):
        selected = self.process_tree.selection()
        if not selected:
            return
        pid = int(selected[0])
        if self.proc_manager.kill_process(pid):
            self._refresh_process_list()
            self.show_toast(f"Processo {pid} finalizado.")
        else:
            self.show_toast(f"Erro ao finalizar processo {pid}.", duration=3000)

    def _suspend_selected_process(self):
        selected = self.process_tree.selection()
        if not selected:
            return
        pid = int(selected[0])
        if self.proc_manager.suspend_process(pid):
            self._refresh_process_list()
            self.show_toast(f"Processo {pid} suspenso.")
        else:
            self.show_toast(f"Erro ao suspender processo {pid}.", duration=3000)

    def _resume_selected_process(self):
        selected = self.process_tree.selection()
        if not selected:
            return
        pid = int(selected[0])
        if self.proc_manager.resume_process(pid):
            self._refresh_process_list()
            self.show_toast(f"Processo {pid} continuado.")
        else:
            self.show_toast(f"Erro ao continuar processo {pid}.", duration=3000)

    def _set_nice_selected(self):
        selected = self.process_tree.selection()
        if not selected:
            return
        pid = int(selected[0])
        nice_val = self.nice_var.get()
        if self.proc_manager.set_nice(pid, nice_val):
            self._refresh_process_list()
            self.show_toast(f"Nice do processo {pid} alterado para {nice_val}.")
        else:
            self.show_toast(f"Erro ao alterar nice do processo {pid}.", duration=3000)

    def _on_process_double_click(self, event):
        selected = self.process_tree.selection()
        if not selected:
            return
        pid = int(selected[0])
        self.show_toast(f"Detalhes do PID {pid} em breve.", duration=2000)
'''

def fazer_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"main.py.{timestamp}.bak"
    shutil.copy(MAIN_FILE, backup_path)
    print(f"✅ Backup criado em: {backup_path}")

def main():
    print("🔧 Adicionando métodos de processo faltantes...")

    if not MAIN_FILE.exists():
        print("❌ core/main.py não encontrado!")
        return

    fazer_backup()

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Verificar se os métodos já existem
    if "def _check_process_queue" in content:
        print("⚠️ Métodos já parecem existir. Nenhuma ação necessária.")
        return

    # Inserir antes do final da classe (antes de if __name__)
    # Procurar pela última ocorrência de 'def' que seja o último método da classe
    # Ou simplesmente inserir antes de 'if __name__'
    if "if __name__" in content:
        new_content = content.replace("if __name__", METHODS + "\n\nif __name__")
        with open(MAIN_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ Métodos inseridos com sucesso antes de if __name__.")
    else:
        print("❌ Não foi possível localizar 'if __name__'.")
        return

    print("▶️ Execute 'python -m core.main' novamente.")

if __name__ == "__main__":
    main()
