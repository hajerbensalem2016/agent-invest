"""Genere un rapport PDF a partir des donnees + optionnellement du rapport Claude en markdown.

Deux modes :
- Mode DIRECT : appelle risk/halal directement et fait un PDF sans Claude (rapide, sans SDK)
- Mode CLAUDE : prend le markdown produit par orchestrator.py et le convertit en PDF
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from tools import halal, paths, risk

ROOT = Path(__file__).parent.parent

BLEU = (37, 99, 235)
VERT = (22, 163, 74)
ROUGE = (220, 38, 38)
ORANGE = (234, 88, 12)
VIOLET = (147, 51, 234)
GRIS_FONCE = (34, 34, 34)
GRIS_CLAIR = (156, 163, 175)
FOND_BLEU = (240, 249, 255)
FOND_ROUGE = (254, 226, 226)
FOND_ORANGE = (255, 247, 237)
FOND_VERT = (220, 252, 231)
FOND_VIOLET = (250, 245, 255)
FOND_GRIS = (249, 250, 251)


class RapportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*GRIS_FONCE)
        self.cell(0, 10, "Rapport quotidien - Agent Invest", ln=True)
        self.set_draw_color(*BLEU)
        self.set_line_width(1)
        self.line(10, 22, 200, 22)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRIS_CLAIR)
        self.cell(0, 10, f"Page {self.page_no()} - Agent Invest - Ne constitue pas un conseil en investissement.", align="C")

    def section_title(self, txt):
        self.ln(3)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*BLEU)
        self.cell(0, 8, txt, ln=True)
        self.set_draw_color(*BLEU)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 60, self.get_y())
        self.ln(3)

    def paragraphe(self, txt, taille=10, gras=False, couleur=None):
        if couleur is None:
            couleur = GRIS_FONCE
        self.set_font("Helvetica", "B" if gras else "", taille)
        self.set_text_color(*couleur)
        self.set_x(10)
        self.multi_cell(0, 5, txt)


def _euros(v):
    try:
        return f"{float(v):,.0f} EUR".replace(",", " ")
    except (ValueError, TypeError):
        return "N/A"


def _classe_pv(pct):
    return VERT if pct >= 0 else ROUGE


# ============================================================
# MODE DIRECT : PDF sans Claude
# ============================================================

def generer_pdf_direct(user: str = paths.DEFAULT_USER) -> Path:
    """Genere un PDF a partir des tools locaux (sans Claude), utile pour test rapide."""
    pf = risk.calculer_portefeuille(user)
    alertes_conc = risk.alertes_concentration(user)
    alertes_sl = risk.alertes_stop_loss(user)
    alloc = risk.ecart_allocation(user)

    pdf = RapportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS_CLAIR)
    pdf.cell(0, 5, f"Genere le {datetime.now().strftime('%d/%m/%Y a %Hh%M')}", ln=True)
    pdf.ln(3)

    # Encart valeur
    y = pdf.get_y()
    pdf.set_fill_color(*FOND_BLEU)
    pdf.set_draw_color(*BLEU)
    pdf.rect(10, y, 190, 32, style="DF")
    pdf.set_xy(15, y + 3)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS_FONCE)
    pdf.cell(0, 5, "Valeur totale du portefeuille", ln=True)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(3, 105, 161)
    pdf.cell(0, 10, _euros(pf["total_valeur_eur"]), ln=True)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS_FONCE)
    pdf.cell(0, 5, f"Investi : {_euros(pf['total_cout_eur'])}", ln=True)
    pdf.set_x(15)
    signe = "+" if pf["plus_value_totale_eur"] >= 0 else ""
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*_classe_pv(pf["plus_value_totale_pct"]))
    pdf.cell(0, 5, f"Performance : {signe}{_euros(pf['plus_value_totale_eur'])} ({signe}{pf['plus_value_totale_pct']:.1f}%)", ln=True)
    pdf.set_y(y + 35)

    # Positions
    pdf.section_title("Positions detenues")
    _render_tableau_positions(pdf, pf["positions"])

    # Halal
    pdf.section_title("Conformite Halal")
    non_halal = [p for p in pf["positions"] if halal.check_halal(p["ticker"])["halal"] is False]
    if non_halal:
        for p in non_halal:
            statut = halal.check_halal(p["ticker"])
            _bloc_colore(pdf, f"{p['ticker']} ({statut['raison']}) - {p['poids_pct']:.1f}% = {_euros(p['valeur_actuelle_eur'])} A SORTIR", FOND_ROUGE, ROUGE)
    else:
        _bloc_colore(pdf, "Aucune position non-halal.", FOND_VERT, VERT)

    # Concentration
    pdf.section_title("Alertes de concentration")
    if alertes_conc:
        for a in alertes_conc:
            _bloc_colore(pdf, f"{a['ticker']} pese {a['poids_pct']}% (seuil {a['seuil_pct']}%)", FOND_ORANGE, ORANGE)
    else:
        _bloc_colore(pdf, "Aucune concentration excessive.", FOND_VERT, VERT)

    # Stop-loss
    pdf.section_title("Alertes stop-loss")
    if alertes_sl:
        for a in alertes_sl:
            _bloc_colore(pdf, f"{a['ticker']} a {a['plus_value_pct']}% (seuil {a['seuil_pct']}%)", FOND_ROUGE, ROUGE)
    else:
        _bloc_colore(pdf, "Aucun stop-loss atteint.", FOND_VERT, VERT)

    # Ecart alloc
    if isinstance(alloc.get("ecart_pct"), dict):
        pdf.section_title("Ecart avec ta strategie")
        _render_tableau_alloc(pdf, alloc)

    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    out = paths.reports_dir(user) / f"rapport_direct_{now}.pdf"
    pdf.output(str(out))
    return out


# ============================================================
# MODE CLAUDE : parse markdown -> PDF
# ============================================================

def generer_pdf_depuis_markdown(markdown: str, user: str = paths.DEFAULT_USER, titre_fichier: str | None = None) -> Path:
    """Convertit un rapport markdown Claude en PDF style Agent Invest."""
    pdf = RapportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS_CLAIR)
    pdf.cell(0, 5, f"Genere le {datetime.now().strftime('%d/%m/%Y a %Hh%M')}", ln=True)
    pdf.ln(3)

    lignes = markdown.split("\n")
    for ligne in lignes:
        _render_ligne_markdown(pdf, ligne)

    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    nom = titre_fichier or f"rapport_claude_{now}.pdf"
    out = paths.reports_dir(user) / nom
    pdf.output(str(out))
    return out


def _render_ligne_markdown(pdf, ligne: str):
    """Convertit une ligne markdown en element PDF."""
    l = ligne.rstrip()

    if not l.strip():
        pdf.ln(2)
        return

    # Titre H2 (##)
    if l.startswith("## "):
        pdf.section_title(l[3:].strip())
        return

    # Titre H1 (#)
    if l.startswith("# "):
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(*GRIS_FONCE)
        pdf.cell(0, 8, l[2:].strip(), ln=True)
        pdf.ln(2)
        return

    # Table markdown | ... | ... |
    if l.startswith("|"):
        # Skip separator lines |---|---|
        if re.match(r"^\|\s*[-:]+\s*\|", l):
            return
        cells = [c.strip() for c in l.split("|") if c.strip() != ""]
        _render_table_row(pdf, cells)
        return

    # Liste
    if l.strip().startswith(("- ", "* ")):
        txt = l.strip()[2:]
        _render_texte_avec_gras(pdf, f"- {txt}", indent=8)
        return

    # Flechede recommandation
    if l.strip().startswith("->"):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*BLEU)
        pdf.set_x(12)
        pdf.multi_cell(0, 5, l.strip())
        return

    # Ligne normale
    _render_texte_avec_gras(pdf, l)


def _render_table_row(pdf, cells: list[str]):
    """Rend une ligne de tableau markdown."""
    if not cells:
        return
    w = 190 / len(cells)
    is_header = all(cell and not cell.startswith("-") for cell in cells) and pdf.get_font_style() != "B"
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GRIS_FONCE)
    for c in cells:
        # Colorer les gains/pertes visibles
        couleur = GRIS_FONCE
        if "+" in c and "%" in c:
            couleur = VERT
        elif "-" in c and "%" in c:
            couleur = ROUGE
        pdf.set_text_color(*couleur)
        pdf.cell(w, 6, c[:35], border=1)
    pdf.ln()


def _render_texte_avec_gras(pdf, texte: str, indent: int = 10):
    """Rend un texte en gerant les **gras**."""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS_FONCE)
    pdf.set_x(indent)
    # Simplification : on retire les ** et on met tout en gras si la ligne commence par **
    if "**" in texte:
        clean = texte.replace("**", "")
        pdf.multi_cell(0, 5, clean)
    else:
        pdf.multi_cell(0, 5, texte)


def _render_tableau_positions(pdf, positions):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*BLEU)
    pdf.set_text_color(255, 255, 255)
    for h, w in [("Titre", 25), ("Halal", 22), ("Qte", 12), ("Poids", 15), ("Valeur", 28), ("Achat->Actuel", 40), ("Perf", 48)]:
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for i, p in enumerate(positions):
        statut = halal.check_halal(p["ticker"])
        if statut["halal"] is True:
            badge, badge_couleur = "HALAL", VERT
        elif statut["halal"] is False:
            badge, badge_couleur = "NON HALAL", ROUGE
        else:
            badge, badge_couleur = "A VERIFIER", ORANGE
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(*FOND_GRIS)
        pdf.set_text_color(*GRIS_FONCE)
        pdf.cell(25, 6, p["ticker"], border=1, fill=fill)
        pdf.set_text_color(*badge_couleur)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(22, 6, badge, border=1, align="C", fill=fill)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GRIS_FONCE)
        pdf.cell(12, 6, f"{p['quantite']:.0f}", border=1, align="R", fill=fill)
        pdf.cell(15, 6, f"{p['poids_pct']:.1f}%", border=1, align="R", fill=fill)
        pdf.cell(28, 6, _euros(p["valeur_actuelle_eur"]), border=1, align="R", fill=fill)
        pdf.cell(40, 6, f"{p['prix_achat_eur']:.2f} -> {p['prix_actuel_eur']:.2f}", border=1, align="C", fill=fill)
        pdf.set_text_color(*_classe_pv(p["plus_value_pct"]))
        pdf.set_font("Helvetica", "B", 9)
        signe = "+" if p["plus_value_eur"] >= 0 else ""
        pdf.cell(48, 6, f"{signe}{_euros(p['plus_value_eur'])} ({signe}{p['plus_value_pct']:.1f}%)", border=1, align="R", fill=fill)
        pdf.ln()


def _render_tableau_alloc(pdf, alloc):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*BLEU)
    pdf.set_text_color(255, 255, 255)
    for h, w in [("Categorie", 45), ("Cible", 35), ("Reel", 35), ("Ecart", 45)]:
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for i, k in enumerate(("actions", "etf", "cash")):
        if k not in alloc["ecart_pct"]:
            continue
        e = alloc["ecart_pct"][k]
        couleur = VERT if abs(e) < 5 else ROUGE
        signe = "+" if e >= 0 else ""
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(*FOND_GRIS)
        pdf.set_text_color(*GRIS_FONCE)
        pdf.cell(45, 6, k.capitalize(), border=1, fill=fill)
        pdf.cell(35, 6, f"{alloc['cible'][k]}%", border=1, align="R", fill=fill)
        pdf.cell(35, 6, f"{alloc['reel'][k]}%", border=1, align="R", fill=fill)
        pdf.set_text_color(*couleur)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(45, 6, f"{signe}{e}%", border=1, align="R", fill=fill)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)


def _bloc_colore(pdf, texte, fond, bordure):
    pdf.set_fill_color(*fond)
    pdf.set_draw_color(*bordure)
    pdf.set_line_width(0.8)
    y_debut = pdf.get_y()
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS_FONCE)
    pdf.multi_cell(190, 5, texte, fill=True, border=0)
    y_fin = pdf.get_y()
    pdf.rect(10, y_debut, 190, y_fin - y_debut, style="D")
    pdf.ln(3)


# Backward compat
def generer_pdf(user: str = paths.DEFAULT_USER) -> Path:
    return generer_pdf_direct(user)
