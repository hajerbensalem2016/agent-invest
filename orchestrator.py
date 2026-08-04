"""Boucle agentique : Claude Agent SDK + tools Python custom."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server

from tools import halal, market, news_multisource, risk

ROOT = Path(__file__).parent
SYSTEM_PROMPT = (ROOT / "system_prompt.txt").read_text()


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
    return {"content": [{"type": "text", "text": json.dumps(risk.calculer_portefeuille())}]}


@tool("alertes_concentration", "Positions au-dessus du seuil de concentration", {})
async def _alertes_conc(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.alertes_concentration())}]}


@tool("alertes_stop_loss", "Positions sous le seuil stop-loss", {})
async def _alertes_sl(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.alertes_stop_loss())}]}


@tool("ecart_allocation", "Ecart entre allocation reelle et cible strategie", {})
async def _ecart(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.ecart_allocation())}]}


@tool("liste_halal_watchlist", "Watchlist halal pour identifier opportunites", {})
async def _watchlist(args):
    return {"content": [{"type": "text", "text": json.dumps(halal.liste_halal_watchlist())}]}


@tool("get_news_multisource",
      "Agregation news depuis Alpha Vantage + Marketaux + Finnhub avec dedup + score confiance (1-3 sources)",
      {"ticker": str})
async def _news_ticker(args):
    return {"content": [{"type": "text", "text": json.dumps(news_multisource.aggregate_news(args["ticker"]))}]}


@tool("get_news_portefeuille",
      "Agregation news multi-sources pour tous les tickers du portefeuille en parallele",
      {})
async def _news_pf(args):
    pf = risk.calculer_portefeuille()
    tickers = [p["ticker"] for p in pf["positions"]]
    return {"content": [{"type": "text", "text": json.dumps(news_multisource.aggregate_news_portefeuille(tickers))}]}


# ============================================================
# Orchestration
# ============================================================

def _server():
    return create_sdk_mcp_server(
        name="agent-invest-tools",
        version="0.2.0",
        tools=[
            _get_price, _get_fundamentals, _check_halal, _calc_pf,
            _alertes_conc, _alertes_sl, _ecart, _watchlist,
            _news_ticker, _news_pf,
        ],
    )


async def generer_rapport() -> str:
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
        ],
    )

    parts = []
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "Genere le rapport quotidien complet en suivant le workflow et le format defini dans "
            "ton system prompt. Utilise TOUS les outils necessaires. IMPORTANT : appelle "
            "get_news_portefeuille au moins une fois pour avoir la vision news complete."
        )
        async for msg in client.receive_response():
            for block in getattr(msg, "content", []) or []:
                if hasattr(block, "text"):
                    parts.append(block.text)

    return "\n".join(parts)


def sauver_rapport(contenu: str) -> Path:
    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = ROOT / "reports" / f"rapport_{now}.md"
    path.write_text(contenu, encoding="utf-8")
    return path


if __name__ == "__main__":
    rapport = asyncio.run(generer_rapport())
    p = sauver_rapport(rapport)
    print(f"\nRapport sauvegarde : {p}\n")
    print(rapport)
