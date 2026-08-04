# Installation pas a pas

Guide pour installer l'agent sur un nouveau PC (Windows ou Linux/WSL).

---

## Prerequis a installer

1. **Python 3.10+** - https://python.org/downloads/
   - Windows : coche **"Add Python to PATH"** pendant l'install
2. **Git** - https://git-scm.com/download
3. **Node.js LTS** - https://nodejs.org (necessaire pour Claude Code)
4. **Claude Code** - https://claude.com/claude-code
   - Apres install, lance `claude login` dans un terminal
   - Utilise ton compte **Claude Max**
   - C'est cette auth qui sera utilisee par l'agent (pas besoin de cle API separee)

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

Le prompt doit maintenant commencer par `(.venv)`.

---

## Etape 3 - Installer les dependances

```bash
pip install -r requirements.txt
```

Prend 1-3 min. Doit installer : claude-agent-sdk, yfinance, PyYAML, fpdf2, requests.

---

## Etape 4 - Cles API news (optionnel mais recommande)

Sans cles, les news seront vides. Le reste marche.

### 4.1 - Copier le template
```bash
cp config/secrets.example.yaml config/secrets.yaml
```

### 4.2 - Creer les comptes gratuits (5 min)

**Alpha Vantage** (25 req/jour)
- https://www.alphavantage.co/support/#api-key
- Copie la cle affichee apres inscription

**Marketaux** (100 req/jour)
- https://www.marketaux.com/register
- Dashboard > API token

**Finnhub** (60 req/min)
- https://finnhub.io/register
- Dashboard > API keys

### 4.3 - Remplir config/secrets.yaml

Colle tes 3 cles a la place des placeholders. **NE JAMAIS commit ce fichier** (il est dans .gitignore).

---

## Etape 5 - Connecteur IBKR (recommande, pour positions live)

Sans IBKR, l'agent utilise `portefeuille.csv` en fallback.

### 5.1 - Dans Claude
- Ouvre Claude Code ou claude.ai
- Va dans **Settings > Connectors**
- Recherche **"Interactive Brokers"**
- Clique **Add** puis **Connect**

### 5.2 - Login IBKR
- Ecran de login IBKR officiel s'affiche
- Login avec tes credentials IBKR habituels
- Autorise l'acces au compte

### 5.3 - Verifier les tools exposes
Dans Claude, tape :
```
Liste les tools IBKR disponibles
```
Tu dois voir : `get_account_positions`, `get_account_balances`, `get_market_data`, etc.

**Bug connu** : parfois 0 tools affiches (issue GitHub #571). Si c'est le cas :
- Deconnecte le connecteur, reconnecte-toi
- Sinon utilise le fallback `portefeuille.csv`

---

## Etape 6 - Tests

### Test 1 : Screening halal (sans Claude, sans API)
```bash
python cli.py check AAPL
python cli.py check JPM
```
AAPL doit sortir halal, JPM non halal.

### Test 2 : News multi-sources (necessite cles API)
```bash
python cli.py news AAPL
```
Tu vois les news agregees avec score confiance 1-3 par news.

### Test 3 : Portefeuille brut
```bash
python cli.py portefeuille
```

### Test 4 : PDF direct (sans Claude)
```bash
python cli.py pdf
```
Le PDF est dans `reports/rapport_direct_YYYY-MM-DD.pdf`.

### Test 5 : Rapport complet Claude (le vrai truc)
```bash
python cli.py rapport
```
Prend 1-2 min. Claude appelle les tools en boucle, redige les 11 sections, sauvegarde en markdown ET en PDF.

---

## Personnalisation

- **Ton profil** : `config/strategie.yaml` (objectifs, seuils, alloc cible)
- **Ton portefeuille** : `portefeuille.csv` (fallback si pas d'IBKR live)
- **Ta whitelist halal** : `config/halal_whitelist.yaml`

---

## Problemes connus

### `python3 -m venv` echoue avec "ensurepip is not available"

```bash
apt install python3.10-venv -y
```

Si apt echoue (Zscaler/proxy), telecharge pip manuellement :
```bash
curl -sS -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
python3 /tmp/get-pip.py
python3 -m pip install -r requirements.txt
```

### yfinance echoue avec KeyError 'A3' ou SSL error

Zscaler/proxy corporate intercepte Yahoo. Solutions :
- Tester sur PC perso (pas de proxy)
- Utiliser GitHub Codespaces ou Google Colab
- Downgrader : `pip install "yfinance==0.2.40"`

### News APIs renvoient rien

- Verifie que `config/secrets.yaml` existe et contient tes vraies cles (pas les placeholders)
- Verifie que t'as pas depasse la limite quotidienne (25/j Alpha Vantage, 100/j Marketaux)
- Test individuel : `python cli.py news AAPL` -> regarde "Sources configurees : X/3"

### Claude Agent SDK ne trouve pas l'auth

Assure-toi d'avoir fait `claude login` avec ton compte Claude Max avant de lancer `python cli.py rapport`.
