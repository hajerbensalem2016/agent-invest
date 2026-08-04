"""Point d'entree CLI de l'agent d'investissement.

Usage :
    python cli.py rapport         - genere le rapport quotidien (Claude, texte)
    python cli.py pdf             - genere le rapport en PDF (sans Claude, calculs Python)
    python cli.py portefeuille    - affiche le portefeuille (sans Claude)
    python cli.py check TICKER    - test rapide d'un ticker (halal + prix)
"""
from __future__ import annotations

import asyncio
import json
import sys

from tools import halal, market, risk


def cmd_rapport():
    from orchestrator import generer_rapport, sauver_rapport
    rapport = asyncio.run(generer_rapport())
    p = sauver_rapport(rapport)
    print(f"\nRapport sauvegarde : {p}\n")
    print(rapport)


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


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "rapport":
        cmd_rapport()
    elif cmd == "pdf":
        from tools.pdf_report import generer_pdf
        out = generer_pdf()
        print(f"PDF genere : {out}")
    elif cmd == "portefeuille":
        cmd_portefeuille()
    elif cmd == "check" and len(sys.argv) >= 3:
        cmd_check(sys.argv[2].upper())
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
