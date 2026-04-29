from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import tomllib


class AppConfig:
    """Lightweight TOML config accessor with safe fallbacks."""

    def __init__(self, config_path: str | Path | None = None):
        self.project_root = Path(__file__).resolve().parents[1]
        self.path = (
            Path(config_path).resolve()
            if config_path is not None
            else self.project_root / "config" / "config.toml"
        )
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return
        try:
            with self.path.open("rb") as fh:
                parsed = tomllib.load(fh)
            self._data = parsed if isinstance(parsed, dict) else {}
        except (OSError, UnicodeError, tomllib.TOMLDecodeError):
            self._data = {}

    def get(self, path: str, default: Any = None) -> Any:
        if not path:
            return default
        try:
            current: Any = self._data
            for part in path.split("."):
                part = part.strip()
                if not part:
                    return default
                if not isinstance(current, dict) or part not in current:
                    return default
                current = current[part]
            return current
        except Exception:
            return default

    def get_str(self, path: str, default: str = "") -> str:
        value = self.get(path, default=default)
        if value is None:
            return default
        return str(value).strip()

    def get_int(self, path: str, default: int = 0) -> int:
        value = self.get(path, default=default)
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        try:
            return int(str(value).strip())
        except Exception:
            return default

    def get_float(self, path: str, default: float = 0.0) -> float:
        value = self.get(path, default=default)
        if isinstance(value, bool):
            return float(int(value))
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).strip())
        except Exception:
            return default

    def get_bool(self, path: str, default: bool = False) -> bool:
        value = self.get(path, default=default)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
        try:
            return bool(value)
        except Exception:
            return default


@lru_cache(maxsize=1)
def _get_default_config() -> AppConfig:
    return AppConfig()


def get_config(config_path: str | Path | None = None) -> AppConfig:
    if config_path is None:
        return _get_default_config()
    return AppConfig(config_path=config_path)
