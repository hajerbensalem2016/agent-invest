# Agent Invest — MVP squelette

Conseiller financier IA halal, propulse par Claude Agent SDK.

## Ce qu'il fait (aujourd'hui)

- Charge ton portefeuille depuis `portefeuille.csv`
- Recupere prix live via yfinance (gratuit)
- Screene halal via `config/halal_whitelist.yaml` (liste manuelle)
- Calcule P&L, poids, alertes concentration/stop-loss
- Claude orchestre les outils en boucle et redige un rapport structure

## Ce qu'il fait PAS (encore)

- Pas de connexion IBKR live (CSV manuel pour l'instant)
- Pas de news / macro (Phase 2)
- Pas de memoire historique des recos (Phase 2)
- Pas de backtesting (Phase 3)

## Installation

```bash
cd /mnt/c/Users/E034980/Desktop/tesrtacl/agent-invest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Prerequis Claude Agent SDK :** tu dois avoir Claude Code installe et etre logguee avec ton abonnement Claude Max. Le SDK reutilise cette authentification, aucune cle API a fournir.

## Utilisation

### 1. Tester un ticker (sans Claude, rapide)
```bash
python cli.py check AAPL
python cli.py check JPM       # doit sortir "non halal"
```

### 2. Voir ton portefeuille brut (calculs Python seulement)
```bash
python cli.py portefeuille
```

### 3. Generer le rapport quotidien complet (avec Claude)
```bash
python cli.py rapport
```

Le rapport est affiche + sauvegarde dans `reports/rapport_YYYY-MM-DD_HHMM.md`.

## Structure

```
agent-invest/
├── config/
│   ├── strategie.yaml         profil investisseur + valeurs + seuils
│   └── halal_whitelist.yaml   tickers halal + tickers exclus
├── portefeuille.csv           tes positions (ticker, quantite, prix achat)
├── system_prompt.txt          role Claude + format rapport
├── tools/
│   ├── market.py              prix + fondamentaux (yfinance)
│   ├── halal.py               screening AAOIFI
│   └── risk.py                P&L, concentration, allocation
├── orchestrator.py            boucle Claude Agent SDK + tools
├── cli.py                     point d'entree
└── reports/                   rapports generes
```

## Personnalisation

1. **Ton profil** : edite `config/strategie.yaml` (objectifs, seuils, allocation cible).
2. **Ton portefeuille** : edite `portefeuille.csv` avec tes vraies positions.
3. **Ta whitelist halal** : enrichis `config/halal_whitelist.yaml` au fil de tes verifications Zoya.

## Prochaines phases (a discuter)

- **P2** : connecteur IBKR (positions live), SQLite historique recos
- **P3** : news RSS + macro Fed/BCE croisees, calibration confiance
- **P4** : backtesting recos passees, dashboard web
