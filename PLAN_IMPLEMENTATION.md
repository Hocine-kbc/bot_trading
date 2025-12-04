# 🎯 PLAN D'IMPLÉMENTATION - BOT ACTIONS US MOMENTUM

## 📊 OBJECTIFS
- **Gain cible** : +20%
- **Stop-loss** : -5%
- **Stratégie** : Momentum sur actions US avec filtres stricts

---

## ✅ PHASE 1 — Installation & Infrastructure

### 1.1 Configuration Environnement (✅ FAIT)
- [x] Ubuntu configuré
- [x] Python 3.12 + venv
- [x] Dépendances installées : ib_insync, pandas, numpy, telegram, requests
- [x] Structure dossiers : `/data`, `/filters`, `/logs`, `/scripts`

### 1.2 Configuration API (À FAIRE)
**Fichier à créer** : `.env`
```bash
# Interactive Brokers
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # 7497 = Paper Trading, 7496 = Live
IBKR_CLIENT_ID=1

# Benzinga Pro
BENZINGA_API_KEY=your_api_key_here

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 1.3 Tests Connexions (À FAIRE)
**Fichier à créer** : `scripts/test_connections.py`
- Test connexion IBKR (TWS ou IB Gateway)
- Test API Benzinga
- Test envoi message Telegram

---

## 📈 PHASE 2 — Surveillance Marché & Secteurs

### 2.1 Module Secteurs
**Fichier** : `scripts/market_sectors.py`

**ETFs à surveiller** :
- **XLK** - Technology
- **XLY** - Consumer Discretionary
- **XLE** - Energy
- **XLF** - Financials
- **XLV** - Health Care
- **XLI** - Industrials
- **XLP** - Consumer Staples
- **XLU** - Utilities
- **XLB** - Materials
- **XLRE** - Real Estate
- **XLC** - Communication Services

**Fonctions** :
```python
def get_sector_strength():
    # Retourne secteurs haussiers (>0.5% + volume élevé)
    pass

def is_sector_bullish(etf_symbol):
    # Vérifie si secteur est en momentum haussier
    pass
```

### 2.2 Module Indices & VIX
**Fichier** : `scripts/market_indices.py`

**Fonctions** :
```python
def get_spy_status():
    # Retourne tendance SPY (haussier/neutre/baissier)
    pass

def get_qqq_status():
    # Retourne tendance QQQ
    pass

def get_vix_level():
    # Retourne niveau VIX (calme < 20, nerveux 20-30, panique > 30)
    pass

def is_market_bullish():
    # Validation : SPY + QQQ haussiers + VIX < 25
    pass
```

### 2.3 Module News
**Fichier** : `scripts/news_monitor.py`

**Sources Benzinga** :
- Earnings (48h avant = interdiction)
- Downgrades/Upgrades
- FDA approvals
- SEC filings
- Macro news

**Fonctions** :
```python
def get_earnings_calendar():
    # Retourne prochains earnings par ticker
    pass

def has_earnings_soon(ticker, hours=48):
    # True si earnings dans les X heures
    pass

def get_breaking_news(ticker):
    # News des 30 dernières minutes
    pass

def is_negative_news(news):
    # Détecte news négatives (downgrade, FDA rejection, etc.)
    pass
```

### 2.4 Module Données Actions
**Fichier** : `scripts/stock_data.py`

**Fonctions** :
```python
def get_ohlcv(ticker, interval='5min', bars=100):
    # Retourne OHLCV via IBKR
    pass

def get_orderflow(ticker):
    # Retourne bid/ask, volume bid/ask, market orders
    pass

def get_realtime_bars(ticker):
    # Streaming temps réel
    pass
```

---

## 📋 PHASE 2.1 — Watchlist Professionnelle

### 2.1.1 Watchlist Core
**Fichier** : `data/watchlist_core.json`

**Leaders par secteur (20-30 actions)** :
```json
{
  "tech": ["AAPL", "MSFT", "NVDA", "AMD", "META", "GOOGL", "TSLA"],
  "consumer": ["AMZN", "NFLX", "HD", "NKE", "SBUX"],
  "healthcare": ["UNH", "JNJ", "PFE", "ABBV"],
  "energy": ["XOM", "CVX", "COP"],
  "industrials": ["BA", "CAT", "HON"],
  "materials": ["LIN", "APD"],
  "communication": ["DIS", "CMCSA", "T"],
  "updated": "2025-12-03"
}
```

### 2.1.2 Watchlist Secondary
**Fichier** : `data/watchlist_secondary.json`

**Opportunités momentum (30-50 actions)** :
- Mid-caps en forte croissance
- Actions avec actualité positive récente
- Breakouts techniques récents

**Mise à jour** : hebdomadaire

### 2.1.3 Règle d'Or
**❌ JAMAIS trader hors watchlist !**

**Fichier** : `scripts/watchlist_manager.py`
```python
def load_watchlist():
    # Charge core + secondary
    pass

def is_in_watchlist(ticker):
    # Validation stricte
    pass

def update_watchlist():
    # Mise à jour mensuelle watchlist core
    # Mise à jour hebdomadaire watchlist secondary
    pass
```

---

## 🚫 PHASE 2.2 — Blacklist Sectorielle

### 2.2.1 Secteurs Interdits
**Fichier** : `filters/blacklist_sectors.json`

```json
{
  "excluded_sectors": [
    "Banks",
    "Insurance",
    "Vaccines/Biotechs (specific)",
    "REITs",
    "Utilities"
  ],
  "excluded_tickers": [
    "JPM", "BAC", "WFC", "C", "GS", "MS",
    "BRK.B", "AIG", "MET", "PRU",
    "MRNA", "BNTX", "NVAX",
    "VNQ", "IYR"
  ],
  "reason": "Volatilité excessive ou secteurs défensifs non-momentum"
}
```

### 2.2.2 Filtre Blacklist
**Fichier** : `scripts/blacklist_filter.py`

```python
def is_blacklisted(ticker):
    # Vérifie si ticker est dans blacklist
    pass

def filter_watchlist():
    # Exclut tickers blacklistés de la watchlist
    pass
```

**⚠️ Priorité** : Blacklist s'applique **AVANT** tout autre filtre !

---

## 🔍 PHASE 3 — Filtres du Bot

### 3.1 Filtres Horaires
**Fichier** : `scripts/filters_time.py`

```python
def is_trading_hours():
    # True si 09h30 - 16h00 US Eastern Time
    pass

def is_excluded_time():
    # True si 09h30 - 10h15 US (volatilité ouverture)
    pass

def can_trade_now():
    # is_trading_hours() and not is_excluded_time()
    pass
```

### 3.2 Filtre Earnings
**Fichier** : `scripts/filters_earnings.py`

```python
def has_earnings_soon(ticker, hours=48):
    # True si earnings dans les 48h
    # Source : Benzinga API
    pass
```

### 3.3 Filtres Émotions Marché
**Fichier** : `scripts/filters_market.py`

**Conditions** :
- SPY : hausse > 0.3% sur 5min
- QQQ : hausse > 0.3% sur 5min
- VIX : < 25
- Macro news positive ou neutre (pas de crise)

```python
def check_market_emotion():
    # Retourne score 0-100
    # 0 = très baissier, 100 = très haussier
    pass

def is_market_favorable():
    # True si score > 60
    pass
```

### 3.4 Filtres Émotions Secteur
**Fichier** : `scripts/filters_sector.py`

**Conditions** :
- ETF sectoriel : hausse > 0.5%
- Volume ETF : > moyenne 20 jours

```python
def get_sector_emotion(ticker):
    # Identifie secteur de l'action
    # Vérifie ETF sectoriel
    pass

def is_sector_favorable(ticker):
    # True si secteur haussier
    pass
```

### 3.5 Filtres Émotions Action
**Fichier** : `scripts/filters_stock.py`

**Conditions interdites** :
- Doji (open ≈ close)
- Mèche haute > 50% range
- Volume < 50% moyenne

```python
def has_doji(candle):
    # body < 20% total range
    pass

def has_high_wick(candle):
    # upper_shadow > 50% total range
    pass

def is_stock_favorable(ticker):
    # Pas de doji, pas de mèche haute, volume OK
    pass
```

---

## 🕯️ PHASE 4 — Chandeliers (Steve Nison)

### 4.1 Patterns Haussiers Autorisés
**Fichier** : `scripts/candlestick_patterns.py`

**Patterns validés** :
1. **Hammer** (marteau)
   - Body en haut
   - Lower shadow ≥ 2x body
   - Upper shadow petite

2. **Inverted Hammer** (marteau inversé)
   - Body en bas
   - Upper shadow ≥ 2x body
   - Lower shadow petite

3. **Bullish Engulfing**
   - Chandelier vert englobe le rouge précédent

4. **Piercing Line**
   - Rouge puis vert qui clôture > 50% du rouge

5. **Three White Soldiers**
   - 3 chandeliers verts consécutifs croissants

```python
def detect_hammer(candle):
    pass

def detect_inverted_hammer(candle):
    pass

def detect_bullish_engulfing(prev, current):
    pass

def detect_piercing_line(prev, current):
    pass

def detect_three_white_soldiers(candles):
    pass

def detect_bullish_pattern(candles):
    # Retourne pattern détecté ou None
    pass
```

### 4.2 Patterns Baissiers Interdits
**Pas d'entrée si** :
- Shooting Star
- Hanging Man
- Doji
- Bearish Engulfing
- Evening Star

```python
def detect_bearish_pattern(candles):
    # Si pattern baissier détecté : interdiction trade
    pass
```

### 4.3 Validation Volume
**Règle** : Volume chandelier ≥ 120% moyenne 20 périodes

```python
def is_volume_valid(candle, avg_volume_20):
    return candle['volume'] >= avg_volume_20 * 1.2
```

---

## 📊 PHASE 4.1 — Breakout + Orderflow

### 4.1.1 Détection Breakout
**Fichier** : `scripts/breakout_detector.py`

**Conditions** :
- Prix clôture > résistance (high des 20 derniers chandeliers 5min)
- Volume ≥ 150% moyenne
- Chandelier vert (close > open)

```python
def detect_breakout(ticker):
    # Vérifie clôture, résistance, volume
    pass
```

### 4.1.2 Orderflow IBKR
**Fichier** : `scripts/orderflow_analyzer.py`

**Indicateurs** :
- Bid size vs Ask size (bid > ask = haussier)
- Market Buy > Market Sell
- Spread stable (< 0.1% prix)

```python
def get_orderflow_signal(ticker):
    # 1 = haussier, 0 = neutre, -1 = baissier
    pass

def is_orderflow_bullish(ticker):
    return get_orderflow_signal(ticker) == 1
```

---

## 🎯 PHASE 5 — Entrée & Gestion

### 5.1 Validation Entrée
**Fichier** : `scripts/entry_manager.py`

**Checklist complète** :
```python
def can_enter_trade(ticker):
    checks = {
        'in_watchlist': is_in_watchlist(ticker),
        'not_blacklisted': not is_blacklisted(ticker),
        'trading_hours': can_trade_now(),
        'no_earnings': not has_earnings_soon(ticker),
        'market_favorable': is_market_favorable(),
        'sector_favorable': is_sector_favorable(ticker),
        'stock_favorable': is_stock_favorable(ticker),
        'bullish_pattern': detect_bullish_pattern(ticker) is not None,
        'volume_valid': is_volume_valid(ticker),
        'breakout': detect_breakout(ticker),
        'orderflow_bullish': is_orderflow_bullish(ticker)
    }
    
    # Tous les checks doivent être True
    return all(checks.values()), checks
```

### 5.2 Exécution Ordre
```python
def enter_position(ticker, quantity):
    # 1. Calcul position size (max 20% capital par position)
    # 2. Ordre limit à ask + 0.02%
    # 3. Attente confirmation fill
    # 4. Log dans /logs/trades.json
    # 5. Notification Telegram
    pass
```

### 5.3 Stop-Loss Automatique
```python
def set_stop_loss(ticker, entry_price):
    stop_price = entry_price * 0.95  # -5%
    # Bracket order IBKR
    pass
```

### 5.4 Take-Profit
```python
def set_take_profit(ticker, entry_price):
    tp_price = entry_price * 1.20  # +20%
    # Bracket order IBKR
    pass
```

---

## 🛡️ PHASE 6 — Sécurité & Surveillance

### 6.1 Sortie Urgente
**Fichier** : `scripts/emergency_exit.py`

**Déclencheurs** :
- News négative (downgrade, FDA rejection)
- Spread > 0.5% (illiquidité)
- VIX +20% soudain
- SPY/QQQ chute > 1%

```python
def check_emergency_conditions(ticker):
    # Surveillance continue positions ouvertes
    pass

def emergency_exit(ticker):
    # Market order sortie immédiate
    # Notification Telegram urgence
    pass
```

### 6.2 Limites de Risque
**Fichier** : `scripts/risk_manager.py`

```python
def check_daily_loss_limit():
    # Max -2% capital / jour
    if loss_today > 0.02 * capital:
        stop_all_trading()
        notify_telegram("⛔ Limite perte journalière atteinte")

def check_weekly_loss_limit():
    # Max -6% capital / semaine
    if loss_week > 0.06 * capital:
        stop_all_trading()
        notify_telegram("⛔ Limite perte hebdomadaire atteinte")

def check_max_positions():
    # Max 5 positions simultanées
    return len(open_positions) < 5
```

---

## 📱 PHASE 7 — Telegram

### 7.1 Types d'Alertes
**Fichier** : `scripts/telegram_notifier.py`

```python
def notify_entry(ticker, price, quantity):
    msg = f"✅ ACHAT {ticker}\n"
    msg += f"Prix: ${price}\n"
    msg += f"Quantité: {quantity}\n"
    msg += f"SL: -5% | TP: +20%"
    send_telegram(msg)

def notify_take_profit(ticker, entry, exit, profit_pct):
    msg = f"🎯 TAKE PROFIT {ticker}\n"
    msg += f"Entrée: ${entry}\n"
    msg += f"Sortie: ${exit}\n"
    msg += f"Gain: +{profit_pct}%"
    send_telegram(msg)

def notify_stop_loss(ticker, entry, exit, loss_pct):
    msg = f"🛑 STOP LOSS {ticker}\n"
    msg += f"Entrée: ${entry}\n"
    msg += f"Sortie: ${exit}\n"
    msg += f"Perte: {loss_pct}%"
    send_telegram(msg)

def notify_emergency(ticker, reason):
    msg = f"⚠️ SORTIE URGENCE {ticker}\n"
    msg += f"Raison: {reason}"
    send_telegram(msg)

def notify_error(error_msg):
    msg = f"❌ ERREUR\n{error_msg}"
    send_telegram(msg)

def notify_pause(reason):
    msg = f"⏸️ PAUSE TRADING\n{reason}"
    send_telegram(msg)
```

### 7.2 Anti-Spam
```python
# Cooldown 5 minutes par ticker
last_notification = {}

def can_send_notification(ticker):
    if ticker in last_notification:
        elapsed = time.time() - last_notification[ticker]
        return elapsed > 300  # 5 minutes
    return True
```

---

## 🧪 PHASE 8 — Tests

### 8.1 Phase à Blanc (2 semaines)
**Objectifs** :
- Vérifier tous les filtres fonctionnent
- Pas d'ordres envoyés
- Logs des opportunités détectées
- Statistiques : combien de signaux/jour, taux faux positifs

**Fichier** : `scripts/dry_run.py`
```python
DRY_RUN_MODE = True  # Pas d'ordres réels

def simulate_trade(ticker):
    # Log opportunité sans trader
    pass
```

### 8.2 Paper Trading (4-12 semaines)
**Objectifs** :
- Trading réel sur compte démo IBKR
- Validation ratio gain/perte
- Validation taille positions
- Ajustement paramètres

**Configuration** :
```python
IBKR_PORT = 7497  # Paper Trading
PAPER_TRADING_MODE = True
```

**Métriques à suivre** :
- Win rate (objectif > 55%)
- Ratio moyen gain/perte (objectif > 2.5)
- Drawdown max (objectif < 10%)
- Nombre trades/semaine

### 8.3 Réel Faible Taille (4 semaines)
**Après validation paper trading** :
- Taille 10% position normale
- Maximum 2 positions simultanées
- Stop immédiat si perte > -1% capital

---

## 🔧 PHASE 9 — Optimisation

### 9.1 Ajustement Filtres Nison
**Toutes les 2 semaines** :
- Analyser patterns gagnants vs perdants
- Ajuster seuils mèches, volume
- Tester nouveaux patterns

### 9.2 Ajustement Filtres Émotions
**Toutes les 2 semaines** :
- Analyser corrélation VIX/SPY/QQQ avec réussite trades
- Ajuster seuils si nécessaire

### 9.3 Mise à Jour Watchlist
**Mensuel (Core) + Hebdomadaire (Secondary)** :
```python
def update_watchlist_core():
    # Analyse leaders sectoriels
    # Suppression actions faibles
    # Ajout nouveaux leaders
    pass

def update_watchlist_secondary():
    # Scan momentum marché
    # Breakouts récents
    # News positives
    pass
```

---

## 📂 STRUCTURE FINALE DES FICHIERS

```
/bot/action_momentum/
│
├── .env                          # API keys
├── PLAN_IMPLEMENTATION.md        # Ce document
│
├── /data/
│   ├── watchlist_core.json       # Leaders sectoriels
│   ├── watchlist_secondary.json  # Opportunités
│   └── positions.json            # Positions ouvertes
│
├── /filters/
│   └── blacklist_sectors.json    # Secteurs interdits
│
├── /logs/
│   ├── trades.json               # Historique trades
│   ├── signals.json              # Signaux détectés
│   └── errors.log                # Erreurs
│
├── /scripts/
│   ├── bot.py                    # Main bot (orchestration)
│   ├── test_connections.py       # Tests API
│   │
│   ├── market_sectors.py         # Surveillance secteurs
│   ├── market_indices.py         # SPY, QQQ, VIX
│   ├── news_monitor.py           # Benzinga news
│   ├── stock_data.py             # Données OHLCV
│   │
│   ├── watchlist_manager.py      # Gestion watchlists
│   ├── blacklist_filter.py       # Filtrage blacklist
│   │
│   ├── filters_time.py           # Filtres horaires
│   ├── filters_earnings.py       # Filtres earnings
│   ├── filters_market.py         # Émotions marché
│   ├── filters_sector.py         # Émotions secteur
│   ├── filters_stock.py          # Émotions action
│   │
│   ├── candlestick_patterns.py   # Patterns Steve Nison
│   ├── breakout_detector.py      # Détection breakouts
│   ├── orderflow_analyzer.py     # Orderflow IBKR
│   │
│   ├── entry_manager.py          # Gestion entrées
│   ├── exit_manager.py           # Gestion sorties
│   ├── risk_manager.py           # Gestion risque
│   ├── emergency_exit.py         # Sorties urgentes
│   │
│   ├── telegram_notifier.py      # Notifications Telegram
│   │
│   ├── dry_run.py                # Mode à blanc
│   └── optimizer.py              # Optimisation paramètres
│
└── /venv/                        # Virtual environment
```

---

## 🚀 PROCHAINES ÉTAPES IMMÉDIATES

### ✅ Étape 1 : Configuration .env
Créer fichier avec vos API keys

### ✅ Étape 2 : Remplir Watchlists
- watchlist_core.json : 20-30 leaders
- watchlist_secondary.json : 30-50 opportunités

### ✅ Étape 3 : Corriger Blacklist
Renommer `backlist_sectors.json` → `blacklist_sectors.json`

### ✅ Étape 4 : Tests Connexions
Lancer `test_connections.py`

### ✅ Étape 5 : Développer Modules
Un par un, en testant chacun

---

## 📞 SUPPORT

**Questions fréquentes** :
- Benzinga API : https://www.benzinga.com/apis
- IBKR API : https://ib-insync.readthedocs.io/
- Telegram Bot : https://core.telegram.org/bots

**Communauté** :
- ib_insync Discord
- QuantConnect forums

