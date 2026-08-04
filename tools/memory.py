"""Memoire SQLite : historique rapports + recos + calibration confiance.

Schema :
- reports : chaque rapport genere (metadata + markdown complet)
- recos : chaque recommandation d'action extraite d'un rapport
- reco_evaluations : evaluation post-mortem d'une reco (a J+30, J+90)

L'agent peut :
- Se souvenir de ses recos precedentes (get_recos_precedentes)
- Voir si ses recos passees ont ete bonnes (get_calibration)
- Detecter ses biais (secteur sur-recommande, tendance a trop de confiance...)
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime

from tools import paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    date TEXT NOT NULL,
    valeur_totale_eur REAL,
    plus_value_totale_eur REAL,
    plus_value_totale_pct REAL,
    nb_positions INTEGER,
    contenu_md TEXT
);

CREATE TABLE IF NOT EXISTS recos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    report_id INTEGER,
    date TEXT NOT NULL,
    action TEXT NOT NULL,          -- VENDRE, ACHETER, REDUIRE, ATTENDRE, SURVEILLER, CASH
    ticker TEXT,
    quantite TEXT,
    justification TEXT,
    confiance INTEGER,             -- 0-100
    horizon TEXT,
    statut TEXT DEFAULT 'pending', -- pending, executed, rejected, expired
    date_statut TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(id)
);

CREATE TABLE IF NOT EXISTS reco_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reco_id INTEGER NOT NULL,
    date_eval TEXT NOT NULL,
    delta_pct REAL,                -- perf du titre depuis la reco
    verdict TEXT,                  -- correct, incorrect, neutre
    note TEXT,
    FOREIGN KEY (reco_id) REFERENCES recos(id)
);

CREATE INDEX IF NOT EXISTS idx_reports_user_date ON reports(user, date DESC);
CREATE INDEX IF NOT EXISTS idx_recos_user_date ON recos(user, date DESC);
CREATE INDEX IF NOT EXISTS idx_recos_ticker ON recos(ticker);
"""


@contextmanager
def _conn():
    conn = sqlite3.connect(str(paths.memory_db_path()))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def log_report(user: str, valeur_totale: float, pv_totale: float, pv_pct: float,
               nb_positions: int, contenu_md: str) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO reports(user, date, valeur_totale_eur, plus_value_totale_eur, "
            "plus_value_totale_pct, nb_positions, contenu_md) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user, now, valeur_totale, pv_totale, pv_pct, nb_positions, contenu_md),
        )
        return cur.lastrowid


def log_reco(user: str, report_id: int, action: str, ticker: str | None,
             quantite: str | None, justification: str, confiance: int | None,
             horizon: str | None) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO recos(user, report_id, date, action, ticker, quantite, "
            "justification, confiance, horizon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user, report_id, now, action, ticker, quantite, justification, confiance, horizon),
        )
        return cur.lastrowid


def marquer_reco(reco_id: int, statut: str) -> bool:
    """statut = executed | rejected | expired."""
    if statut not in ("executed", "rejected", "expired"):
        raise ValueError(f"statut invalide : {statut}")
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            "UPDATE recos SET statut = ?, date_statut = ? WHERE id = ?",
            (statut, now, reco_id),
        )
        return cur.rowcount > 0


def get_historique_rapports(user: str, limit: int = 30) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, date, valeur_totale_eur, plus_value_totale_eur, plus_value_totale_pct, "
            "nb_positions FROM reports WHERE user = ? ORDER BY date DESC LIMIT ?",
            (user, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_rapport_complet(report_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        return dict(row) if row else None


def get_recos_precedentes(user: str, ticker: str | None = None, limit: int = 20) -> list[dict]:
    """Retourne les dernieres recos d'un user, optionnellement filtrees par ticker."""
    with _conn() as c:
        if ticker:
            rows = c.execute(
                "SELECT * FROM recos WHERE user = ? AND ticker = ? ORDER BY date DESC LIMIT ?",
                (user, ticker, limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM recos WHERE user = ? ORDER BY date DESC LIMIT ?",
                (user, limit),
            ).fetchall()
        return [dict(r) for r in rows]


def get_recos_par_statut(user: str, statut: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM recos WHERE user = ? AND statut = ? ORDER BY date DESC",
            (user, statut),
        ).fetchall()
        return [dict(r) for r in rows]


def get_calibration_confiance(user: str) -> dict:
    """Statistiques : par tranche de confiance, quel taux de succes des recos executees ?

    Necessite que les recos executees aient ete evaluees (via reco_evaluations).
    """
    with _conn() as c:
        rows = c.execute(
            """
            SELECT
                CASE
                    WHEN r.confiance >= 80 THEN '80-100'
                    WHEN r.confiance >= 60 THEN '60-79'
                    WHEN r.confiance >= 40 THEN '40-59'
                    ELSE '0-39'
                END AS tranche,
                COUNT(*) AS total,
                SUM(CASE WHEN e.verdict = 'correct' THEN 1 ELSE 0 END) AS succes
            FROM recos r
            LEFT JOIN reco_evaluations e ON e.reco_id = r.id
            WHERE r.user = ? AND r.statut = 'executed' AND e.id IS NOT NULL
            GROUP BY tranche
            ORDER BY tranche DESC
            """,
            (user,),
        ).fetchall()

        result = {"tranches": [], "total_recos_evaluees": 0}
        for r in rows:
            taux = round(r["succes"] / r["total"] * 100, 1) if r["total"] else 0
            result["tranches"].append({
                "tranche_confiance": r["tranche"],
                "total_recos": r["total"],
                "succes": r["succes"],
                "taux_succes_pct": taux,
            })
            result["total_recos_evaluees"] += r["total"]
        return result


def evaluer_reco(reco_id: int, delta_pct: float, verdict: str, note: str = "") -> int:
    """Enregistre une evaluation post-mortem d'une reco."""
    if verdict not in ("correct", "incorrect", "neutre"):
        raise ValueError(f"verdict invalide : {verdict}")
    now = datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO reco_evaluations(reco_id, date_eval, delta_pct, verdict, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (reco_id, now, delta_pct, verdict, note),
        )
        return cur.lastrowid


def extraire_et_logger_recos_depuis_rapport(user: str, report_id: int, markdown: str) -> int:
    """Parse la section '## 11. Recommandations synthese' du rapport et log chaque reco.

    Format attendu (tableau markdown) :
    | Action | Ticker | Qte | Justification | Confiance | Horizon |
    | VENDRE | JPM | 4 | Non-halal + ATH | 95/100 | immediat |
    """
    import re

    # Isoler la section synthese
    match = re.search(r"##\s*(?:11\.)?\s*Recommandations synth[eè]se(.*?)(?=\n##|\Z)",
                      markdown, re.DOTALL | re.IGNORECASE)
    if not match:
        return 0

    section = match.group(1)
    nb_logged = 0
    for ligne in section.split("\n"):
        if not ligne.strip().startswith("|"):
            continue
        # Skip header et separateur
        cells = [c.strip() for c in ligne.split("|") if c.strip()]
        if len(cells) < 4:
            continue
        # Skip separateur --- et header
        if cells[0].startswith("-") or cells[0].lower() == "action":
            continue

        action = cells[0]
        ticker = cells[1] if len(cells) > 1 else None
        quantite = cells[2] if len(cells) > 2 else None
        justification = cells[3] if len(cells) > 3 else ""
        confiance_str = cells[4] if len(cells) > 4 else "0"
        horizon = cells[5] if len(cells) > 5 else None

        # Parse confiance "95/100" ou "95"
        conf_match = re.search(r"(\d+)", confiance_str)
        confiance = int(conf_match.group(1)) if conf_match else None

        log_reco(user, report_id, action, ticker, quantite, justification, confiance, horizon)
        nb_logged += 1

    return nb_logged
