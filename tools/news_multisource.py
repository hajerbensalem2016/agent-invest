"""News multi-sources avec deduplication et score de confiance.

Sources gratuites :
- Alpha Vantage News & Sentiment (25 req/jour, sentiment inclus)
- Marketaux (100 req/jour, 5000+ sources)
- Finnhub Company News (60 req/min)

Strategie :
- Fetch les 3 en parallele
- Dedup par titre normalise (Jaccard similarity > 0.7)
- Score confiance = nombre de sources qui la mentionnent
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import requests

from tools import secrets

TIMEOUT = 10


# ============================================================
# Fetchers individuels par source
# ============================================================

def get_news_alpha_vantage(ticker: str, limit: int = 5) -> list[dict]:
    key = secrets.alpha_vantage_key()
    if not key or key.startswith("TA_"):
        return []
    url = (
        f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
        f"&tickers={ticker}&limit={limit}&apikey={key}"
    )
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return [{"source": "alpha_vantage", "error": str(e)}]

    if "feed" not in data:
        return []
    return [
        {
            "source": "alpha_vantage",
            "titre": item.get("title", ""),
            "resume": item.get("summary", ""),
            "url": item.get("url", ""),
            "date": item.get("time_published", ""),
            "sentiment_score": float(item.get("overall_sentiment_score", 0)),
            "sentiment_label": item.get("overall_sentiment_label", "Neutral"),
            "auteur": item.get("source", ""),
        }
        for item in data["feed"][:limit]
    ]


def get_news_marketaux(ticker: str, limit: int = 5) -> list[dict]:
    token = secrets.marketaux_token()
    if not token or token.startswith("TON_"):
        return []
    url = (
        f"https://api.marketaux.com/v1/news/all?symbols={ticker}"
        f"&limit={limit}&language=en&api_token={token}"
    )
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return [{"source": "marketaux", "error": str(e)}]

    if "data" not in data:
        return []
    result = []
    for item in data["data"][:limit]:
        entities = item.get("entities", [])
        sentiment = 0.0
        if entities:
            sentiment = sum(e.get("sentiment_score", 0) for e in entities) / len(entities)
        result.append({
            "source": "marketaux",
            "titre": item.get("title", ""),
            "resume": item.get("description", "") or item.get("snippet", ""),
            "url": item.get("url", ""),
            "date": item.get("published_at", ""),
            "sentiment_score": sentiment,
            "sentiment_label": _label_from_score(sentiment),
            "auteur": item.get("source", ""),
        })
    return result


def get_news_finnhub(ticker: str, limit: int = 5, jours: int = 7) -> list[dict]:
    key = secrets.finnhub_key()
    if not key or key.startswith("TA_"):
        return []
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d")
    url = (
        f"https://finnhub.io/api/v1/company-news?symbol={ticker}"
        f"&from={from_date}&to={to_date}&token={key}"
    )
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return [{"source": "finnhub", "error": str(e)}]

    if not isinstance(data, list):
        return []
    return [
        {
            "source": "finnhub",
            "titre": item.get("headline", ""),
            "resume": item.get("summary", ""),
            "url": item.get("url", ""),
            "date": datetime.fromtimestamp(item.get("datetime", 0)).isoformat() if item.get("datetime") else "",
            "sentiment_score": None,  # Finnhub free tier ne fournit pas sentiment
            "sentiment_label": None,
            "auteur": item.get("source", ""),
        }
        for item in data[:limit]
    ]


# ============================================================
# Agregateur avec dedup et score confiance
# ============================================================

def _normalize_title(t: str) -> set[str]:
    """Titre -> set de mots normalises pour Jaccard similarity."""
    t = re.sub(r"[^\w\s]", "", t.lower())
    return set(w for w in t.split() if len(w) > 3)


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _label_from_score(s: float | None) -> str:
    if s is None:
        return "Inconnu"
    if s >= 0.15:
        return "Positif"
    if s <= -0.15:
        return "Negatif"
    return "Neutre"


def aggregate_news(ticker: str, limit_par_source: int = 5) -> dict:
    """Fetch 3 sources en parallele, dedup, score confiance.

    Retourne un dict :
    {
        "ticker": str,
        "sources_utilisees": ["alpha_vantage", "marketaux", ...],
        "sources_configurees": int,  # combien de cles API valides
        "nb_articles_brut": int,
        "nb_articles_uniques": int,
        "news": [
            {
                "titre": ..., "resume": ..., "url": ..., "date": ...,
                "sources": ["alpha_vantage", "marketaux"],  # sources qui l'ont mentionne
                "score_confiance": 2,  # 1 = 1 source, 2 = fiable, 3 = tres fiable
                "sentiment_moyen": 0.35,
                "sentiment_label": "Positif",
            }, ...
        ]
    }
    """
    fetchers = [
        ("alpha_vantage", get_news_alpha_vantage),
        ("marketaux", get_news_marketaux),
        ("finnhub", get_news_finnhub),
    ]

    all_news = []
    sources_utilisees = []
    sources_configurees = 0

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {name: executor.submit(fn, ticker, limit_par_source) for name, fn in fetchers}
        for name, future in futures.items():
            try:
                results = future.result(timeout=TIMEOUT + 5)
            except Exception:
                results = []
            if results and not (len(results) == 1 and "error" in results[0]):
                sources_configurees += 1
                if results:
                    sources_utilisees.append(name)
                all_news.extend(results)

    # Deduplication par similarite de titre
    clusters = []  # chaque cluster = liste de news similaires
    for news in all_news:
        titre_norm = _normalize_title(news["titre"])
        placed = False
        for cluster in clusters:
            ref_titre = _normalize_title(cluster[0]["titre"])
            if _jaccard(titre_norm, ref_titre) > 0.5:
                cluster.append(news)
                placed = True
                break
        if not placed:
            clusters.append([news])

    # Construire la sortie finale
    news_uniques = []
    for cluster in clusters:
        sources = list(set(n["source"] for n in cluster))
        scores = [n["sentiment_score"] for n in cluster if n.get("sentiment_score") is not None]
        sentiment_moyen = sum(scores) / len(scores) if scores else None
        # Prendre la version avec le resume le plus long
        meilleur = max(cluster, key=lambda n: len(n.get("resume", "")))
        news_uniques.append({
            "titre": meilleur["titre"],
            "resume": meilleur["resume"],
            "url": meilleur["url"],
            "date": meilleur["date"],
            "auteur": meilleur.get("auteur", ""),
            "sources": sources,
            "score_confiance": len(sources),
            "sentiment_moyen": round(sentiment_moyen, 3) if sentiment_moyen is not None else None,
            "sentiment_label": _label_from_score(sentiment_moyen),
        })

    # Trier par score confiance decroissant puis date decroissante
    news_uniques.sort(key=lambda n: (-n["score_confiance"], n["date"]), reverse=False)
    news_uniques.sort(key=lambda n: n["score_confiance"], reverse=True)

    return {
        "ticker": ticker,
        "sources_utilisees": sources_utilisees,
        "sources_configurees": sources_configurees,
        "nb_articles_brut": len(all_news),
        "nb_articles_uniques": len(news_uniques),
        "news": news_uniques,
    }


def aggregate_news_portefeuille(tickers: list[str]) -> dict:
    """Agrege les news pour plusieurs tickers en parallele."""
    resultats = {}
    with ThreadPoolExecutor(max_workers=min(len(tickers), 6)) as executor:
        futures = {executor.submit(aggregate_news, tk): tk for tk in tickers}
        for future in futures:
            tk = futures[future]
            try:
                resultats[tk] = future.result(timeout=45)
            except Exception as e:
                resultats[tk] = {"ticker": tk, "error": str(e), "news": []}
    return resultats
