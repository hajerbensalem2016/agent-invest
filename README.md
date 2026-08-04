# Agent Invest - MVP v3

Conseiller financier IA halal propulse par Claude Agent SDK.
Multi-users + memoire SQLite + news multi-sources + connecteur IBKR.

## Fonctionnalites v3

- **Multi-users** : chaque user (toi + un autre par ex.) a son portefeuille et ses rapports isoles
- **Memoire SQLite** : historique complet rapports + recos + calibration confiance dans le temps
- **Portefeuille** : IBKR MCP live (recommande) ou CSV local par user
- **Prix / fondamentaux** : yfinance (gratuit)
- **Screening halal** : whitelist AAOIFI + ratios financiers
- **Actualites multi-sources** : Alpha Vantage + Marketaux + Finnhub avec dedup + score confiance (1-3)
- **Analyse Claude** : 13 tools MCP orchestres, rapport 11 sections
- **Rapport PDF** : layout structure avec badges halal, sentiments colores
- **Calibration** : apres N recos executees + evaluees, l'agent connait son taux de succes reel par tranche de confiance

## Setup rapide

```bash
git clone https://github.com/hajerbensalem2016/agent-invest.git
cd agent-invest
python -m venv .venv
source .venv/bin/activate      # Linux/WSL
# ou : .venv\Scripts\activate  # Windows CMD
pip install -r requirements.txt
```

Voir [INSTALL.md](INSTALL.md) pour le guide complet (cles API news + IBKR).

## Utilisation

### Commandes courantes
```bash
# Voir les users disponibles
python cli.py users

# Portefeuille brut d'un user (defaut : hajer)
python cli.py portefeuille
python cli.py --user demo portefeuille

# Test rapide d'un ticker
python cli.py check AAPL

# Rapport complet Claude (markdown + PDF + memoire)
python cli.py rapport
python cli.py --user demo rapport

# PDF direct sans Claude
python cli.py pdf
```

### Commandes memoire
```bash
# Historique des rapports
python cli.py --user hajer historique
python cli.py historique --limit 50

# Recommandations passees
python cli.py recos                       # tous
python cli.py recos --ticker AAPL         # sur AAPL seulement

# Marquer une reco (statut : executed | rejected | expired)
python cli.py marquer-reco 42 executed

# Calibration confiance (necessite des recos executees + evaluees)
python cli.py calibration
```

### News multi-sources
```bash
python cli.py news AAPL
```
Necessite au moins une cle API news dans `config/secrets.yaml`.

## Structure

```
agent-invest/
├── users/                     UN DOSSIER PAR USER
│   ├── hajer/
│   │   ├── portefeuille.csv
│   │   ├── strategie.yaml
│   │   └── reports/           .md et .pdf de ce user
│   └── demo/
│       ├── portefeuille.csv
│       ├── strategie.yaml
│       └── reports/
├── config/
│   ├── halal_whitelist.yaml   commun a tous les users
│   ├── secrets.example.yaml
│   └── secrets.yaml           tes cles API (NON commit)
├── memory/
│   └── agent_invest.sqlite    rapports + recos + evaluations
├── system_prompt.txt          role Claude + workflow + format
├── tools/
│   ├── paths.py               resolveur chemins par user
│   ├── market.py              prix + fondamentaux (yfinance)
│   ├── halal.py               screening AAOIFI
│   ├── risk.py                P&L, concentration, allocation
│   ├── news_multisource.py    Alpha Vantage + Marketaux + Finnhub
│   ├── memory.py              SQLite historique + recos + calibration
│   ├── ibkr_client.py         stub + doc connecteur IBKR MCP
│   ├── secrets.py             loader cles API
│   └── pdf_report.py          generateur PDF
├── orchestrator.py            boucle Claude Agent SDK + 13 tools MCP
├── cli.py                     point d'entree CLI
└── requirements.txt
```

## Boucle apprentissage de l'agent

L'agent devient meilleur au fil du temps :

1. **Chaque rapport** logge automatiquement dans SQLite (contenu + recos extraites)
2. **Tu executes** une reco (achat/vente reel) et fais `python cli.py marquer-reco ID executed`
3. **Apres 30-90 jours**, tu evalues manuellement le resultat (via un script/interface a venir)
4. L'agent voit sa **calibration reelle** (`python cli.py calibration`) et l'utilise pour ajuster ses futurs conseils

## Format du rapport genere

11 sections numerotees :

1. Statut global
2. Contexte marche (Fed, indices, macro)
3. Positions detenues
4. Actualites par position (avec score confiance)
5. Impact des actualites sur le portefeuille
6. Opportunites marche (watchlist halal x news)
7. Conformite halal
8. Alertes concentration
9. Alertes stop-loss
10. Ecart avec la strategie
11. Recommandations synthese (tableau)
+ Sources URLs

## Prochaines phases

- **P4** : dashboard web (Flask/FastAPI) + planification cron quotidienne
- **P5** : execution semi-auto via IBKR MCP (drafts d'ordres pre-remplis)
- **P6** : evaluation automatique des recos (script qui compare prix J+30, J+90 au prix reco)
