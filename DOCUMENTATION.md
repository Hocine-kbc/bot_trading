# 📚 Documentation du Bot Trading Momentum

## 🎯 Vue d'ensemble

Ce bot de trading automatique analyse les actions américaines pour détecter des opportunités de momentum et exécute des trades avec une stratégie simple :
- **Take Profit** : +20% de gain
- **Stop Loss** : -5% de perte

---

## 📁 Structure du Projet

```
action_momentum/
├── scripts/           # Code Python du bot
├── data/              # Données (watchlists, positions)
├── filters/           # Filtres (blacklist)
├── logs/              # Fichiers de logs
├── venv/              # Environnement virtuel Python
├── .env               # Variables d'environnement (API keys)
├── requirements.txt   # Dépendances Python
└── README.md          # Documentation
```

---

## 🐍 Fichiers Python (scripts/)

### 🧠 Fichier Principal

| Fichier | Rôle |
|---------|------|
| **`bot.py`** | **CERVEAU DU BOT** - Orchestre tous les modules, exécute la stratégie complète |

---

### ⚙️ Configuration

| Fichier | Rôle |
|---------|------|
| **`config.py`** | Centralise TOUTES les constantes et paramètres du bot (lus depuis `.env`) |

**Paramètres importants :**
- Connexion IBKR (host, port, client ID)
- API Keys (Benzinga, Telegram)
- Limites de risque (stop-loss, take-profit)
- Horaires de trading
- Seuils des filtres

---

### 📊 Récupération des Données

| Fichier | Rôle |
|---------|------|
| **`stock_data.py`** | Récupère les données boursières via Interactive Brokers (IBKR) |

**Fonctionnalités :**
- Connexion/déconnexion à IBKR
- Prix en temps réel
- Données historiques (OHLCV = Open, High, Low, Close, Volume)
- Orderflow (bid/ask, pression acheteuse/vendeuse)

---

### 📋 Gestion des Listes

| Fichier | Rôle |
|---------|------|
| **`watchlist_manager.py`** | Gère les listes d'actions à surveiller |

**Listes gérées :**
- **Watchlist Core** : Leaders sectoriels (Apple, Microsoft, etc.)
- **Watchlist Secondary** : Opportunités momentum
- **Blacklist** : Actions à éviter

---

### 📰 Surveillance des News

| Fichier | Rôle |
|---------|------|
| **`news_monitor.py`** | Surveille les actualités financières via Benzinga API |

**Fonctionnalités :**
- Calendrier des earnings (résultats trimestriels)
- Détection de news négatives (procès, fraude, etc.)
- Suivi des upgrades/downgrades des analystes

---

### 📈 Analyse du Marché

| Fichier | Rôle |
|---------|------|
| **`market_indices.py`** | Analyse les indices majeurs (SPY, QQQ, VIX) |
| **`market_sectors.py`** | Analyse les secteurs via ETFs (XLK, XLF, etc.) |

**Indices surveillés :**
- **SPY** : S&P 500 (500 plus grandes entreprises US)
- **QQQ** : Nasdaq 100 (tech)
- **VIX** : Indice de volatilité ("indice de la peur")

**Secteurs analysés :**
- Technology (XLK)
- Healthcare (XLV)
- Financials (XLF)
- Energy (XLE)
- etc.

---

### 🔍 Filtres de Validation

| Fichier | Rôle |
|---------|------|
| **`filters.py`** | Regroupe TOUS les filtres de trading |
| **`filters_time.py`** | Filtres basés sur les horaires |

**9 Filtres appliqués :**
1. ✅ Watchlist (action dans la liste ?)
2. ✅ Horaires (heures de marché ?)
3. ✅ Earnings (pas d'annonce imminente ?)
4. ✅ Marché (indices favorables ?)
5. ✅ Secteur (secteur en hausse ?)
6. ✅ Action (pas de doji, volume OK ?)
7. ✅ News (pas de news négatives ?)
8. ✅ Downgrade (pas de downgrade récent ?)
9. ✅ Spread (spread acceptable ?)

---

### 🕯️ Analyse Technique

| Fichier | Rôle |
|---------|------|
| **`candlestick_patterns.py`** | Détecte les patterns de chandeliers japonais |
| **`breakout_detector.py`** | Détecte les cassures de résistance (breakouts) |

**Patterns haussiers détectés :**
- 🔨 Hammer (Marteau)
- 📈 Bullish Engulfing (Englobante haussière)
- ⚔️ Three White Soldiers (Trois soldats blancs)
- etc.

**Conditions breakout :**
- Prix casse la résistance
- Volume > 150% de la moyenne
- Orderflow haussier (pression acheteuse)

---

### 💰 Gestion du Risque

| Fichier | Rôle |
|---------|------|
| **`risk_manager.py`** | Gère les limites de risque et le suivi des positions |

**Limites appliquées :**
- Max 5 positions simultanées
- Perte journalière max : 2% du capital
- Perte hebdomadaire max : 6% du capital
- Taille position : 20% du capital

---

### 🛒 Exécution des Trades

| Fichier | Rôle |
|---------|------|
| **`trading_manager.py`** | Exécute les achats et ventes |

**Fonctionnalités :**
- Entrée en position (achat)
- Sortie de position (vente)
- Ordres bracket (entrée + SL + TP automatiques)
- Surveillance des positions ouvertes
- Sorties d'urgence (news négatives, etc.)

---

### 📱 Notifications

| Fichier | Rôle |
|---------|------|
| **`telegram_notifier.py`** | Envoie des notifications Telegram |

**Types de notifications :**
- 🟢 Achat effectué
- 🎯 Take Profit atteint
- 🛑 Stop Loss déclenché
- ⚠️ Sortie urgente
- ❌ Erreur
- 📊 Résumé journalier

---

### 📝 Logging

| Fichier | Rôle |
|---------|------|
| **`logger.py`** | Système de logging (fichiers + console) |

**Fichiers de logs créés :**
- `bot.log` : Log général
- `trades.log` : Historique des trades
- `errors.log` : Erreurs uniquement

---

### 🧪 Utilitaires

| Fichier | Rôle |
|---------|------|
| **`test_connections.py`** | Teste les connexions (IBKR, Telegram, Benzinga) |
| **`get_chat_id.py`** | Récupère votre Chat ID Telegram |
| **`analyze_performance.py`** | Analyse les performances passées |
| **`__init__.py`** | Fichier d'initialisation du package Python |

---

## 📂 Fichiers de Données (data/)

| Fichier | Rôle |
|---------|------|
| **`watchlist_core.json`** | Liste des leaders sectoriels |
| **`watchlist_secondary.json`** | Liste des opportunités momentum |
| **`positions.json`** | Positions ouvertes et historique |

---

## 🚫 Fichiers de Filtres (filters/)

| Fichier | Rôle |
|---------|------|
| **`blacklist_sectors.json`** | Secteurs et actions à éviter |

---

## 🔐 Configuration (.env)

```env
# Interactive Brokers
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# Benzinga API
BENZINGA_API_KEY=votre_clé

# Telegram
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id

# Trading
DRY_RUN_MODE=True
PAPER_TRADING_MODE=True
MAX_POSITIONS=5
STOP_LOSS_PCT=0.05
TAKE_PROFIT_PCT=0.20
```

---

## 🔄 Flux de Fonctionnement

```
┌─────────────────────────────────────────────────────────────┐
│                    BOT.PY (Orchestrateur)                   │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  STOCK_DATA.PY  │  │  FILTERS.PY     │  │ RISK_MANAGER.PY │
│  (Données IBKR) │  │  (Validation)   │  │ (Gestion risque)│
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         │           ┌───────┴───────┐            │
         │           │               │            │
         ▼           ▼               ▼            │
┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│ MARKET_     │ │ NEWS_       │ │ CANDLESTICK │   │
│ INDICES.PY  │ │ MONITOR.PY  │ │ PATTERNS.PY │   │
└─────────────┘ └─────────────┘ └─────────────┘   │
                                                  │
                              ┌───────────────────┘
                              ▼
                   ┌─────────────────────┐
                   │  TRADING_MANAGER.PY │
                   │  (Exécution trades) │
                   └─────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ TELEGRAM_NOTIFIER.PY│
                   │   (Notifications)   │
                   └─────────────────────┘
```

---

## 🚀 Comment Lancer le Bot

### Mode Test (un seul cycle)
```bash
cd /home/houhou/bot/action_momentum
source venv/bin/activate
python scripts/bot.py --scan-once
```

### Mode Normal (boucle continue)
```bash
cd /home/houhou/bot/action_momentum
source venv/bin/activate
python scripts/bot.py
```

### Tester les Connexions
```bash
python scripts/test_connections.py
```

### Tester Telegram
```bash
python scripts/telegram_notifier.py
```

---

## ⚠️ Points Importants

1. **Mode DRY RUN** : Par défaut, le bot simule les trades sans passer de vrais ordres.
   - Pour trader en réel, mettez `DRY_RUN_MODE=False` dans `.env`

2. **TWS/IB Gateway** : Doit être lancé et l'API activée avant de lancer le bot.

3. **Horaires** : Le bot ne trade que du lundi au vendredi, entre 10:15 et 16:00 (heure de New York).

4. **Fichier .env** : Ne jamais partager ce fichier (contient vos clés API) !

---

## 📞 Support

En cas de problème :
1. Vérifiez les logs dans le dossier `logs/`
2. Testez les connexions avec `test_connections.py`
3. Vérifiez que TWS/IB Gateway est lancé

---

*Documentation générée le 5 décembre 2025*

