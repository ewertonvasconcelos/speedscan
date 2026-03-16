#!/bin/bash
# Correção definitiva dos cards – adiciona prints e garante execução

set -e

cd ~/speedscan/speedscan

# Backup
cp core/main.py core/main.py.bak.$(date +%s)
echo "✅ Backup criado."

# ============================================================
# 1. Garantir que o método run_card_action tenha prints
# ============================================================
sed -i '/def run_card_action/,/threading.Thread/ {
    /log.delete/a \        print(f"\\n>>> CARD CLICADO: cmd={cmd}, tag={tag}, is_dns={is_dns}")\n        import sys; sys.stdout.flush()
}' core/main.py

# ============================================================
# 2. Garantir que _execute_command tenha prints
# ============================================================
sed -i '/def _execute_command/,/action_map/ {
    /action_map = {/i \        print(f"  -> _execute_command chamado com cmd={cmd}, tag={tag}")\n        sys.stdout.flush()
}' core/main.py

# ============================================================
# 3. Garantir que o método específico (ex: _run_ping) seja chamado
# ============================================================
sed -i '/def _run_ping/,/^    def/ {
    /def _run_ping/,/^    def/ c\
    def _run_ping(self, log):\n\
        print("    -> _run_ping sendo executado")\n\
        sys.stdout.flush()\n\
        self._run_subprocess(["ping", "-c", "4", "google.com"], log, tag="ping")
}' core/main.py

# ============================================================
# 4. Garantir que _run_subprocess tenha prints e trate erros
# ============================================================
sed -i '/def _run_subprocess/,/^    def/ {
    /def _run_subprocess/,/^    def/ c\
    def _run_subprocess(self, cmd, log, use_sudo=False, shell=False, tag=None):\n\
        print(f"      -> _run_subprocess: cmd={cmd}")\n\
        sys.stdout.flush()\n\
        try:\n\
            if use_sudo and self.SO == "Linux":\n\
                if isinstance(cmd, list):\n\
                    cmd = ["sudo"] + cmd\n\
                else:\n\
                    cmd = "sudo " + cmd\n\
            proc = subprocess.Popen(cmd,\n\
                                    stdout=subprocess.PIPE,\n\
                                    stderr=subprocess.STDOUT,\n\
                                    text=True,\n\
                                    bufsize=1,\n\
                                    shell=shell)\n\
            for line in proc.stdout:\n\
                if not self._btn_shown:\n\
                    self._show_detail_button(tag)\n\
                    self._btn_shown = True\n\
                log.insert("end", line)\n\
            proc.wait()\n\
        except Exception as e:\n\
            print(f"      !! ERRO no subprocess: {e}")\n\
            sys.stdout.flush()\n\
            log.insert("end", self._("Error executing command: {e}\\n").format(e=e))
}' core/main.py

# ============================================================
# 5. Garantir que a criação dos botões use o callback correto
# ============================================================
sed -i 's/command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d)/command=lambda c=cmd, t=tag_prefix, d=is_dns: self.run_card_action(c, t, d)/g' core/ui.py

echo "✅ Correções aplicadas. Execute o programa e veja os prints."
