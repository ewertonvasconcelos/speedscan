#!/bin/bash
# Adiciona prints de depuração no __init__ da classe SpeedScan

set -e

ARQUIVO="core/main.py"
BACKUP="${ARQUIVO}.bak_init_$(date +%Y%m%d_%H%M%S)"
cp "$ARQUIVO" "$BACKUP"
echo "✅ Backup criado: $BACKUP"

# Insere print no início do __init__
sed -i '/def __init__(self):/a\        print("DEBUG: __init__ - inicio")' "$ARQUIVO"

# Após self.runner
sed -i '/self.runner = CommandRunner(self.SO)/a\        print("DEBUG: __init__ - runner criado")' "$ARQUIVO"

# Após self.hw
sed -i '/self.hw = HardwareInfo(self.SO, self.runner)/a\        print("DEBUG: __init__ - hardware info criado")' "$ARQUIVO"

# Após self.config
sed -i '/self.config = self._load_config()/a\        print("DEBUG: __init__ - config carregado")' "$ARQUIVO"

# Após self._ = get_translation(...)
sed -i '/self._ = get_translation(self.config.get(.language., .pt_BR.))/a\        print("DEBUG: __init__ - tradução carregada")' "$ARQUIVO"

# Após self.update_theme_vars()
sed -i '/self.update_theme_vars()/a\        print("DEBUG: __init__ - tema atualizado")' "$ARQUIVO"

# Após self.title(...)
sed -i '/self.title(self._("SpeedScan") + f" {config.VERSION}")/a\        print("DEBUG: __init__ - título definido")' "$ARQUIVO"

# Após self.configure(fg_color=self.bg_color)
sed -i '/self.configure(fg_color=self.bg_color)/a\        print("DEBUG: __init__ - cor de fundo configurada")' "$ARQUIVO"

# Após self.minsize
sed -i '/self.minsize(900, 500)/a\        print("DEBUG: __init__ - tamanho mínimo definido")' "$ARQUIVO"

# Após self.apply_ui_scale()
sed -i '/self.apply_ui_scale()/a\        print("DEBUG: __init__ - escala aplicada")' "$ARQUIVO"

# Após criar health_monitor
sed -i '/self.health_monitor = HealthScore()/a\        print("DEBUG: __init__ - health monitor criado")' "$ARQUIVO"

# Após criar temp_monitor
sed -i '/self.temp_monitor = TemperatureMonitor()/a\        print("DEBUG: __init__ - temp monitor criado")' "$ARQUIVO"

# Após criar smart_monitor
sed -i '/self.smart_monitor = SmartMonitor()/a\        print("DEBUG: __init__ - smart monitor criado")' "$ARQUIVO"

# Após criar browser_cleaner
sed -i '/self.browser_cleaner = BrowserCleaner()/a\        print("DEBUG: __init__ - browser cleaner criado")' "$ARQUIVO"

# Após criar speed_tester
sed -i '/self.speed_tester = SpeedTester()/a\        print("DEBUG: __init__ - speed tester criado")' "$ARQUIVO"

# Após criar proc_manager
sed -i '/self.proc_manager = ProcessManager()/a\        print("DEBUG: __init__ - process manager criado")' "$ARQUIVO"

# Após criar metrics_collector
sed -i '/self.metrics_collector = MetricsCollector(interval=5)/a\        print("DEBUG: __init__ - metrics collector criado")' "$ARQUIVO"

# Após criar metrics_db
sed -i '/self.metrics_db = MetricsDB()/a\        print("DEBUG: __init__ - metrics db criado")' "$ARQUIVO"

# Após criar lan_scanner
sed -i '/self.lan_scanner = LANScanner()/a\        print("DEBUG: __init__ - lan scanner criado")' "$ARQUIVO"

# Após criar ai_proactive
sed -i '/self.ai_proactive = AIProactive(self.metrics_db, self.health_monitor)/a\        print("DEBUG: __init__ - ai proactive criado")' "$ARQUIVO"

# Após criar security_scanner
sed -i '/self.security_scanner = SecurityScanner(self.SO)/a\        print("DEBUG: __init__ - security scanner criado")' "$ARQUIVO"

# Após criar lan_cache
sed -i '/self.lan_cache = LANCacheManager(self.SO)/a\        print("DEBUG: __init__ - lan cache criado")' "$ARQUIVO"

# Após criar cookie_manager
sed -i '/self.cookie_manager = CookieManager()/a\        print("DEBUG: __init__ - cookie manager criado")' "$ARQUIVO"

# Após criar trash_manager
sed -i '/self.trash_manager = TrashManager()/a\        print("DEBUG: __init__ - trash manager criado")' "$ARQUIVO"

# Após windows_cleaner
sed -i '/self.windows_cleaner = WindowsCleaner()/a\        print("DEBUG: __init__ - windows cleaner criado")' "$ARQUIVO" 2>/dev/null || true

# Após metrics_collector.start()
sed -i '/self.metrics_collector.start()/a\        print("DEBUG: __init__ - metrics collector iniciado")' "$ARQUIVO"

# Após proc_manager.start_monitoring()
sed -i '/self.proc_manager.start_monitoring()/a\        print("DEBUG: __init__ - process monitoring iniciado")' "$ARQUIVO"

# Após action_handler
sed -i '/self.action_handler = ActionHandler(self)/a\        print("DEBUG: __init__ - action handler criado")' "$ARQUIVO"

# Após grid_columnconfigure
sed -i '/self.grid_columnconfigure(1, weight=1)/a\        print("DEBUG: __init__ - grid configurado")' "$ARQUIVO"

# Após grid_rowconfigure
sed -i '/self.grid_rowconfigure(0, weight=1)/a\        print("DEBUG: __init__ - grid configurado")' "$ARQUIVO"

# Após _build_sidebar()
sed -i '/self._build_sidebar()/a\        print("DEBUG: __init__ - sidebar construída")' "$ARQUIVO"

# Após criar container
sed -i '/self.container = ctk.CTkFrame(self, fg_color="transparent")/a\        print("DEBUG: __init__ - container criado")' "$ARQUIVO"

# Após container.grid(...)
sed -i '/self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)/a\        print("DEBUG: __init__ - container posicionado")' "$ARQUIVO"

# Após container.grid_columnconfigure
sed -i '/self.container.grid_columnconfigure(0, weight=1)/a\        print("DEBUG: __init__ - container column config")' "$ARQUIVO"

# Após container.grid_rowconfigure
sed -i '/self.container.grid_rowconfigure(0, weight=1)/a\        print("DEBUG: __init__ - container row config")' "$ARQUIVO"

# Após self.frames = {}
sed -i '/self.frames = {}/a\        print("DEBUG: __init__ - frames dict criado")' "$ARQUIVO"

# Após o loop for btn in self.detail_buttons.values()
sed -i '/for btn in self.detail_buttons.values():/a\        print("DEBUG: __init__ - antes do loop de detalhes")' "$ARQUIVO"
sed -i '/            btn.pack_forget()/a\        print("DEBUG: __init__ - dentro do loop de detalhes")' "$ARQUIVO"

# Após self.consoles_visible
sed -i '/self.consoles_visible = {tag: False for tag in self.detail_buttons.keys()}/a\        print("DEBUG: __init__ - consoles_visible criado")' "$ARQUIVO"

# Após self.show_frame("dashboard")
sed -i '/self.show_frame("dashboard")/a\        print("DEBUG: __init__ - show_frame chamado")' "$ARQUIVO"

# Após _setup_bindings
sed -i '/self._setup_bindings()/a\        print("DEBUG: __init__ - bindings configurados")' "$ARQUIVO"

# Após threading.Thread
sed -i '/threading.Thread(target=self._monitor_loop, daemon=True).start()/a\        print("DEBUG: __init__ - monitor thread iniciada")' "$ARQUIVO"

# Após _check_process_queue
sed -i '/self._check_process_queue()/a\        print("DEBUG: __init__ - process queue checked")' "$ARQUIVO"

# Após after(200, ...)
sed -i '/self.after(200, self._restore_window_state)/a\        print("DEBUG: __init__ - after para restore window")' "$ARQUIVO"

# Após protocol
sed -i '/self.protocol("WM_DELETE_WINDOW", self._on_closing)/a\        print("DEBUG: __init__ - protocol configurado")' "$ARQUIVO"

# Após after(500, ...)
sed -i '/self.after(500, self._check_first_run)/a\        print("DEBUG: __init__ - after para first run")' "$ARQUIVO"

echo "✅ Prints adicionados. Execute o programa e observe onde para."
