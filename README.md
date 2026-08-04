# Agent Invest - MVP v2

Conseiller financier IA halal propulse par Claude Agent SDK.
Multi-sources news + connecteur IBKR + rapport PDF quotidien.

## Fonctionnalites v2

- **Portefeuille** : IBKR MCP live (recommande) ou CSV local
- **Prix / fondamentaux** : yfinance (gratuit)
- **Screening halal** : whitelist AAOIFI + ratios financiers
- **Actualites multi-sources** : Alpha Vantage + Marketaux + Finnhub avec dedup + score confiance (1-3)
- **Analyse Claude** : boucle agentique orchestre 10 tools, redige rapport 11 sections
- **Rapport PDF** : layout structure avec badges halal, sentiments colores, tableaux

## Ce qu'il ne fait pas encore

- Pas de memoire SQLite historique recos (Phase 3)
- Pas de backtesting recos passees (Phase 3)
- Pas de dashboard web (Phase 4)

## Installation

Voir [INSTALL.md](INSTALL.md) pour le guide pas a pas.

## Setup rapide

```bash
git clone https://github.com/hajerbensalem2016/agent-invest.git
cd agent-invest
python -m venv .venv
source .venv/bin/activate      # Linux/WSL
# ou : .venv\Scripts\activate  # Windows CMD
pip install -r requirements.txt
```

## Configuration cles API news (optionnel mais recommande)

Copier le template :
```bash
cp config/secrets.example.yaml config/secrets.yaml
```

Puis creer les comptes gratuits et remplir les cles :
- Alpha Vantage : https://www.alphavantage.co/support/#api-key (25 req/jour)
- Marketaux : https://www.marketaux.com/register (100 req/jour)
- Finnhub : https://finnhub.io/register (60 req/min)

Sans cles, les news seront simplement vides mais tout le reste marche.

## Configuration connecteur IBKR (recommande, evite CSV manuel)

1. Dans Claude Code ou claude.ai, aller dans Settings > Connectors
2. Rechercher "Interactive Brokers", cliquer Add
3. Login IBKR direct, autoriser l'acces
4. Claude aura automatiquement acces aux positions live

Bug connu (GitHub #571) : parfois 0 tools exposes. Verifier dans Claude que
les tools IBKR (get_account_positions, etc.) sont bien listes. Sinon utiliser
le fallback CSV en editant portefeuille.csv.

## Utilisation

```bash
# Rapport quotidien complet (Claude + PDF)
python cli.py rapport

# PDF direct sans Claude (rapide, pour test)
python cli.py pdf

# Test news multi-sources sur un ticker
python cli.py news AAPL

# Test screening halal + prix + fondamentaux
python cli.py check AAPL

# Portefeuille brut
python cli.py portefeuille
```

## Structure

```
agent-invest/
├── config/
│   ├── strategie.yaml         profil investisseur + valeurs + seuils
│   ├── halal_whitelist.yaml   tickers halal + exclus AAOIFI
│   ├── secrets.example.yaml   template cles API news
│   └── secrets.yaml           TES cles (NON commit, dans .gitignore)
├── portefeuille.csv           tes positions (fallback si pas d'IBKR MCP)
├── system_prompt.txt          role Claude + workflow + format rapport
├── tools/
│   ├── market.py              prix + fondamentaux (yfinance)
│   ├── halal.py               screening AAOIFI
│   ├── risk.py                P&L, concentration, allocation
│   ├── news_multisource.py    Alpha Vantage + Marketaux + Finnhub agreges
│   ├── ibkr_client.py         stub + doc connecteur IBKR MCP
│   ├── secrets.py             loader cles API
│   └── pdf_report.py          generateur PDF (direct ou depuis markdown)
├── orchestrator.py            boucle Claude Agent SDK + 10 tools MCP
├── cli.py                     point d'entree (rapport / pdf / news / check)
└── reports/                   rapports generes (md + pdf)
```

## Format du rapport genere

11 sections numerotees :

1. Statut global (valeur + P&L + verdict)
2. Contexte marche (Fed, indices, macro)
3. Positions detenues (tableau)
4. Actualites par position (avec score confiance multi-sources)
5. Impact des actualites sur le portefeuille (news -> action)
6. Opportunites marche (watchlist halal x news)
7. Conformite halal (non-halal a sortir)
8. Alertes concentration
9. Alertes stop-loss
10. Ecart avec la strategie (cible vs reel)
11. Recommandations synthese (tableau final)
+ Sources URLs des news citees

## Prochaines phases

- **P3** : SQLite memoire recos + backtesting (savoir ta calibration reelle)
- **P4** : dashboard web + planification cron quotidienne
- **P5** : execution semi-automatique via IBKR MCP (drafts d'ordres)
