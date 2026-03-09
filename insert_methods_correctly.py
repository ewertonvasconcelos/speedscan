#!/usr/bin/env python3
"""
Insere os métodos faltantes DENTRO da classe SpeedScan, antes do final da classe.
"""

import shutil
import re
from pathlib import Path

MAIN_FILE = Path("core/main.py")
BACKUP_FILE = Path("core/main.py.bak.correct")

# Métodos a serem inseridos (com indentação de 4 espaços)
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
    print("🔧 Inserindo métodos dentro da classe SpeedScan...")

    if not MAIN_FILE.exists():
        print("❌ core/main.py não encontrado!")
        return

    shutil.copy(MAIN_FILE, BACKUP_FILE)
    print(f"✅ Backup: {BACKUP_FILE}")

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Procurar a última linha da classe (antes do if __name__)
    # Estratégia: encontrar a última linha que não está indentada (nível 0) após a definição da classe
    # E que seja antes de "if __name__"
    insert_index = None
    in_class = False
    class_indent = 0
    for i, line in enumerate(lines):
        if re.match(r'^class SpeedScan\(ctk\.CTk\):', line):
            in_class = True
            # a indentação da classe é 0, os métodos internos têm indentação maior
            continue
        if in_class:
            # Verificar se a linha tem indentação menor que a dos métodos (fim da classe)
            # Consideramos que a classe termina quando encontramos uma linha não indentada
            # (ou com indentação 0) e que não seja comentário ou linha em branco
            stripped = line.lstrip()
            if stripped and not stripped.startswith('#'):
                indent = len(line) - len(stripped)
                if indent <= class_indent:
                    # Encontramos uma linha com indentação menor ou igual à da classe
                    # Isso pode ser o final da classe
                    # Mas precisamos garantir que não é um método ou atributo
                    # Vamos verificar se é algo como "if __name__" ou outra definição
                    if 'if __name__' in line or 'def ' not in line:
                        insert_index = i
                        break
    if insert_index is None:
        # Se não encontrar, procurar por "if __name__"
        for i, line in enumerate(lines):
            if 'if __name__' in line:
                insert_index = i
                break
    if insert_index is None:
        print("❌ Não foi possível localizar o local de inserção.")
        return

    # Inserir os métodos antes da linha encontrada
    methods_lines = METHODS.splitlines(True)
    # Ajustar indentação: os métodos já têm 4 espaços no início, mas precisamos garantir
    # que estejam no mesmo nível dos outros métodos (provavelmente 4 ou 8 espaços)
    # Vamos usar a indentação da linha anterior (que deve ser um método)
    # Como fallback, usamos 4 espaços.
    indent = '    '
    methods_lines_indented = [indent + line if line.strip() and not line.startswith(' ') else line for line in methods_lines]

    new_lines = lines[:insert_index] + methods_lines_indented + lines[insert_index:]

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("✅ Métodos inseridos corretamente dentro da classe!")
    print("▶️ Execute 'python -m core.main' para testar.")
    print("🧹 Após testar, pode excluir este script.")

if __name__ == "__main__":
    main()
