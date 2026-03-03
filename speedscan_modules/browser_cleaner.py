"""
SpeedScan - Limpeza de Cache de Navegadores
============================================
Detecta e limpa cache de Chrome, Firefox, Edge, Brave e Opera.
Compatível com Linux, Windows e macOS.

Dependências:
    Apenas biblioteca padrão Python (os, shutil, pathlib)
"""

import os
import shutil
import platform
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrowserInfo:
    """Informações de um navegador detectado."""
    name: str
    icon: str
    cache_paths: list[Path]
    data_paths: list[Path]      # Para outros dados (cookies, histórico) — apenas informativo
    is_installed: bool
    cache_size_bytes: int = 0

    @property
    def cache_size_mb(self) -> float:
        return round(self.cache_size_bytes / (1024 * 1024), 2)

    @property
    def cache_size_label(self) -> str:
        if self.cache_size_bytes >= 1024 ** 3:
            return f"{self.cache_size_bytes / (1024**3):.1f} GB"
        elif self.cache_size_bytes >= 1024 ** 2:
            return f"{self.cache_size_bytes / (1024**2):.1f} MB"
        elif self.cache_size_bytes >= 1024:
            return f"{self.cache_size_bytes / 1024:.1f} KB"
        return f"{self.cache_size_bytes} B"


@dataclass
class CleanResult:
    """Resultado da limpeza de um navegador."""
    browser_name: str
    bytes_freed: int
    files_removed: int
    errors: list[str] = field(default_factory=list)
    success: bool = True

    @property
    def mb_freed(self) -> float:
        return round(self.bytes_freed / (1024 * 1024), 2)


class BrowserCleaner:
    """
    Detecta e limpa cache de navegadores populares.

    Exemplo de uso:
        cleaner = BrowserCleaner()
        browsers = cleaner.detect_browsers()
        for b in browsers:
            if b.is_installed:
                print(f"{b.icon} {b.name}: {b.cache_size_label}")

        results = cleaner.clean_all()
        total = sum(r.bytes_freed for r in results)
        print(f"Total liberado: {total / (1024*1024):.1f} MB")
    """

    def __init__(self):
        self._system = platform.system()
        self._home = Path.home()
        self._browsers = self._define_browsers()

    def _define_browsers(self) -> dict[str, dict]:
        """Define os caminhos de cache por navegador e plataforma."""
        system = self._system
        home = self._home

        browsers = {}

        # ===================== GOOGLE CHROME =====================
        if system == "Linux":
            chrome_cache = [
                home / ".cache" / "google-chrome",
                home / ".cache" / "chromium",
            ]
        elif system == "Windows":
            local_app = Path(os.environ.get("LOCALAPPDATA", ""))
            chrome_cache = [
                local_app / "Google" / "Chrome" / "User Data" / "Default" / "Cache",
                local_app / "Google" / "Chrome" / "User Data" / "Default" / "Code Cache",
                local_app / "Google" / "Chrome" / "User Data" / "Default" / "GPUCache",
            ]
        elif system == "Darwin":
            chrome_cache = [
                home / "Library" / "Caches" / "Google" / "Chrome",
            ]
        else:
            chrome_cache = []

        browsers["chrome"] = {
            "name": "Google Chrome",
            "icon": "🌐",
            "cache_paths": chrome_cache,
        }

        # ===================== FIREFOX =====================
        if system == "Linux":
            ff_base = home / ".mozilla" / "firefox"
            ff_snap = home / "snap" / "firefox" / "common" / ".mozilla" / "firefox"
            ff_flatpak = home / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox"
        elif system == "Windows":
            appdata = Path(os.environ.get("APPDATA", ""))
            ff_base = appdata / "Mozilla" / "Firefox" / "Profiles"
            ff_snap = None
            ff_flatpak = None
        elif system == "Darwin":
            ff_base = home / "Library" / "Application Support" / "Firefox" / "Profiles"
            ff_snap = None
            ff_flatpak = None
        else:
            ff_base = None

        ff_cache_paths = []
        for ff_root in [ff_base, ff_snap, ff_flatpak]:
            if ff_root and ff_root.exists():
                # Encontrar todos os perfis
                for profile_dir in ff_root.glob("*.default*"):
                    ff_cache_paths.append(profile_dir / "cache2")
                    ff_cache_paths.append(profile_dir / "startupCache")
                    ff_cache_paths.append(profile_dir / "thumbnails")

                if system == "Linux":
                    # Cache pode estar em .cache separado
                    ff_cache_root = home / ".cache" / "mozilla" / "firefox"
                    if ff_cache_root.exists():
                        ff_cache_paths.extend(ff_cache_root.glob("*.default*"))

        browsers["firefox"] = {
            "name": "Mozilla Firefox",
            "icon": "🦊",
            "cache_paths": ff_cache_paths,
        }

        # ===================== MICROSOFT EDGE =====================
        if system == "Linux":
            edge_cache = [home / ".cache" / "microsoft-edge"]
        elif system == "Windows":
            local_app = Path(os.environ.get("LOCALAPPDATA", ""))
            edge_cache = [
                local_app / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache",
                local_app / "Microsoft" / "Edge" / "User Data" / "Default" / "Code Cache",
            ]
        elif system == "Darwin":
            edge_cache = [home / "Library" / "Caches" / "Microsoft Edge"]
        else:
            edge_cache = []

        browsers["edge"] = {
            "name": "Microsoft Edge",
            "icon": "🔷",
            "cache_paths": edge_cache,
        }

        # ===================== BRAVE =====================
        if system == "Linux":
            brave_cache = [home / ".cache" / "BraveSoftware" / "Brave-Browser"]
        elif system == "Windows":
            local_app = Path(os.environ.get("LOCALAPPDATA", ""))
            brave_cache = [
                local_app / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "Cache",
                local_app / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "Code Cache",
            ]
        elif system == "Darwin":
            brave_cache = [home / "Library" / "Caches" / "BraveSoftware" / "Brave-Browser"]
        else:
            brave_cache = []

        browsers["brave"] = {
            "name": "Brave Browser",
            "icon": "🦁",
            "cache_paths": brave_cache,
        }

        # ===================== OPERA =====================
        if system == "Linux":
            opera_cache = [home / ".cache" / "opera"]
        elif system == "Windows":
            appdata = Path(os.environ.get("APPDATA", ""))
            opera_cache = [appdata / "Opera Software" / "Opera Stable" / "Cache"]
        elif system == "Darwin":
            opera_cache = [home / "Library" / "Caches" / "com.operasoftware.Opera"]
        else:
            opera_cache = []

        browsers["opera"] = {
            "name": "Opera",
            "icon": "🎭",
            "cache_paths": opera_cache,
        }

        # ===================== VIVALDI =====================
        if system == "Linux":
            vivaldi_cache = [home / ".cache" / "vivaldi"]
        elif system == "Windows":
            local_app = Path(os.environ.get("LOCALAPPDATA", ""))
            vivaldi_cache = [local_app / "Vivaldi" / "User Data" / "Default" / "Cache"]
        elif system == "Darwin":
            vivaldi_cache = [home / "Library" / "Caches" / "Vivaldi"]
        else:
            vivaldi_cache = []

        browsers["vivaldi"] = {
            "name": "Vivaldi",
            "icon": "🎵",
            "cache_paths": vivaldi_cache,
        }

        return browsers

    def _get_dir_size(self, path: Path) -> int:
        """Calcula o tamanho total de um diretório."""
        total = 0
        try:
            for entry in path.rglob("*"):
                try:
                    if entry.is_file():
                        total += entry.stat().st_size
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass
        return total

    def detect_browsers(self) -> list[BrowserInfo]:
        """
        Detecta navegadores instalados e calcula tamanho do cache.

        Returns:
            Lista de BrowserInfo com informações de cada navegador.
        """
        result = []
        for browser_id, config in self._browsers.items():
            existing_paths = [p for p in config["cache_paths"] if isinstance(p, Path) and p.exists()]
            is_installed = len(existing_paths) > 0

            # Calcular tamanho do cache
            cache_size = 0
            if is_installed:
                for path in existing_paths:
                    if path.is_dir():
                        cache_size += self._get_dir_size(path)
                    elif path.is_file():
                        try:
                            cache_size += path.stat().st_size
                        except OSError:
                            pass

            result.append(BrowserInfo(
                name=config["name"],
                icon=config["icon"],
                cache_paths=existing_paths,
                data_paths=[],
                is_installed=is_installed,
                cache_size_bytes=cache_size,
            ))

        return sorted(result, key=lambda b: b.cache_size_bytes, reverse=True)

    def get_total_cache_size(self) -> int:
        """Retorna o tamanho total do cache de todos os navegadores (bytes)."""
        return sum(b.cache_size_bytes for b in self.detect_browsers() if b.is_installed)

    def clean_browser(self, browser_id: str) -> CleanResult:
        """
        Limpa o cache de um navegador específico.

        Args:
            browser_id: ID do navegador ('chrome', 'firefox', 'edge', etc.)

        Returns:
            CleanResult com bytes liberados e erros
        """
        config = self._browsers.get(browser_id)
        if not config:
            return CleanResult(browser_name=browser_id, bytes_freed=0,
                               files_removed=0, errors=["Navegador não reconhecido"])

        total_freed = 0
        files_removed = 0
        errors = []

        for cache_path in config["cache_paths"]:
            if not isinstance(cache_path, Path) or not cache_path.exists():
                continue
            try:
                # Calcula tamanho antes
                size_before = self._get_dir_size(cache_path) if cache_path.is_dir() else cache_path.stat().st_size

                if cache_path.is_dir():
                    # Remove conteúdo mas mantém o diretório
                    for item in cache_path.iterdir():
                        try:
                            size = self._get_dir_size(item) if item.is_dir() else item.stat().st_size
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                            total_freed += size
                            files_removed += 1
                        except (PermissionError, OSError) as e:
                            errors.append(f"Não foi possível remover {item.name}: {e}")
                elif cache_path.is_file():
                    try:
                        total_freed += cache_path.stat().st_size
                        cache_path.unlink()
                        files_removed += 1
                    except (PermissionError, OSError) as e:
                        errors.append(f"Arquivo bloqueado: {cache_path.name}")

            except Exception as e:
                errors.append(f"Erro ao limpar {cache_path}: {str(e)}")

        return CleanResult(
            browser_name=config["name"],
            bytes_freed=total_freed,
            files_removed=files_removed,
            errors=errors,
            success=len(errors) == 0 or total_freed > 0,
        )

    def clean_all(self, on_progress=None) -> list[CleanResult]:
        """
        Limpa o cache de todos os navegadores detectados.

        Args:
            on_progress: Callback(browser_name, step, total)

        Returns:
            Lista de CleanResult por navegador.
        """
        browsers = [b for b in self.detect_browsers() if b.is_installed]
        results = []

        for i, browser in enumerate(browsers):
            if on_progress:
                on_progress(browser.name, i + 1, len(browsers))

            # Encontra o ID do navegador pelo nome
            browser_id = next(
                (k for k, v in self._browsers.items() if v["name"] == browser.name),
                None
            )
            if browser_id:
                result = self.clean_browser(browser_id)
                results.append(result)

        return results


if __name__ == "__main__":
    print("=== SpeedScan — Limpeza de Cache de Navegadores ===\n")

    cleaner = BrowserCleaner()

    print("🔍 Detectando navegadores instalados...\n")
    browsers = cleaner.detect_browsers()

    installed = [b for b in browsers if b.is_installed]
    if not installed:
        print("Nenhum navegador detectado.")
    else:
        print(f"Encontrados {len(installed)} navegador(es):\n")
        for b in installed:
            print(f"  {b.icon} {b.name:<20} Cache: {b.cache_size_label}")

        total_mb = sum(b.cache_size_bytes for b in installed) / (1024 * 1024)
        print(f"\n  📦 Total de cache: {total_mb:.1f} MB")

        print("\n" + "="*40)
        resposta = input("Deseja limpar todo o cache? [s/N]: ").strip().lower()
        if resposta == "s":
            print("\n🧹 Limpando...\n")

            def progresso(name, step, total):
                print(f"  [{step}/{total}] Limpando {name}...")

            results = cleaner.clean_all(on_progress=progresso)
            total_freed = sum(r.bytes_freed for r in results)

            print(f"\n✅ Concluído!")
            for r in results:
                if r.bytes_freed > 0:
                    print(f"  {r.browser_name}: {r.mb_freed:.1f} MB liberados")
            print(f"\n🎉 Total liberado: {total_freed / (1024*1024):.1f} MB")
        else:
            print("Operação cancelada.")
