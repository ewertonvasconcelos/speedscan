#!/bin/bash
# Script para corrigir a execução dos cards no SpeedScan
# Executar dentro do diretório do projeto (~/speedscan/speedscan)

set -e

echo "🔧 Aplicando correções nos cards..."

# Backup do main.py
cp core/main.py core/main.py.bak.$(date +%s)

# ============================================================
# 1. Substituir o método _run_ping por uma versão com debug
# ============================================================
sed -i '/def _run_ping/,/^    def/ {
    /def _run_ping/,/^    def/ c\
    def _run_ping(self, log):\n\
        print("DEBUG _run_ping: executando ping")\n\
        self._run_subprocess(["ping", "-c", "4", "google.com"], log, tag="ping")
}' core/main.py

# ============================================================
# 2. Substituir o método _run_subprocess por uma versão robusta
# ============================================================
sed -i '/def _run_subprocess/,/^    def/ {
    /def _run_subprocess/,/^    def/ c\
    def _run_subprocess(self, cmd, log, use_sudo=False, shell=False, tag=None):\n\
        try:\n\
            print(f"DEBUG _run_subprocess: executando {cmd}")\n\
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
            log.insert("end", self._("Error executing command: {e}\\n").format(e=e))
}' core/main.py

# ============================================================
# 3. Garantir que a variável _btn_shown seja resetada em run_card_action
# ============================================================
sed -i '/def run_card_action/,/threading.Thread/ {
    /log.delete/a \        self._btn_shown = False
}' core/main.py

# ============================================================
# 4. Adicionar um método _show_detail_button se não existir
# ============================================================
if ! grep -q "def _show_detail_button" core/main.py; then
    sed -i '/def run_card_action/i \    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)\n' core/main.py
fi

# ============================================================
# 5. Ajustar toggle_console para que o botão suma ao fechar
# ============================================================
sed -i '/def toggle_console/,/^    def/ {
    /def toggle_console/,/^    def/ c\
    def toggle_console(self, tag):\n\
        btn = self.detail_buttons.get(tag)\n\
        log = self.logs.get(tag)\n\
        if not btn or not log:\n\
            return\n\
        if self.consoles_visible.get(tag, False):\n\
            log.pack_forget()\n\
            btn.pack_forget()\n\
            btn.configure(text=self._("Details ▼"))\n\
            self.consoles_visible[tag] = False\n\
        else:\n\
            log.pack(fill="x", expand=True, padx=5, before=btn)\n\
            btn.configure(text=self._("Hide Details ▲"))\n\
            self.consoles_visible[tag] = True
}' core/main.py

echo "✅ Correções aplicadas. Execute o programa com: python -m core.main"
