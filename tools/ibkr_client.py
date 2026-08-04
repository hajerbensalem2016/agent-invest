"""Client IBKR - deux modes :

1. MODE OFFICIEL : connecteur IBKR MCP direct dans Claude (recommande)
   Ne necessite AUCUN code Python ici - Claude parle directement a IBKR
   via le MCP officiel a https://claude.com/connectors/interactive-brokers
   Le connecteur expose les tools suivants a Claude :
   - get_account_positions
   - get_account_balances
   - get_account_summary
   - get_market_data
   - get_open_orders
   - place_order (drafté, approbation manuelle requise)

   Pour activer :
   1. Sur claude.ai ou dans les Settings de Claude Code, ajouter le connecteur
   2. Login IBKR direct
   3. Autoriser l'acces au compte
   ATTENTION bug connu (GitHub issue #571) : parfois 0 tools exposes.
   Verifier dans Claude que les tools IBKR sont bien listes avant utilisation.

2. MODE FALLBACK CSV : utiliser portefeuille.csv (test / demo / avant IBKR live)
   Ce mode est utilise si le MCP IBKR n'est pas branche.
"""
from __future__ import annotations

from pathlib import Path

from tools import risk

ROOT = Path(__file__).parent.parent


def is_ibkr_mcp_connected() -> bool:
    """Verifie si le MCP IBKR est branche a Claude.

    En pratique, l'agent Claude sait lui-meme quels tools sont disponibles.
    Cette fonction sert juste au fallback dans les scripts Python purs.
    """
    # TODO : quand un moyen fiable existera, tester la presence des tools MCP IBKR
    return False


def get_positions_fallback() -> list[dict]:
    """Fallback : lit portefeuille.csv via risk.calculer_portefeuille()."""
    pf = risk.calculer_portefeuille()
    return pf["positions"]


def get_summary_fallback() -> dict:
    """Fallback : resume portefeuille via calculs Python."""
    pf = risk.calculer_portefeuille()
    return {
        "valeur_totale_eur": pf["total_valeur_eur"],
        "cout_total_eur": pf["total_cout_eur"],
        "plus_value_totale_eur": pf["plus_value_totale_eur"],
        "plus_value_totale_pct": pf["plus_value_totale_pct"],
        "nb_positions": len(pf["positions"]),
        "source": "csv_fallback",
    }
