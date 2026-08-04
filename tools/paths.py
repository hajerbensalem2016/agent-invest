"""Resolveur de chemins par utilisateur."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
DEFAULT_USER = "hajer"


def user_dir(user: str = DEFAULT_USER) -> Path:
    """Retourne le repertoire d'un user, cree s'il n'existe pas."""
    d = ROOT / "users" / user
    d.mkdir(parents=True, exist_ok=True)
    (d / "reports").mkdir(exist_ok=True)
    return d


def portefeuille_path(user: str = DEFAULT_USER) -> Path:
    return user_dir(user) / "portefeuille.csv"


def strategie_path(user: str = DEFAULT_USER) -> Path:
    return user_dir(user) / "strategie.yaml"


def reports_dir(user: str = DEFAULT_USER) -> Path:
    return user_dir(user) / "reports"


def memory_db_path() -> Path:
    """DB SQLite unique (tous les users), path fixe."""
    d = ROOT / "memory"
    d.mkdir(exist_ok=True)
    return d / "agent_invest.sqlite"


def list_users() -> list[str]:
    """Liste tous les users disponibles (dossiers dans users/)."""
    users_root = ROOT / "users"
    if not users_root.exists():
        return []
    return sorted([p.name for p in users_root.iterdir() if p.is_dir()])
