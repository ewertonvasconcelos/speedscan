#!/usr/bin/env python3
"""
Adiciona os métodos faltantes ao arquivo core/main.py:
- _check_process_queue
- _update_process_tree
- _refresh_process_list
- _on_filter_change
- _on_sort_change
- _sort_by_column
- _kill_selected_process
- _suspend_selected_process
- _resume_selected_process
- _set_nice_selected
- _on_process_double_click
- _update_graphs (já existe? vamos garantir)
- _on_period_change
- _on_metric_change
- _update_ai_suggestions
"""

import shutil
import re
from pathlib import Path

MAIN_FILE = Path("core/main.py")
BACKUP_FILE = Path("core/main.py.bak.missing")

# Métodos a serem inseridos (como string)
METHODS = """
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

    # =========================================================================
    # Métodos do histórico
    # =========================================================================
    def _on_period_change(self, choice):
        self._update_graphs()

    def _on_metric_change(self, choice):
        self._update_graphs()

    def _update_graphs(self):
        # Implementação simplificada (pode ser expandida depois)
        pass

    # =========================================================================
    # Métodos da IA
    # =========================================================================
    def _update_ai_suggestions(self):
        sugestoes = self.ai_proactive.get_summary()
        if hasattr(self, 'ai_sugestoes_text'):
            self.ai_sugestoes_text.delete("1.0", "end")
            self.ai_sugestoes_text.insert("1.0", sugestoes)
"""

def main():
    print("🔧 Adicionando métodos faltantes ao main.py...")

    if not MAIN_FILE.exists():
        print("❌ Arquivo core/main.py não encontrado!")
        return

    # Backup
    shutil.copy(MAIN_FILE, BACKUP_FILE)
    print(f"✅ Backup criado: {BACKUP_FILE}")

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Verificar se alguns métodos já existem (para não duplicar)
    if "def _check_process_queue" in content:
        print("⚠️ Métodos já parecem existir. Nenhuma alteração feita.")
        return

    # Procurar pelo final da classe (antes do if __name__)
    # Vamos inserir antes da linha "if __name__ == '__main__':"
    if "if __name__ == '__main__':" in content:
        # Inserir os métodos antes dessa linha
        new_content = content.replace("if __name__ == '__main__':", METHODS + "\n\nif __name__ == '__main__':")
        with open(MAIN_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ Métodos inseridos com sucesso!")
    else:
        print("❌ Não foi possível encontrar a marcação 'if __name__'. Inserindo no final do arquivo.")
        # Inserir no final
        with open(MAIN_FILE, "a", encoding="utf-8") as f:
            f.write(METHODS)
        print("✅ Métodos adicionados ao final do arquivo.")

    print("▶️ Execute 'python -m core.main' para testar.")
    print("🧹 Após testar, você pode excluir este script.")

if __name__ == "__main__":
    main()
