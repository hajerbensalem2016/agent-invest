"""Boucle agentique : Claude Agent SDK + tools Python custom."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server

from tools import market, halal, risk

ROOT = Path(__file__).parent
SYSTEM_PROMPT = (ROOT / "system_prompt.txt").read_text()


# --- Definition des tools exposes a Claude ---

@tool("get_price", "Recupere le prix live d'un ticker et sa variation du jour", {"ticker": str})
async def _get_price(args):
    return {"content": [{"type": "text", "text": json.dumps(market.get_price(args["ticker"]))}]}


@tool("get_fundamentals", "Recupere fondamentaux (PER, dette/actif, beta, secteur) d'un ticker", {"ticker": str})
async def _get_fundamentals(args):
    return {"content": [{"type": "text", "text": json.dumps(market.get_fundamentals(args["ticker"]))}]}


@tool("check_halal", "Verifie la conformite halal d'un ticker (whitelist + ratios AAOIFI)", {"ticker": str})
async def _check_halal(args):
    return {"content": [{"type": "text", "text": json.dumps(halal.check_halal(args["ticker"]))}]}


@tool("calculer_portefeuille", "Retourne toutes les positions avec P&L et poids", {})
async def _calc_pf(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.calculer_portefeuille())}]}


@tool("alertes_concentration", "Positions au-dessus du seuil de concentration", {})
async def _alertes_conc(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.alertes_concentration())}]}


@tool("alertes_stop_loss", "Positions sous le seuil stop-loss defini dans la strategie", {})
async def _alertes_sl(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.alertes_stop_loss())}]}


@tool("ecart_allocation", "Ecart entre l'allocation reelle et la cible strategie", {})
async def _ecart(args):
    return {"content": [{"type": "text", "text": json.dumps(risk.ecart_allocation())}]}


@tool("liste_halal_watchlist", "Retourne la watchlist des tickers halal a monitorer", {})
async def _watchlist(args):
    return {"content": [{"type": "text", "text": json.dumps(halal.liste_halal_watchlist())}]}


# --- Orchestration ---

def _server():
    return create_sdk_mcp_server(
        name="agent-invest-tools",
        version="0.1.0",
        tools=[_get_price, _get_fundamentals, _check_halal, _calc_pf,
               _alertes_conc, _alertes_sl, _ecart, _watchlist],
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
        ],
    )

    rapport_parts = []
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "Genere le rapport quotidien de conseil pour mon portefeuille en suivant le workflow "
            "et le format defini dans ton system prompt. Utilise TOUS les outils necessaires."
        )
        async for msg in client.receive_response():
            for block in getattr(msg, "content", []) or []:
                if hasattr(block, "text"):
                    rapport_parts.append(block.text)

    return "\n".join(rapport_parts)


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
