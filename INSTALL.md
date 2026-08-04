# Installation pas a pas

Guide pour installer l'agent sur un nouveau PC (Windows ou Linux/WSL).

---

## Prerequis a installer sur le PC

1. **Python 3.10 ou plus recent** - https://python.org/downloads/
   - Windows : coche **"Add Python to PATH"** pendant l'install
2. **Git** - https://git-scm.com/download
3. **Node.js LTS** - https://nodejs.org (necessaire pour Claude Code)
4. **Claude Code** - https://claude.com/claude-code
   - Apres install, lance `claude login` dans un terminal et connecte-toi avec ton compte **Claude Max**
   - C'est cette auth qui sera utilisee par l'agent (pas besoin de cle API separee)

---

## Etape 1 - Cloner le repo

```bash
git clone https://github.com/hajerbensalem2016/agent-invest.git
cd agent-invest
```

---

## Etape 2 - Creer l'environnement Python isole

### Sur Windows (CMD ou PowerShell)
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Sur Linux / WSL / Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Le prompt doit maintenant commencer par `(.venv)`.

---

## Etape 3 - Installer les dependances

```bash
pip install -r requirements.txt
```

Prend 1-3 min. A la fin, tu dois voir `Successfully installed claude-agent-sdk-X.X yfinance-X.X ...`.

---

## Etape 4 - Test rapide (sans Claude)

Verifier le screening halal sur un ticker connu :

```bash
python cli.py check AAPL
python cli.py check JPM
```

- **AAPL** doit sortir `"halal": true`
- **JPM** doit sortir `"halal": false, "raison": "banque conventionnelle"`

Verifier le portefeuille de demo :

```bash
python cli.py portefeuille
```

Tu dois voir 6 positions avec P&L, poids, alertes.

---

## Etape 5 - Generer le rapport quotidien complet (avec Claude)

```bash
python cli.py rapport
```

Ca prend 30-60 sec (Claude appelle les outils en boucle).

Le rapport est **affiche dans le terminal** + **sauvegarde dans `reports/rapport_YYYY-MM-DD_HHMM.md`**.

---

## Personnalisation

Une fois que ca marche :

1. **Ton profil investisseur** : edite `config/strategie.yaml`
2. **Ton vrai portefeuille** : edite `portefeuille.csv` avec tes positions IBKR
3. **Ta whitelist halal** : enrichis `config/halal_whitelist.yaml` au fil de tes verifications Zoya

---

## Problemes connus

### Sur WSL avec VPN ArcelorMittal / Zscaler

Zscaler intercepte HTTPS et casse yfinance. 2 workarounds :

**Option A (rapide)** - Utiliser le bundle CA systeme :
```bash
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
python cli.py check AAPL
```

Pour rendre permanent, ajoute la ligne `export ...` dans `~/.bashrc`.

**Option B (propre)** - Extraire le certif Zscaler et l'ajouter au bundle certifi. Voir doc interne AMF.

### `python3 -m venv` echoue avec "ensurepip is not available" (Ubuntu/WSL)

```bash
apt install python3.10-venv -y
```

Si apt echoue a cause de Zscaler, telecharge pip manuellement :
```bash
curl -sS -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
python3 /tmp/get-pip.py
```

Puis skip le venv et installe directement :
```bash
python3 -m pip install -r requirements.txt
```

---

## Prochaines phases (roadmap)

- **P2** : Connecteur IBKR (positions live via ib_insync), memoire SQLite historique recos
- **P3** : Veille news (RSS Reuters/FT), macro Fed/BCE croisees
- **P4** : Backtesting recos passees, calibration confiance
- **P5** : Dashboard web + planification quotidienne automatique
