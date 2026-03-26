#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat interface for integration with AI providers (Ollama, OpenAI, DeepSeek, etc.)
Version 1.0.0
"""
import customtkinter as ctk
import threading
import requests
import logging

class ChatFrame(ctk.CTkFrame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.configure(fg_color="transparent")

        self.history = []
        self.current_ai = app_instance.config_data.get("ai", {}).get("provider", "ollama")
        self.ai_model = app_instance.config_data.get("ai", {}).get("model", "llama3.2")
        # Tentar múltiplas URLs para Ollama (localhost, host.docker.internal, etc.)
        default_endpoint = app_instance.config_data.get("ai", {}).get("endpoint", "http://localhost:11434")
        # Tentar URLs alternativas para container
        self.endpoint = self._try_ollama_endpoints(default_endpoint)
        self.api_key = app_instance.config_data.get("ai", {}).get("api_key", "")

        # Get colors safely, with fallback values
        try:
            light_bg = getattr(self.app, 'light_bg', '#2b2b2b')
            text_color = getattr(self.app, 'text_color', '#ffffff')
            acc_color = getattr(self.app, 'acc_color', '#1f6aa5')
        except Exception as e:
            logging.error(f"Error getting theme colors: {e}")
            light_bg = '#2b2b2b'
            text_color = '#ffffff'
            acc_color = '#1f6aa5'

        self.chat_display = ctk.CTkTextbox(self, wrap="word", font=("Inter", 12),
                                            fg_color=light_bg,
                                            text_color=text_color)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        # Provider selector
        provider_frame = ctk.CTkFrame(self, fg_color="transparent")
        provider_frame.pack(fill="x", padx=10, pady=(5,0))
        ctk.CTkLabel(provider_frame, text="Provider:", font=("Inter", 12)).pack(side="left", padx=5)
        
        # Available providers
        self.providers = {
            "ollama": "Ollama (Local)",
            "openai": "OpenAI (ChatGPT)",
            "deepseek": "DeepSeek",
            "anthropic": "Anthropic (Claude)",
        }
        self.provider_var = ctk.StringVar(value=self.providers.get(self.current_ai, "Ollama (Local)"))
        provider_menu = ctk.CTkOptionMenu(provider_frame, values=list(self.providers.values()),
                                         variable=self.provider_var, width=180,
                                         command=self._on_provider_change)
        provider_menu.pack(side="left", padx=5)

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0,10))

        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Type your message...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(input_frame, text="Send", command=self.send_message,
                                      fg_color=acc_color, cursor="hand2")
        self.send_btn.pack(side="right")

        self._add_message("system", "🤖 SpeedScan AI Assistant\n"
                          "Type /help for available commands.\n"
                          f"Current provider: {self.current_ai}\n"
                          f"Model: {self.ai_model}\n\n"
                          "Note: Make sure Ollama is running for local AI.")

    def _try_ollama_endpoints(self, default_endpoint):
        """Tenta múltiplos endpoints para encontrar Ollama."""
        endpoints = [
            default_endpoint,
            "http://localhost:11434",
            "http://host.containers.internal:11434",
            "http://172.17.0.1:11434",  # Docker default bridge
        ]
        for endpoint in endpoints:
            try:
                response = requests.get(f"{endpoint}/api/tags", timeout=2)
                if response.status_code == 200:
                    print(f"DEBUG: Ollama encontrado em {endpoint}")
                    return endpoint
            except:
                continue
        print(f"DEBUG: Nenhum endpoint de Ollama funcionou, usando {default_endpoint}")
        return default_endpoint

    def _on_provider_change(self, choice):
        # Find provider key from value
        for key, value in self.providers.items():
            if value == choice:
                self.current_ai = key
                break
        self._add_message("system", f"✅ Provider changed to: {choice}\nPlease enter your API key in Settings if needed.")

    def _add_message(self, role, content):
        self.chat_display.configure(state="normal")
        if role == "user":
            self.chat_display.insert("end", f"You: {content}\n\n")
        elif role == "assistant":
            self.chat_display.insert("end", f"AI: {content}\n\n")
        elif role == "system":
            self.chat_display.insert("end", f"{content}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        self.history.append({"role": role, "content": content})

    def send_message(self):
        msg = self.message_entry.get().strip()
        if not msg:
            return
        self.message_entry.delete(0, "end")
        self._add_message("user", msg)

        if msg.startswith("/"):
            self._handle_command(msg)
            return

        threading.Thread(target=self._get_ai_response, args=(msg,), daemon=True).start()

    def _handle_command(self, cmd):
        if cmd == "/help":
            self._add_message("system", "Available commands:\n"
                              "/help - show this help\n"
                              "/clear - clear chat\n"
                              "/model - show current model\n"
                              "/test - test Ollama connection\n"
                              "/trash - list trash items\n"
                              "/emptytrash - empty trash")
        elif cmd == "/clear":
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            self.history = []
            self._add_message("system", "🗑️ Chat cleared.")
        elif cmd == "/model":
            self._add_message("system", f"Current model: {self.current_ai} ({self.ai_model})\nEndpoint: {self.endpoint}")
        elif cmd == "/test":
            self._add_message("system", "🔄 Testing connection to Ollama...")
            threading.Thread(target=self._test_connection, daemon=True).start()
        elif cmd == "/trash":
            items = self.app.trash_manager.list_trash()
            if items:
                msg = "Items in trash:\n" + "\n".join([f"{i['name']} (original: {i['original']})" for i in items])
            else:
                msg = "Trash is empty."
            self._add_message("system", msg)
        elif cmd == "/emptytrash":
            self.app.trash_manager.empty_trash()
            self._add_message("system", "🗑️ Trash emptied.")
        else:
            self._add_message("system", f"Unknown command: {cmd}")

    def _get_ai_response(self, user_message):
        if self.current_ai == "ollama":
            self._query_ollama(user_message)
        elif self.current_ai == "openai":
            self._query_openai(user_message)
        elif self.current_ai == "deepseek":
            self._query_deepseek(user_message)
        else:
            self.app.after(0, lambda: self._add_message("system", "⚠️ Provider not supported."))

    def _query_ollama(self, message):
        try:
            messages = [{"role": m["role"], "content": m["content"]} for m in self.history if m["role"] != "system"]
            payload = {
                "model": self.ai_model,
                "messages": messages,
                "stream": False
            }
            # First check if Ollama is reachable
            try:
                test_response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
                if test_response.status_code != 200:
                    self.app.after(0, lambda: self._add_message("system", f"⚠️ Ollama returned status {test_response.status_code}. Is it running?"))
                    return
            except requests.exceptions.ConnectionError:
                self.app.after(0, lambda: self._add_message("system", "⚠️ Cannot connect to Ollama. Make sure Ollama is running:\n\n  ollama serve\n\nThen try again."))
                return
            except requests.exceptions.Timeout:
                self.app.after(0, lambda: self._add_message("system", "⚠️ Connection to Ollama timed out."))
                return
            
            response = requests.post(f"{self.endpoint}/api/chat", json=payload, timeout=120)
            if response.status_code == 200:
                data = response.json()
                reply = data.get("message", {}).get("content", "No response.")
                self.app.after(0, lambda: self._add_message("assistant", reply))
            else:
                self.app.after(0, lambda: self._add_message("system", f"Error from Ollama: {response.status_code}"))
        except requests.exceptions.Timeout:
            logging.error("Ollama request timed out")
            self.app.after(0, lambda: self._add_message("system", "⚠️ Request timed out. Try a simpler query or check Ollama."))
        except Exception as e:
            logging.error(f"Error querying Ollama: {e}")
            self.app.after(0, lambda e=e: self._add_message("system", f"Error connecting to Ollama: {e}"))

    def _query_openai(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚠️ OpenAI not implemented. Configure your key."))

    def _query_deepseek(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚠️ DeepSeek not implemented."))

    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "unknown") for m in models]
                msg = f"✅ Connection successful!\nAvailable models: {', '.join(model_names) if model_names else 'none'}"
                self.app.after(0, lambda: self._add_message("system", msg))
            else:
                self.app.after(0, lambda: self._add_message("system", f"⚠️ Server returned status {response.status_code}"))
        except requests.exceptions.ConnectionError:
            self.app.after(0, lambda: self._add_message("system", "⚠️ Cannot connect to Ollama.\n\n"
                                                        "Make sure Ollama is running:\n"
                                                        "  ollama serve\n\n"
                                                        "Or install Ollama:\n"
                                                        "  curl -fsSL https://ollama.com/install.sh | sh"))
        except Exception as e:
            self.app.after(0, lambda e=e: self._add_message("system", f"⚠️ Error: {e}"))
