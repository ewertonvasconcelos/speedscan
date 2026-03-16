#!/usr/bin/env python3
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_prints_seguro")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Função para inserir linha após um padrão, respeitando indentação
def inserir_apos(linhas, padrao, nova_linha):
    for i, linha in enumerate(linhas):
        if padrao in linha:
            espacos = len(linha) - len(linha.lstrip())
            indent = ' ' * (espacos + 4)  # +4 para estar dentro do bloco
            linhas.insert(i+1, indent + nova_linha + '\n')
            print(f"Inserido após linha {i+1}: {nova_linha}")
            return True
    return False

# Lista de padrões e mensagens
insercoes = [
    ('def __init__(self):', 'print("DEBUG: __init__ - inicio")'),
    ('self.runner = CommandRunner(self.SO)', 'print("DEBUG: __init__ - runner criado")'),
    ('self.hw = HardwareInfo(self.SO, self.runner)', 'print("DEBUG: __init__ - hardware info criado")'),
    ('self.config = self._load_config()', 'print("DEBUG: __init__ - config carregado")'),
    ('self._ = get_translation(self.config.get(', 'print("DEBUG: __init__ - tradução carregada")'),
    ('self.update_theme_vars()', 'print("DEBUG: __init__ - tema atualizado")'),
    ('self.title(self._("SpeedScan") + f" {config.VERSION}")', 'print("DEBUG: __init__ - título definido")'),
    ('self.configure(fg_color=self.bg_color)', 'print("DEBUG: __init__ - cor de fundo configurada")'),
    ('self.minsize(900, 500)', 'print("DEBUG: __init__ - tamanho mínimo definido")'),
    ('self.apply_ui_scale()', 'print("DEBUG: __init__ - escala aplicada")'),
    ('self.health_monitor = HealthScore()', 'print("DEBUG: __init__ - health monitor criado")'),
    ('self.temp_monitor = TemperatureMonitor()', 'print("DEBUG: __init__ - temp monitor criado")'),
    ('self.smart_monitor = SmartMonitor()', 'print("DEBUG: __init__ - smart monitor criado")'),
    ('self.browser_cleaner = BrowserCleaner()', 'print("DEBUG: __init__ - browser cleaner criado")'),
    ('self.speed_tester = SpeedTester()', 'print("DEBUG: __init__ - speed tester criado")'),
    ('self.proc_manager = ProcessManager()', 'print("DEBUG: __init__ - process manager criado")'),
    ('self.metrics_collector = MetricsCollector(interval=5)', 'print("DEBUG: __init__ - metrics collector criado")'),
    ('self.metrics_db = MetricsDB()', 'print("DEBUG: __init__ - metrics db criado")'),
    ('self.lan_scanner = LANScanner()', 'print("DEBUG: __init__ - lan scanner criado")'),
    ('self.ai_proactive = AIProactive(self.metrics_db, self.health_monitor)', 'print("DEBUG: __init__ - ai proactive criado")'),
    ('self.security_scanner = SecurityScanner(self.SO)', 'print("DEBUG: __init__ - security scanner criado")'),
    ('self.lan_cache = LANCacheManager(self.SO)', 'print("DEBUG: __init__ - lan cache criado")'),
    ('self.cookie_manager = CookieManager()', 'print("DEBUG: __init__ - cookie manager criado")'),
    ('self.trash_manager = TrashManager()', 'print("DEBUG: __init__ - trash manager criado")'),
    ('self.metrics_collector.start()', 'print("DEBUG: __init__ - metrics collector iniciado")'),
    ('self.proc_manager.start_monitoring()', 'print("DEBUG: __init__ - process monitoring iniciado")'),
    ('self.action_handler = ActionHandler(self)', 'print("DEBUG: __init__ - action handler criado")'),
    ('self.grid_columnconfigure(1, weight=1)', 'print("DEBUG: __init__ - grid column config")'),
    ('self.grid_rowconfigure(0, weight=1)', 'print("DEBUG: __init__ - grid row config")'),
    ('self._build_sidebar()', 'print("DEBUG: __init__ - sidebar construída")'),
    ('self.container = ctk.CTkFrame(self, fg_color="transparent")', 'print("DEBUG: __init__ - container criado")'),
    ('self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)', 'print("DEBUG: __init__ - container posicionado")'),
    ('self.container.grid_columnconfigure(0, weight=1)', 'print("DEBUG: __init__ - container column config")'),
    ('self.container.grid_rowconfigure(0, weight=1)', 'print("DEBUG: __init__ - container row config")'),
    ('self.frames = {}', 'print("DEBUG: __init__ - frames dict criado")'),
    ('for btn in self.detail_buttons.values():', 'print("DEBUG: __init__ - antes do loop de detalhes")'),
    ('btn.pack_forget()', 'print("DEBUG: __init__ - dentro do loop de detalhes")'),
    ('self.consoles_visible = {tag: False for tag in self.detail_buttons.keys()}', 'print("DEBUG: __init__ - consoles_visible criado")'),
    ('self.show_frame("dashboard")', 'print("DEBUG: __init__ - show_frame chamado")'),
    ('self._setup_bindings()', 'print("DEBUG: __init__ - bindings configurados")'),
    ('threading.Thread(target=self._monitor_loop, daemon=True).start()', 'print("DEBUG: __init__ - monitor thread iniciada")'),
    ('self._check_process_queue()', 'print("DEBUG: __init__ - process queue checked")'),
    ('self.after(200, self._restore_window_state)', 'print("DEBUG: __init__ - after para restore window")'),
    ('self.protocol("WM_DELETE_WINDOW", self._on_closing)', 'print("DEBUG: __init__ - protocol configurado")'),
    ('self.after(500, self._check_first_run)', 'print("DEBUG: __init__ - after para first run")'),
]

for padrao, msg in insercoes:
    inserir_apos(linhas, padrao, msg)

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Prints inseridos. Execute o programa.")
