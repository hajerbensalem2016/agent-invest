"""Point d'entree CLI de l'agent d'investissement.

Usage :
    python cli.py [--user USER] COMMAND [args]

Commandes :
    rapport                       - Claude genere rapport complet (markdown + PDF + memoire)
    pdf                           - PDF direct sans Claude
    portefeuille                  - affiche portefeuille en JSON
    check TICKER                  - test halal + prix + fondamentaux d'un ticker
    news TICKER                   - news multi-sources agregees d'un ticker
    historique [--limit N]        - liste les rapports precedents du user
    calibration                   - stats de calibration confiance vs succes reel
    recos [--ticker TICK]         - liste les recommandations passees du user
    marquer-reco ID STATUT        - marque reco (executed | rejected | expired)
    users                         - liste les users disponibles

Exemples :
    python cli.py rapport                       # defaut : user hajer
    python cli.py --user demo rapport           # user demo
    python cli.py --user hajer check AAPL
    python cli.py marquer-reco 42 executed
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from tools import halal, market, memory, news_multisource, paths, risk


def cmd_rapport(user: str):
    from orchestrator import generer_rapport, sauver_rapport
    from tools.pdf_report import generer_pdf_depuis_markdown
    rapport = asyncio.run(generer_rapport(user))
    p = sauver_rapport(user, rapport)
    print(f"\nRapport markdown sauvegarde : {p}")
    pdf = generer_pdf_depuis_markdown(rapport, user=user)
    print(f"Rapport PDF sauvegarde : {pdf}\n")
    print(rapport)


def cmd_pdf(user: str):
    from tools.pdf_report import generer_pdf_direct
    out = generer_pdf_direct(user)
    print(f"PDF genere : {out}")


def cmd_portefeuille(user: str):
    print(f"=== User : {user} ===")
    pf = risk.calculer_portefeuille(user)
    print(json.dumps(pf, indent=2, ensure_ascii=False))
    print("\n--- Alertes concentration ---")
    print(json.dumps(risk.alertes_concentration(user), indent=2, ensure_ascii=False))
    print("\n--- Alertes stop-loss ---")
    print(json.dumps(risk.alertes_stop_loss(user), indent=2, ensure_ascii=False))
    print("\n--- Ecart allocation ---")
    print(json.dumps(risk.ecart_allocation(user), indent=2, ensure_ascii=False))


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


def cmd_historique(user: str, limit: int = 20):
    print(f"=== Historique rapports : {user} (dernier {limit}) ===\n")
    reports = memory.get_historique_rapports(user, limit)
    if not reports:
        print("Aucun rapport en memoire.")
        return
    print(f"{'ID':<5}{'Date':<22}{'Valeur EUR':>14}{'PV EUR':>14}{'PV %':>10}{'Pos':>6}")
    print("-" * 71)
    for r in reports:
        print(f"{r['id']:<5}{r['date']:<22}"
              f"{r['valeur_totale_eur']:>14.0f}"
              f"{r['plus_value_totale_eur']:>14.0f}"
              f"{r['plus_value_totale_pct']:>9.1f}%"
              f"{r['nb_positions']:>6}")


def cmd_calibration(user: str):
    print(f"=== Calibration confiance : {user} ===\n")
    calib = memory.get_calibration_confiance(user)
    if not calib["tranches"]:
        print("Aucune reco evaluee - la calibration se construira au fil du temps.")
        print("Utilise 'python cli.py marquer-reco ID executed' apres avoir execute une reco,")
        print("puis evalue le resultat 30-90j plus tard.")
        return
    print(f"Total recos evaluees : {calib['total_recos_evaluees']}\n")
    print(f"{'Tranche':<12}{'Total':>8}{'Succes':>9}{'Taux':>10}")
    print("-" * 39)
    for t in calib["tranches"]:
        print(f"{t['tranche_confiance']:<12}{t['total_recos']:>8}{t['succes']:>9}{t['taux_succes_pct']:>9}%")


def cmd_recos(user: str, ticker: str | None = None):
    print(f"=== Recommandations : {user} ===")
    if ticker:
        print(f"(filtre ticker : {ticker})")
    print()
    recos = memory.get_recos_precedentes(user, ticker, limit=30)
    if not recos:
        print("Aucune reco en memoire.")
        return
    print(f"{'ID':<5}{'Date':<22}{'Action':<12}{'Ticker':<8}{'Conf':>6}{'Statut':<12}")
    print("-" * 65)
    for r in recos:
        print(f"{r['id']:<5}{r['date']:<22}"
              f"{r['action']:<12}"
              f"{(r['ticker'] or '-'):<8}"
              f"{(r['confiance'] or 0):>6}"
              f"{(r['statut'] or 'pending'):<12}")


def cmd_marquer_reco(reco_id: int, statut: str):
    ok = memory.marquer_reco(reco_id, statut)
    if ok:
        print(f"Reco #{reco_id} marquee '{statut}'.")
    else:
        print(f"Reco #{reco_id} introuvable.")


def cmd_users():
    users = paths.list_users()
    print("Users disponibles :")
    for u in users:
        marker = " (defaut)" if u == paths.DEFAULT_USER else ""
        print(f"  - {u}{marker}")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--user", default=paths.DEFAULT_USER)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--ticker", default=None)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args()

    if not parsed.args:
        print(__doc__)
        sys.exit(1)

    cmd = parsed.args[0]
    rest = parsed.args[1:]
    user = parsed.user

    if cmd == "rapport":
        cmd_rapport(user)
    elif cmd == "pdf":
        cmd_pdf(user)
    elif cmd == "portefeuille":
        cmd_portefeuille(user)
    elif cmd == "check" and rest:
        cmd_check(rest[0].upper())
    elif cmd == "news" and rest:
        cmd_news(rest[0].upper())
    elif cmd == "historique":
        cmd_historique(user, parsed.limit)
    elif cmd == "calibration":
        cmd_calibration(user)
    elif cmd == "recos":
        cmd_recos(user, parsed.ticker.upper() if parsed.ticker else None)
    elif cmd == "marquer-reco" and len(rest) >= 2:
        cmd_marquer_reco(int(rest[0]), rest[1])
    elif cmd == "users":
        cmd_users()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
