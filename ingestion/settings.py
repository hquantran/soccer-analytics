"""Load local settings from config/config.toml."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.toml"
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "config" / "config.example.toml"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"Missing {CONFIG_PATH}. Copy {CONFIG_EXAMPLE_PATH.name} to "
            f"{CONFIG_PATH.name} under config/ and fill in your API key."
        )
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def get_headers(config: dict) -> dict:
    api = config["api_sports"]
    key = api["key"]
    if not key or key == "YOUR_API_KEY_HERE":
        sys.exit("Set your real API key in config/config.toml under [api_sports].key")
    return {"x-apisports-key": key}


def get_api_settings(config: dict) -> dict:
    defaults = {
        "safe_pause_seconds": 2.0,
        "max_retries": 3,
        "max_pages": None,
        "quota_reserve": 5,
    }
    return {**defaults, **config.get("api", {})}
