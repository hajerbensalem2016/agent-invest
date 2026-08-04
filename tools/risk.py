"""Calculs portefeuille : P&L, allocation, concentration, ecarts strategie."""
from __future__ import annotations

import csv
from pathlib import Path

import yaml

from tools import market

ROOT = Path(__file__).parent.parent


def load_portefeuille() -> list[dict]:
    with (ROOT / "portefeuille.csv").open() as f:
        return list(csv.DictReader(f))


def load_strategie() -> dict:
    with (ROOT / "config" / "strategie.yaml").open() as f:
        return yaml.safe_load(f)


def calculer_portefeuille() -> dict:
    positions = load_portefeuille()
    lignes = []
    total_valeur = 0.0
    total_cout = 0.0

    for p in positions:
        ticker = p["ticker"]
        qty = float(p["quantite"])
        prix_achat = float(p["prix_achat_eur"])
        cout = qty * prix_achat

        prix_info = market.get_price(ticker)
        prix_actuel = prix_info.get("prix_actuel", prix_achat)
        valeur = qty * prix_actuel
        plus_value = valeur - cout
        pv_pct = (plus_value / cout * 100) if cout else 0.0

        lignes.append({
            "ticker": ticker,
            "quantite": qty,
            "prix_achat_eur": prix_achat,
            "prix_actuel_eur": prix_actuel,
            "cout_total_eur": round(cout, 2),
            "valeur_actuelle_eur": round(valeur, 2),
            "plus_value_eur": round(plus_value, 2),
            "plus_value_pct": round(pv_pct, 2),
            "date_achat": p.get("date_achat"),
        })
        total_valeur += valeur
        total_cout += cout

    for l in lignes:
        l["poids_pct"] = round(l["valeur_actuelle_eur"] / total_valeur * 100, 2) if total_valeur else 0

    return {
        "positions": lignes,
        "total_valeur_eur": round(total_valeur, 2),
        "total_cout_eur": round(total_cout, 2),
        "plus_value_totale_eur": round(total_valeur - total_cout, 2),
        "plus_value_totale_pct": round((total_valeur - total_cout) / total_cout * 100, 2) if total_cout else 0,
    }


def alertes_concentration() -> list[dict]:
    strat = load_strategie()
    seuil = strat["seuils_risque"]["concentration_max_pct_par_position"]
    pf = calculer_portefeuille()
    return [
        {
            "type": "concentration",
            "ticker": p["ticker"],
            "poids_pct": p["poids_pct"],
            "seuil_pct": seuil,
            "message": f"{p['ticker']} pese {p['poids_pct']}% (seuil {seuil}%)",
        }
        for p in pf["positions"]
        if p["poids_pct"] > seuil
    ]


def alertes_stop_loss() -> list[dict]:
    strat = load_strategie()
    seuil = strat["seuils_risque"]["stop_loss_alerte_pct"]
    pf = calculer_portefeuille()
    return [
        {
            "type": "stop_loss",
            "ticker": p["ticker"],
            "plus_value_pct": p["plus_value_pct"],
            "seuil_pct": seuil,
            "message": f"{p['ticker']} a {p['plus_value_pct']}% (sous le seuil {seuil}%)",
        }
        for p in pf["positions"]
        if p["plus_value_pct"] <= seuil
    ]


def ecart_allocation() -> dict:
    """Compare l'allocation reelle a la cible strategie (rudimentaire, MVP)."""
    strat = load_strategie()["allocation_cible"]
    pf = calculer_portefeuille()
    total = pf["total_valeur_eur"]
    if not total:
        return {"message": "portefeuille vide"}

    # Repartition ETF vs actions (heuristique simple : ticker en 3-5 char = action, sinon ETF)
    etf_val = sum(p["valeur_actuelle_eur"] for p in pf["positions"] if p["ticker"] in {"HLAL", "SPUS", "SPRE", "SPTE"})
    actions_val = total - etf_val

    reel = {
        "actions": round(actions_val / total * 100, 2),
        "etf": round(etf_val / total * 100, 2),
        "cash": 0,  # non tracke dans le MVP
    }
    ecarts = {k: round(reel[k] - strat[k], 2) for k in ("actions", "etf", "cash")}
    return {"cible": strat, "reel": reel, "ecart_pct": ecarts}
