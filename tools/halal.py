"""Screening halal : whitelist + verification ratios AAOIFI."""
from __future__ import annotations

from pathlib import Path

import yaml

CONFIG = Path(__file__).parent.parent / "config" / "halal_whitelist.yaml"


def _load() -> dict:
    with CONFIG.open() as f:
        return yaml.safe_load(f)


def check_halal(ticker: str) -> dict:
    data = _load()
    ticker_upper = ticker.upper()

    for entry in data.get("tickers_non_halal", []):
        if entry["ticker"] == ticker_upper:
            return {
                "ticker": ticker_upper,
                "halal": False,
                "confiance": "haute",
                "raison": entry["raison"],
                "source": "liste_exclusion",
            }

    for entry in data.get("tickers_halal", []):
        if entry["ticker"] == ticker_upper:
            return {
                "ticker": ticker_upper,
                "halal": True,
                "confiance": "haute",
                "raison": entry.get("note", "sur whitelist"),
                "secteur": entry.get("secteur"),
                "source": "whitelist",
            }

    return {
        "ticker": ticker_upper,
        "halal": None,
        "confiance": "inconnue",
        "raison": "ticker absent de la whitelist et de la liste d'exclusion, verification manuelle requise (Zoya)",
        "source": "inconnu",
    }


def check_ratios_aaoifi(fondamentaux: dict) -> dict:
    """Verifie les seuils financiers AAOIFI a partir des fondamentaux yfinance."""
    ratio = fondamentaux.get("ratio_dette_actif_pct")
    if ratio is None:
        return {
            "conforme_aaoifi": None,
            "message": "ratio dette/actif indisponible - impossible de valider",
        }
    conforme = ratio < 33
    return {
        "conforme_aaoifi": conforme,
        "ratio_dette_actif_pct": ratio,
        "seuil": 33,
        "message": f"ratio dette/actif = {ratio}% ({'OK' if conforme else 'DEPASSE le seuil de 33%'})",
    }


def liste_halal_watchlist() -> list[dict]:
    """Retourne la watchlist halal complete."""
    return _load().get("tickers_halal", [])
