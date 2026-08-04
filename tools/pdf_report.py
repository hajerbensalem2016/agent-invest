"""Genere un rapport PDF a partir des donnees du portefeuille (sans Claude)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from weasyprint import HTML

from tools import halal, risk

ROOT = Path(__file__).parent.parent


CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: 'Helvetica', 'Arial', sans-serif; color: #222; font-size: 11pt; line-height: 1.5; }
h1 { color: #1a1a1a; border-bottom: 3px solid #2563eb; padding-bottom: 8px; }
h2 { color: #2563eb; margin-top: 24px; border-left: 4px solid #2563eb; padding-left: 10px; }
h3 { color: #444; margin-top: 18px; }
.header { text-align: center; margin-bottom: 20px; color: #666; font-size: 10pt; }
.summary { background: #f0f9ff; border: 1px solid #bae6fd; padding: 15px; border-radius: 8px; margin: 15px 0; }
.summary .big { font-size: 24pt; font-weight: bold; color: #0369a1; }
.summary .green { color: #16a34a; }
.summary .red { color: #dc2626; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 10pt; }
th { background: #2563eb; color: white; padding: 8px; text-align: left; }
td { padding: 8px; border-bottom: 1px solid #e5e7eb; }
tr:nth-child(even) { background: #f9fafb; }
.gain { color: #16a34a; font-weight: bold; }
.loss { color: #dc2626; font-weight: bold; }
.badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 9pt; font-weight: bold; }
.badge-halal { background: #dcfce7; color: #166534; }
.badge-non-halal { background: #fee2e2; color: #991b1b; }
.badge-inconnu { background: #fef3c7; color: #92400e; }
.alerte { background: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; margin: 10px 0; }
.alerte-orange { background: #fff7ed; border-left: 4px solid #ea580c; padding: 12px; margin: 10px 0; }
.info { background: #eff6ff; border-left: 4px solid #2563eb; padding: 12px; margin: 10px 0; }
.footer { margin-top: 40px; text-align: center; font-size: 9pt; color: #999; border-top: 1px solid #e5e7eb; padding-top: 10px; }
"""


def _classe_pv(pv_pct: float) -> str:
    return "gain" if pv_pct >= 0 else "loss"


def _badge_halal(statut: dict) -> str:
    if statut["halal"] is True:
        return '<span class="badge badge-halal">HALAL</span>'
    if statut["halal"] is False:
        return '<span class="badge badge-non-halal">NON HALAL</span>'
    return '<span class="badge badge-inconnu">A VERIFIER</span>'


def generer_html() -> str:
    pf = risk.calculer_portefeuille()
    alertes_conc = risk.alertes_concentration()
    alertes_sl = risk.alertes_stop_loss()
    alloc = risk.ecart_allocation()

    now = datetime.now().strftime("%d/%m/%Y a %Hh%M")

    lignes_html = ""
    for p in pf["positions"]:
        statut = halal.check_halal(p["ticker"])
        badge = _badge_halal(statut)
        cls = _classe_pv(p["plus_value_pct"])
        signe = "+" if p["plus_value_eur"] >= 0 else ""
        lignes_html += f"""
        <tr>
            <td><b>{p['ticker']}</b> {badge}</td>
            <td>{p['quantite']:.0f}</td>
            <td>{p['poids_pct']:.1f}%</td>
            <td>{p['valeur_actuelle_eur']:,.0f} EUR</td>
            <td>{p['prix_achat_eur']:.2f} -> {p['prix_actuel_eur']:.2f}</td>
            <td class="{cls}">{signe}{p['plus_value_eur']:,.0f} EUR ({signe}{p['plus_value_pct']:.1f}%)</td>
        </tr>
        """

    total_cls = _classe_pv(pf["plus_value_totale_pct"])
    total_signe = "+" if pf["plus_value_totale_eur"] >= 0 else ""

    conc_html = ""
    if alertes_conc:
        for a in alertes_conc:
            conc_html += f'<div class="alerte-orange"><b>{a["ticker"]}</b> pese {a["poids_pct"]}% (seuil {a["seuil_pct"]}%) - a rebalancer</div>'
    else:
        conc_html = '<div class="info">Aucune position ne depasse le seuil de concentration.</div>'

    sl_html = ""
    if alertes_sl:
        for a in alertes_sl:
            sl_html += f'<div class="alerte"><b>{a["ticker"]}</b> a {a["plus_value_pct"]}% (seuil {a["seuil_pct"]}%) - decision requise</div>'
    else:
        sl_html = '<div class="info">Aucune position n\'a atteint le seuil de stop-loss.</div>'

    non_halal = [p for p in pf["positions"] if halal.check_halal(p["ticker"])["halal"] is False]
    non_halal_html = ""
    if non_halal:
        for p in non_halal:
            statut = halal.check_halal(p["ticker"])
            non_halal_html += (
                f'<div class="alerte"><b>{p["ticker"]}</b> ({statut["raison"]}) - '
                f'{p["poids_pct"]:.1f}% du portefeuille = {p["valeur_actuelle_eur"]:,.0f} EUR a sortir</div>'
            )
    else:
        non_halal_html = '<div class="info">Aucune position non-halal detectee.</div>'

    ecart_html = ""
    if isinstance(alloc.get("ecart_pct"), dict):
        ecart_html = "<table><tr><th>Categorie</th><th>Cible</th><th>Reel</th><th>Ecart</th></tr>"
        for k in ("actions", "etf", "cash"):
            e = alloc["ecart_pct"][k]
            cls = "gain" if abs(e) < 5 else "loss"
            signe = "+" if e >= 0 else ""
            ecart_html += (
                f'<tr><td>{k.capitalize()}</td><td>{alloc["cible"][k]}%</td>'
                f'<td>{alloc["reel"][k]}%</td><td class="{cls}">{signe}{e}%</td></tr>'
            )
        ecart_html += "</table>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>

<h1>Rapport quotidien - Agent Invest</h1>
<div class="header">Genere le {now} - Portefeuille Interactive Brokers</div>

<div class="summary">
    <div>Valeur totale du portefeuille</div>
    <div class="big">{pf['total_valeur_eur']:,.0f} EUR</div>
    <div>Cout total investi : {pf['total_cout_eur']:,.0f} EUR</div>
    <div class="{total_cls}"><b>Performance : {total_signe}{pf['plus_value_totale_eur']:,.0f} EUR ({total_signe}{pf['plus_value_totale_pct']:.1f}%)</b></div>
</div>

<h2>Positions</h2>
<table>
<tr><th>Titre</th><th>Qte</th><th>Poids</th><th>Valeur</th><th>Prix achat -> actuel</th><th>Performance</th></tr>
{lignes_html}
</table>

<h2>Conformite Halal</h2>
{non_halal_html}

<h2>Alertes de concentration</h2>
{conc_html}

<h2>Alertes stop-loss</h2>
{sl_html}

<h2>Ecart avec ta strategie</h2>
{ecart_html}

<div class="footer">
    Agent Invest MVP - Donnees Yahoo Finance temps reel - Ce rapport ne constitue pas un conseil en investissement.
</div>

</body></html>"""


def generer_pdf() -> Path:
    html_str = generer_html()
    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    out = ROOT / "reports" / f"rapport_{now}.pdf"
    HTML(string=html_str).write_pdf(str(out))
    return out
