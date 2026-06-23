"""Load local settings from config.toml."""

import sys
import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("config.toml")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"Missing {CONFIG_PATH.name}. Copy config.example.toml to config.toml "
            "and fill in your API key."
        )
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def get_headers(config: dict) -> dict:
    api = config["api_sports"]
    key = api["key"]
    if not key or key == "YOUR_API_KEY_HERE":
        sys.exit("Set your real API key in config.toml under [api_sports].key")
    return {"x-apisports-key": key}


def get_api_settings(config: dict) -> dict:
    """Pacing and pagination defaults (overridable in config.toml [api])."""
    defaults = {
        "safe_pause_seconds": 6.0,
        "max_retries": 3,
        "max_pages": 3,
    }
    return {**defaults, **config.get("api", {})}
