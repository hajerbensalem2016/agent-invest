"""Loader de secrets : env vars > config/secrets.yaml > None."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

CONFIG = Path(__file__).parent.parent / "config" / "secrets.yaml"


@lru_cache(maxsize=1)
def _load_file() -> dict:
    if not CONFIG.exists():
        return {}
    with CONFIG.open() as f:
        return yaml.safe_load(f) or {}


def get(key: str, env_var: str | None = None) -> str | None:
    """Recupere un secret : priorite env var > fichier > None."""
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    return _load_file().get(key)


def alpha_vantage_key() -> str | None:
    return get("alpha_vantage_api_key", "ALPHA_VANTAGE_API_KEY")


def marketaux_token() -> str | None:
    return get("marketaux_api_token", "MARKETAUX_API_TOKEN")


def finnhub_key() -> str | None:
    return get("finnhub_api_key", "FINNHUB_API_KEY")
