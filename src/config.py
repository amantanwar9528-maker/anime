"""Loads config.yaml (falls back to config.example.yaml) and resolves secrets
from env vars first, then secrets/ files. Same convention as the trending bot."""
import os
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Config:
    def __init__(self, path: str | None = None):
        cfg_path = Path(path) if path else ROOT / "config.yaml"
        if not cfg_path.exists():
            cfg_path = ROOT / "config.example.yaml"
        with open(cfg_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)
        self.root = ROOT

    def get(self, dotted, default=None):
        node = self.data
        for part in dotted.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def secret(self, env_name: str, file_fallback: str | None = None) -> str | None:
        val = os.environ.get(env_name)
        if val:
            return val.strip()
        if file_fallback:
            p = ROOT / "secrets" / file_fallback
            if p.exists():
                return p.read_text(encoding="utf-8").strip()
        p = ROOT / "secrets" / f"{env_name}.txt"
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
        return None

    def path(self, *parts) -> Path:
        p = ROOT.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
