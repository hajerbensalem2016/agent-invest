"""Recupere prix et fondamentaux via yfinance."""
from __future__ import annotations

import yfinance as yf


def get_price(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    hist = t.history(period="5d")
    if hist.empty:
        return {"ticker": ticker, "error": "no data"}
    last = hist.iloc[-1]
    prev = hist.iloc[-2] if len(hist) >= 2 else last
    return {
        "ticker": ticker,
        "prix_actuel": round(float(last["Close"]), 2),
        "variation_jour_pct": round((float(last["Close"]) - float(prev["Close"])) / float(prev["Close"]) * 100, 2),
        "volume": int(last["Volume"]),
        "devise": t.fast_info.get("currency", "USD"),
    }


def get_fundamentals(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info or {}
    return {
        "ticker": ticker,
        "nom": info.get("longName") or info.get("shortName"),
        "secteur": info.get("sector"),
        "industrie": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "per": info.get("trailingPE"),
        "per_forward": info.get("forwardPE"),
        "dette_totale": info.get("totalDebt"),
        "actif_total": info.get("totalAssets"),
        "ratio_dette_actif_pct": round(info.get("totalDebt", 0) / info.get("totalAssets", 1) * 100, 2)
        if info.get("totalDebt") and info.get("totalAssets") else None,
        "beta": info.get("beta"),
        "dividende_yield_pct": round((info.get("dividendYield") or 0) * 100, 2),
    }


def get_price_bulk(tickers: list[str]) -> dict:
    return {tk: get_price(tk) for tk in tickers}
