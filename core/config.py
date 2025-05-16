import os
import json
import platform
from pathlib import Path
from langchain_ollama import OllamaLLM

class Configuration:
    def __init__(self):
        self.cfg = self.load_config()
        self.llm = OllamaLLM(model=self.cfg["model"], base_url="http://localhost:11434")

    def load_config(self):
        config_path = self.get_config_path()
        if config_path.exists():
            with open(config_path, "r") as f:
                cfg = json.load(f)
            if not cfg.get("model"):
                cfg["model"] = "gemma3"
            return cfg
        return {"model": "gemma3", "system_prompt": ""}

    def get_config_dir(self):
        system = platform.system()
        if system == "Windows":
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata) / "hey"
            return Path.home() / "AppData" / "Roaming" / "hey"
        elif system == "Darwin":
            return Path.home() / "Library" / "Application Support" / "hey"
        else:
            return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "hey"

    def get_config_path(self):
        return self.get_config_dir() / "config.json"
