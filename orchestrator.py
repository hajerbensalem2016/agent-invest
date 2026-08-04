"""Boucle agentique : Claude Agent SDK + tools Python custom + memoire SQLite."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server

from tools import halal, market, memory, news_multisource, paths, risk

ROOT = Path(__file__).parent
SYSTEM_PROMPT = (ROOT / "system_prompt.txt").read_text()


# ============================================================
# Contexte user (thread-local via closure)
# ============================================================

_CURRENT_USER = {"user": paths.DEFAULT_USER}


def _set_user(user: str):
    _CURRENT_USER["user"] = user


def _user() -> str:
    return _CURRENT_USER["user"]


# ============================================================
# Tools exposes a Claude
# ============================================================

@tool("get_price", "Prix live d'un ticker + variation du jour", {"ticker": str})
async def _get_price(args):
    return {"content": [{"type": "text", "text": json.dumps(market.get_price(args["ticker"]))}]}


@tool("get_fundamentals", "Fondamentaux (PER, dette/actif, beta, secteur) d'un ticker", {"ticker": str})
async def _get_fundamentals(args):
    return {"content": [{"type": "text", "text": json.dumps(market.get_fundamentals(args["ticker"]))}]}


@tool("check_halal", "Conformite halal d'un ticker (whitelist + ratios AAOIFI)", {"ticker": str})
async def _check_halal(args):
    return {"content": [{"type": "text", "text": json.dumps(halal.check_halal(args["ticker"]))}]}


@tool("calculer_portefeuille", "Positions actuelles avec P&L, poids, valeur", {})
async def _calc_pf(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.calculer_portefeuille(_user()))}]}


@tool("alertes_concentration", "Positions au-dessus du seuil de concentration", {})
async def _alertes_conc(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.alertes_concentration(_user()))}]}


@tool("alertes_stop_loss", "Positions sous le seuil stop-loss", {})
async def _alertes_sl(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.alertes_stop_loss(_user()))}]}


@tool("ecart_allocation", "Ecart entre allocation reelle et cible strategie", {})
async def _ecart(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.ecart_allocation(_user()))}]}


@tool("liste_halal_watchlist", "Watchlist halal pour identifier opportunites", {})
async def _watchlist(args):
    return {"content": [{"type": "text", "text": json.dumps(halal.liste_halal_watchlist())}]}


@tool("get_news_multisource",
      "News agregees Alpha Vantage + Marketaux + Finnhub avec dedup + score confiance (1-3 sources)",
      {"ticker": str})
async def _news_ticker(args):
    return {"content": [{"type": "text", "text": json.dumps(news_multisource.aggregate_news(args["ticker"]))}]}


@tool("get_news_portefeuille",
      "News multi-sources pour tous les tickers du portefeuille en parallele",
      {})
async def _news_pf(args):
    pf = risk.calculer_portefeuille(_user())
    tickers = [p["ticker"] for p in pf["positions"]]
    return {"content": [{"type": "text", "text": json.dumps(news_multisource.aggregate_news_portefeuille(tickers))}]}


@tool("get_historique_rapports",
      "Retourne les N derniers rapports du user (metadata : date, valeur, PV, nb positions)",
      {"limit": int})
async def _hist_reports(args):
    limit = args.get("limit", 10)
    return {"content": [{"type": "text", "text": json.dumps(memory.get_historique_rapports(_user(), limit))}]}


@tool("get_recos_precedentes",
      "Retourne les dernieres recommandations du user, optionnellement filtrees par ticker (utile pour ne pas repeter les memes conseils ou apprendre des recos passees)",
      {"ticker": str, "limit": int})
async def _recos_prev(args):
    ticker = args.get("ticker") or None
    limit = args.get("limit", 20)
    return {"content": [{"type": "text", "text": json.dumps(memory.get_recos_precedentes(_user(), ticker, limit))}]}


@tool("get_calibration_confiance",
      "Statistiques de calibration : pour chaque tranche de confiance des recos passees, quel taux de succes reel (necessite des recos executees et evaluees)",
      {})
async def _calibration(args):
    return {"content": [{"type": "text", "text": json.dumps(memory.get_calibration_confiance(_user()))}]}


# ============================================================
# Orchestration
# ============================================================

def _server():
    return create_sdk_mcp_server(
        name="agent-invest-tools",
        version="0.3.0",
        tools=[
            _get_price, _get_fundamentals, _check_halal, _calc_pf,
            _alertes_conc, _alertes_sl, _ecart, _watchlist,
            _news_ticker, _news_pf,
            _hist_reports, _recos_prev, _calibration,
        ],
    )


async def generer_rapport(user: str = paths.DEFAULT_USER) -> str:
    _set_user(user)
    server = _server()
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"tools": server},
        allowed_tools=[
            "mcp__tools__get_price",
            "mcp__tools__get_fundamentals",
            "mcp__tools__check_halal",
            "mcp__tools__calculer_portefeuille",
            "mcp__tools__alertes_concentration",
            "mcp__tools__alertes_stop_loss",
            "mcp__tools__ecart_allocation",
            "mcp__tools__liste_halal_watchlist",
            "mcp__tools__get_news_multisource",
            "mcp__tools__get_news_portefeuille",
            "mcp__tools__get_historique_rapports",
            "mcp__tools__get_recos_precedentes",
            "mcp__tools__get_calibration_confiance",
        ],
    )

    parts = []
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Genere le rapport quotidien complet pour l'utilisateur '{user}' en suivant le workflow "
            f"et le format defini dans ton system prompt. Utilise TOUS les outils necessaires. "
            f"IMPORTANT : "
            f"1) appelle get_news_portefeuille au moins une fois pour la vision news complete. "
            f"2) appelle get_recos_precedentes pour eviter de repeter des conseils recents et "
            f"analyser tes recos passees. "
            f"3) si get_calibration_confiance renvoie des donnees, en tenir compte pour ajuster tes niveaux de confiance."
        )
        async for msg in client.receive_response():
            for block in getattr(msg, "content", []) or []:
                if hasattr(block, "text"):
                    parts.append(block.text)

    return "\n".join(parts)


def sauver_rapport(user: str, contenu: str) -> Path:
    """Sauvegarde le rapport en markdown + logge dans SQLite + extrait les recos."""
    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = paths.reports_dir(user) / f"rapport_{now}.md"
    path.write_text(contenu, encoding="utf-8")

    # Logger dans SQLite
    try:
        pf = risk.calculer_portefeuille(user)
        report_id = memory.log_report(
            user=user,
            valeur_totale=pf["total_valeur_eur"],
            pv_totale=pf["plus_value_totale_eur"],
            pv_pct=pf["plus_value_totale_pct"],
            nb_positions=len(pf["positions"]),
            contenu_md=contenu,
        )
        nb_recos = memory.extraire_et_logger_recos_depuis_rapport(user, report_id, contenu)
        print(f"Memoire : rapport #{report_id} logge, {nb_recos} recos extraites")
    except Exception as e:
        print(f"Warning : echec logging memoire ({e})")

    return path


if __name__ == "__main__":
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else paths.DEFAULT_USER
    rapport = asyncio.run(generer_rapport(user))
    p = sauver_rapport(user, rapport)
    print(f"\nRapport sauvegarde : {p}\n")
    print(rapport)
