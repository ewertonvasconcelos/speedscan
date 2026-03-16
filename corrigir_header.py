#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_header")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Procurar pelo método _refresh_process_list
padrao = r'(def _refresh_process_list\(self\):.*?)(?=\n\s*def)'
match = re.search(padrao, conteudo, re.DOTALL)
if match:
    metodo_antigo = match.group(1)
    # Novo método com header corrigido
    novo_metodo = '''    def _refresh_process_list(self):
        procs = self.proc_manager.get_process_list()
        filtro = self.filter_entry.get().lower() if hasattr(self,'filter_entry') else ""
        if filtro:
            procs = [p for p in procs if filtro in p['name'].lower()]
        sort_key = self.sort_var.get() if hasattr(self,'sort_var') else "cpu_percent"
        reverse = self.reverse_var.get() if hasattr(self,'reverse_var') else True
        procs.sort(key=lambda x: x.get(sort_key,0), reverse=reverse)
        self.process_text.configure(state="normal")
        self.process_text.delete("1.0","end")
        header = f"{'PID':>7} {'CPU%':>6} {'MEM%':>6} {'STATUS':>8} {'NICE':>4} {'USUÁRIO':<10} {'NOME'}\\n"
        self.process_text.insert("end", header)
        self.process_text.tag_add("header","1.0","1.end")
        self.process_text.tag_config("header", foreground=self.acc_color)
        for p in procs:
            linha = f"{p['pid']:7d} {p['cpu_percent']:6.1f} {p['memory_percent']:6.1f} {p['status']:>8} {p['nice']:4d} {p['username']:<10} {p['name']}\\n"
            self.process_text.insert("end", linha)
        self.process_text.configure(state="disabled")
        self._current_processes = procs'''
    conteudo = conteudo.replace(metodo_antigo, novo_metodo)
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print("Método _refresh_process_list corrigido.")
else:
    print("Método _refresh_process_list não encontrado.")
