"""Point d'entree CLI de l'agent d'investissement.

Usage :
    python cli.py rapport         - Claude genere le rapport complet (markdown) + PDF
    python cli.py pdf             - PDF direct sans Claude (calculs Python seulement)
    python cli.py portefeuille    - affiche le portefeuille en JSON
    python cli.py check TICKER    - test rapide (halal + prix + fondamentaux)
    python cli.py news TICKER     - test news multi-sources agregees
"""
from __future__ import annotations

import asyncio
import json
import sys

from tools import halal, market, news_multisource, risk


def cmd_rapport():
    from orchestrator import generer_rapport, sauver_rapport
    from tools.pdf_report import generer_pdf_depuis_markdown
    rapport = asyncio.run(generer_rapport())
    p = sauver_rapport(rapport)
    print(f"\nRapport markdown sauvegarde : {p}")
    pdf = generer_pdf_depuis_markdown(rapport)
    print(f"Rapport PDF sauvegarde : {pdf}\n")
    print(rapport)


def cmd_pdf():
    from tools.pdf_report import generer_pdf_direct
    out = generer_pdf_direct()
    print(f"PDF genere : {out}")


def cmd_portefeuille():
    pf = risk.calculer_portefeuille()
    print(json.dumps(pf, indent=2, ensure_ascii=False))
    print("\n--- Alertes concentration ---")
    print(json.dumps(risk.alertes_concentration(), indent=2, ensure_ascii=False))
    print("\n--- Alertes stop-loss ---")
    print(json.dumps(risk.alertes_stop_loss(), indent=2, ensure_ascii=False))
    print("\n--- Ecart allocation ---")
    print(json.dumps(risk.ecart_allocation(), indent=2, ensure_ascii=False))


def cmd_check(ticker: str):
    print(f"\n=== {ticker} ===")
    print("\n[Halal]")
    print(json.dumps(halal.check_halal(ticker), indent=2, ensure_ascii=False))
    print("\n[Prix]")
    print(json.dumps(market.get_price(ticker), indent=2, ensure_ascii=False))
    print("\n[Fondamentaux]")
    print(json.dumps(market.get_fundamentals(ticker), indent=2, ensure_ascii=False))


def cmd_news(ticker: str):
    print(f"\n=== News multi-sources : {ticker} ===")
    result = news_multisource.aggregate_news(ticker)
    print(f"Sources configurees : {result['sources_configurees']}/3")
    print(f"Sources utilisees : {result['sources_utilisees']}")
    print(f"Articles bruts : {result['nb_articles_brut']}, uniques : {result['nb_articles_uniques']}\n")
    for i, news in enumerate(result["news"][:10], 1):
        confiance = "HAUTE" if news["score_confiance"] >= 2 else "A verifier"
        print(f"{i}. [{confiance} - {news['score_confiance']} src] {news['titre']}")
        print(f"   Sentiment: {news['sentiment_label']} | Sources: {', '.join(news['sources'])}")
        if news.get("url"):
            print(f"   {news['url']}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "rapport":
        cmd_rapport()
    elif cmd == "pdf":
        cmd_pdf()
    elif cmd == "portefeuille":
        cmd_portefeuille()
    elif cmd == "check" and len(sys.argv) >= 3:
        cmd_check(sys.argv[2].upper())
    elif cmd == "news" and len(sys.argv) >= 3:
        cmd_news(sys.argv[2].upper())
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
