# Installation pas a pas

Guide pour installer l'agent sur un nouveau PC (Windows ou Linux/WSL).

---

## Prerequis a installer

1. **Python 3.10+** - https://python.org/downloads/
   - Windows : coche **"Add Python to PATH"** pendant l'install
2. **Git** - https://git-scm.com/download
3. **Node.js LTS** - https://nodejs.org (necessaire pour Claude Code)
4. **Claude Code** - https://claude.com/claude-code
   - Apres install, lance `claude login` avec ton compte **Claude Max**

---

## Etape 1 - Cloner le repo

```bash
git clone https://github.com/hajerbensalem2016/agent-invest.git
cd agent-invest
```

---

## Etape 2 - Environnement Python isole

### Windows (CMD ou PowerShell)
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Linux / WSL / Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Etape 3 - Installer les dependances

```bash
pip install -r requirements.txt
```

---

## Etape 4 - Configurer ton profil utilisateur

Le repo contient deja un user `hajer` par defaut. Pour l'utiliser, modifie :
- `users/hajer/strategie.yaml` (ton profil : age, epargne, allocation cible, seuils)
- `users/hajer/portefeuille.csv` (tes vraies positions IBKR)

Pour creer un 2eme user :
```bash
mkdir -p users/marie/reports
cp users/hajer/strategie.yaml users/marie/strategie.yaml
cp users/hajer/portefeuille.csv users/marie/portefeuille.csv
# puis edite marie/strategie.yaml et marie/portefeuille.csv
```

Utilise-le avec `--user marie` :
```bash
python cli.py --user marie rapport
```

---

## Etape 5 - Cles API news (optionnel mais recommande)

Sans cles, les news seront vides. Le reste marche.

### 5.1 - Copier le template
```bash
cp config/secrets.example.yaml config/secrets.yaml
```

### 5.2 - Creer les comptes gratuits (5 min chacun)

**Alpha Vantage** (25 req/jour, sentiment inclus)
- https://www.alphavantage.co/support/#api-key
- Copie la cle affichee apres inscription

**Marketaux** (100 req/jour, 5000+ sources)
- https://www.marketaux.com/register
- Dashboard > API token

**Finnhub** (60 req/min, ticker tagging natif)
- https://finnhub.io/register
- Dashboard > API keys

### 5.3 - Remplir config/secrets.yaml

Colle tes 3 cles a la place des placeholders. **NE JAMAIS commit ce fichier** (il est dans .gitignore).

---

## Etape 6 - Connecteur IBKR (recommande, pour positions live)

Sans IBKR, l'agent utilise `users/USER/portefeuille.csv` en fallback.

### 6.1 - Prerequis
- Un compte Interactive Brokers actif (login web habituel)
- Claude Code installe et loggue (etape 0)

### 6.2 - Brancher le connecteur MCP IBKR

**Option A - Depuis claude.ai (recommande pour test)**
1. Va sur https://claude.ai
2. Clique ton avatar en haut a droite > **Settings** > **Connectors**
3. Recherche **"Interactive Brokers"**
4. Clique **Add** puis **Connect**
5. Ecran de login IBKR s'affiche - login normal
6. Autorise l'acces au compte

**Option B - Depuis Claude Code CLI**
Le connecteur IBKR MCP est un serveur MCP officiel Anthropic. Suit la doc :
- https://claude.com/connectors/interactive-brokers
- https://docs.claude.com/en/docs/agents-and-tools/mcp

### 6.3 - Verifier les tools exposes

Dans une session Claude, tape :
```
Liste tous les tools IBKR disponibles
```
Tu dois voir :
- `get_account_positions`
- `get_account_balances`
- `get_account_summary`
- `get_market_data`
- `get_open_orders`
- `place_order` (drafte l'ordre, approbation manuelle requise)

### 6.4 - Bug connu (issue GitHub #571)

Certains users voient le connecteur "Connected" mais 0 tools exposes. Si c'est ton cas :
1. Deconnecte le connecteur (Settings > Connectors > Disconnect)
2. Reconnecte-toi
3. Ferme et rouvre Claude (ou refresh la page)
4. Si toujours rien : utilise le fallback CSV (`users/USER/portefeuille.csv`) en attendant le fix

Suivi : https://github.com/anthropics/claude-ai-mcp/issues/571

### 6.5 - Utilisation avec agent-invest

Quand le MCP IBKR est branche a Claude :
- L'agent Claude appellera prioritairement `get_account_positions` (IBKR live)
- Le fallback CSV local sera utilise si les tools IBKR ne sont pas listes
- Le comportement est controle par `system_prompt.txt` (regle : "PRIVILEGIE ses tools officiels")

---

## Etape 7 - Tests

### Test 1 : Users disponibles
```bash
python cli.py users
```

### Test 2 : Screening halal (sans Claude, sans API)
```bash
python cli.py check AAPL      # halal
python cli.py check JPM       # non halal
```

### Test 3 : Portefeuille brut
```bash
python cli.py portefeuille
python cli.py --user demo portefeuille
```

### Test 4 : News multi-sources (necessite cles API)
```bash
python cli.py news AAPL
```

### Test 5 : PDF direct (sans Claude)
```bash
python cli.py pdf
python cli.py --user demo pdf
```

### Test 6 : Rapport Claude complet (le vrai truc)
```bash
python cli.py rapport
```
Prend 1-2 min. Sauve markdown + PDF + logge dans SQLite.

### Test 7 : Verifier la memoire
```bash
python cli.py historique
python cli.py recos
```

### Test 8 : Marquer une reco
```bash
python cli.py marquer-reco 1 executed
python cli.py calibration
```

---

## Problemes connus

### yfinance echoue avec KeyError 'A3' ou SSL error
Zscaler/proxy corporate intercepte Yahoo. Solutions :
- Tester sur PC perso (pas de proxy)
- Utiliser GitHub Codespaces ou Google Colab
- Downgrader : `pip install "yfinance==0.2.40"`

### News APIs renvoient rien
- Verifie `config/secrets.yaml` contient tes vraies cles (pas les placeholders)
- Verifie que t'as pas depasse la limite quotidienne
- Test : `python cli.py news AAPL` -> regarde "Sources configurees : X/3"

### Claude Agent SDK ne trouve pas l'auth
Assure-toi d'avoir fait `claude login` avec ton compte Claude Max.

### IBKR MCP : 0 tools exposes
Voir etape 6.4 (bug #571 connu).
