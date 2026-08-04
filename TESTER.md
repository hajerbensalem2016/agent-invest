# Guide de test pas a pas

Deux environnements de test :
- **A. Sur ton PC perso** : test COMPLET (avec Claude, rapport bout-en-bout)
- **B. Sur Google Colab** : test PARTIEL (sans Claude, mais utile pour valider tools + yfinance)

---

## A. Test sur ton PC perso (test complet)

### Prerequis

Installer ces 4 outils avant de commencer :

1. **Python 3.10+**
   - https://python.org/downloads/
   - Windows : **coche "Add Python to PATH"** pendant l'install
2. **Git**
   - https://git-scm.com/download
3. **Node.js LTS**
   - https://nodejs.org
4. **Claude Code**
   - https://claude.com/claude-code
   - Apres install, dans un terminal : `claude login`
   - Utilise ton compte **Claude Max**

### Etape 1 - Cloner le repo

```bash
git clone https://github.com/hajerbensalem2016/agent-invest.git
cd agent-invest
```

### Etape 2 - Environnement Python

**Windows CMD ou PowerShell :**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**Linux / WSL / Mac :**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Le prompt doit maintenant commencer par `(.venv)`.

### Etape 3 - Installer les dependances

```bash
pip install -r requirements.txt
```

Prend 1-3 min. Attends `Successfully installed ...`.

### Etape 4 - Configurer les cles API news (optionnel mais recommande)

Sans cles, les news seront vides. Le reste marche.

#### 4.1 - Copier le template
```bash
# Windows
copy config\secrets.example.yaml config\secrets.yaml

# Linux/WSL/Mac
cp config/secrets.example.yaml config/secrets.yaml
```

#### 4.2 - Creer les 3 comptes gratuits (5 min chacun)

- **Alpha Vantage** (25 req/jour) : https://www.alphavantage.co/support/#api-key
- **Marketaux** (100 req/jour) : https://www.marketaux.com/register
- **Finnhub** (60 req/min) : https://finnhub.io/register

#### 4.3 - Remplir config/secrets.yaml

Ouvre `config/secrets.yaml` avec Notepad ou VS Code, remplace les 3 placeholders (`TA_CLE_ICI`, `TON_TOKEN_ICI`, `TA_CLE_ICI`) par tes vraies cles.

### Etape 5 - Tests progressifs (dans l'ordre)

Lance ces commandes dans l'ordre. Verifie que chacune sort ce qui est attendu avant de passer a la suivante.

#### 5.1 - Voir les users
```bash
python cli.py users
```
**Doit sortir :**
```
Users disponibles :
  - demo
  - hajer (defaut)
```

#### 5.2 - Screening halal (sans Claude, sans API)
```bash
python cli.py check AAPL
python cli.py check JPM
```
- AAPL doit sortir `"halal": true`
- JPM doit sortir `"halal": false, "raison": "banque conventionnelle"`

#### 5.3 - Portefeuille d'un user
```bash
python cli.py --user hajer portefeuille
```
Doit afficher les positions avec P&L, poids, alertes.

#### 5.4 - PDF direct sans Claude
```bash
python cli.py --user hajer pdf
```
Doit sortir : `PDF genere : users/hajer/reports/rapport_direct_YYYY-MM-DD_HHMM.pdf`

Ouvre le PDF pour verifier qu'il est joli.

#### 5.5 - News multi-sources (necessite cles API remplies)
```bash
python cli.py news AAPL
```
Doit sortir la liste des news agregees. Verifie "Sources configurees : X/3" (idealement 3).

#### 5.6 - LE VRAI TRUC : Rapport Claude complet
```bash
python cli.py --user hajer rapport
```
**Prend 1-2 min.** Claude appelle les tools en boucle, redige 11 sections, sauve :
- markdown : `users/hajer/reports/rapport_YYYY-MM-DD_HHMM.md`
- PDF : `users/hajer/reports/rapport_claude_YYYY-MM-DD_HHMM.pdf`
- SQLite : entree dans `memory/agent_invest.sqlite`

#### 5.7 - Verifier la memoire
```bash
python cli.py historique
python cli.py recos
```
Tu dois voir le rapport que tu viens de generer + les recos extraites.

#### 5.8 - Marquer une reco executee (quand tu l'as vraiment fait dans IBKR)
```bash
python cli.py marquer-reco 1 executed
python cli.py calibration
```

### Etape 6 (Optionnel) - Utiliser un 2eme user

```bash
# Windows
mkdir users\marie
mkdir users\marie\reports
copy users\hajer\strategie.yaml users\marie\strategie.yaml
copy users\hajer\portefeuille.csv users\marie\portefeuille.csv

# Linux/WSL/Mac
mkdir -p users/marie/reports
cp users/hajer/strategie.yaml users/marie/strategie.yaml
cp users/hajer/portefeuille.csv users/marie/portefeuille.csv
```

Edite `users/marie/strategie.yaml` et `users/marie/portefeuille.csv` avec ses vraies donnees.

Puis :
```bash
python cli.py users                          # doit voir marie maintenant
python cli.py --user marie portefeuille
python cli.py --user marie rapport
```

---

## B. Test sur Google Colab (partiel, sans Claude)

Utilite : valider yfinance + calculs + PDF + memoire SQLite. **Le rapport complet Claude ne marche PAS sur Colab facilement** (necessite `claude login`).

### Prerequis Colab

- Compte Google gratuit
- URL de ton Colab existant : https://colab.research.google.com

### Cellule 1 - Cloner + installer (premiere fois seulement)

```
!git clone https://github.com/hajerbensalem2016/agent-invest.git
%cd agent-invest
!pip install -r requirements.txt -q
```

Si tu as deja clone dans une session precedente, remplace par :
```
!cd agent-invest && git pull
```

### Cellule 2 - Users disponibles
```
!cd agent-invest && python cli.py users
```

### Cellule 3 - Screening halal (sans Claude, sans API)
```
!cd agent-invest && python cli.py check AAPL
```
```
!cd agent-invest && python cli.py check JPM
```

### Cellule 4 - Portefeuille par user
```
!cd agent-invest && python cli.py --user hajer portefeuille
```
Tu vois les 6 positions avec P&L, alertes, ecart alloc.

### Cellule 5 - PDF direct
```
!cd agent-invest && python cli.py --user hajer pdf
```

### Cellule 6 - Telecharger le PDF sur ton ordi
```
from google.colab import files
import glob
pdf = sorted(glob.glob('agent-invest/users/hajer/reports/*.pdf'))[-1]
files.download(pdf)
```

### Cellule 7 (optionnel) - Cles API news dans Colab

Pour tester `python cli.py news AAPL` sur Colab, ecris tes cles :

```
%%writefile agent-invest/config/secrets.yaml
alpha_vantage_api_key: TA_CLE_ICI
marketaux_api_token: TON_TOKEN_ICI
finnhub_api_key: TA_CLE_ICI
```

**Remplace les valeurs par tes vraies cles avant de lancer**, puis :
```
!cd agent-invest && python cli.py news AAPL
```

### Cellule 8 - Commandes memoire (vides, normal si pas de rapport genere)
```
!cd agent-invest && python cli.py historique
!cd agent-invest && python cli.py calibration
```

---

## Problemes connus & solutions

### yfinance echoue avec "429 Too Many Requests" ou SSL error
- **Sur ton PC boulot avec Zscaler** : yfinance ne marche pas (bloque par le proxy)
  - Solution : utiliser Colab ou ton PC perso
- **Sur Colab ou PC perso** : yfinance marche
  - Si probleme temporaire : `pip install "yfinance==0.2.40"` (downgrade)

### `python -m venv` echoue avec "ensurepip is not available" (WSL/Ubuntu)
```bash
apt install python3.10-venv -y
```

Si apt echoue (Zscaler) :
```bash
curl -sS -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
python3 /tmp/get-pip.py
python3 -m pip install -r requirements.txt
```

### News APIs renvoient rien
- Verifie que `config/secrets.yaml` existe et contient tes vraies cles
- Verifie que t'as pas depasse la limite quotidienne (25/j Alpha Vantage)
- Test individuel : regarde "Sources configurees : X/3" dans la sortie

### Claude Agent SDK ne trouve pas l'auth
Sur ton PC perso, assure-toi que :
- `claude login` a ete fait avec ton compte Claude Max
- La session est active : lance juste `claude` dans un terminal, ca doit s'ouvrir

### `python cli.py rapport` sur Colab plante
Normal - Claude Code n'est pas installe sur Colab facilement. **Utilise ton PC perso pour cette commande.**

Les autres commandes (`check`, `portefeuille`, `pdf`, `news`, `historique`) marchent sur Colab.

---

## Ordre de test recommande la 1ere fois

Sur ton PC perso :
1. Etapes 1 a 3 (install)
2. Etape 5.1 (users) - **doit passer**
3. Etape 5.2 (halal) - **doit passer** (sans yfinance)
4. Etape 5.3 (portefeuille) - **doit passer si yfinance marche**
5. Etape 5.4 (PDF direct) - **doit passer**
6. Etape 4 (cles API news) puis 5.5 (news) - optionnel
7. Etape 5.6 (rapport Claude) - LE vrai test complet

Si une etape plante, **colle-moi l'erreur** et on debug ensemble.
