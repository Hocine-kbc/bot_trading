# 📚 EXPLICATION COMPLÈTE DU CODE - BOT MOMENTUM

Ce document explique **chaque fichier et chaque concept** du projet.

---

## 📁 STRUCTURE DU PROJET

```
/bot/action_momentum/
│
├── scripts/                    # 📂 Tous les fichiers Python
│   ├── bot.py                 # 🎯 FICHIER PRINCIPAL (cerveau du bot)
│   ├── config.py              # ⚙️ Configuration (variables globales)
│   ├── test_connections.py    # 🧪 Test connexions API
│   │
│   ├── stock_data.py          # 📊 Données IBKR (prix, volumes, orderflow)
│   ├── watchlist_manager.py   # 📋 Gestion watchlists
│   ├── news_monitor.py        # 📰 Surveillance news Benzinga
│   ├── market_indices.py      # 📈 Analyse SPY/QQQ/VIX
│   ├── market_sectors.py      # 🏭 Analyse secteurs ETF
│   │
│   ├── filters_time.py        # ⏰ Filtres horaires
│   ├── filters.py             # 🔍 TOUS les filtres combinés
│   │
│   ├── candlestick_patterns.py # 🕯️ Patterns chandeliers
│   ├── breakout_detector.py   # 🚀 Détection breakouts
│   │
│   ├── risk_manager.py        # 🛡️ Gestion risque
│   ├── trading_manager.py     # 💰 Exécution trades
│   └── telegram_notifier.py   # 📱 Notifications
│
├── data/                       # 💾 Données JSON
│   ├── watchlist_core.json    # Leaders sectoriels
│   ├── watchlist_secondary.json # Opportunités
│   └── positions.json         # Positions ouvertes
│
├── filters/                    # 🚫 Exclusions
│   └── blacklist_sectors.json # Secteurs/actions interdits
│
├── logs/                       # 📝 Logs générés
│   ├── bot.log               # Logs du bot
│   └── errors.log            # Erreurs
│
├── .env                        # 🔑 Clés API (À CRÉER)
├── requirements.txt            # 📦 Dépendances Python
└── README.md                   # 📖 Documentation
```

---

## 🎯 FICHIER PRINCIPAL : `bot.py`

### Rôle
C'est le **cerveau du bot**. Il orchestre tous les modules.

### Structure

```python
class MomentumBot:
    def __init__():         # Initialise tous les modules
    def connect():          # Se connecte à IBKR
    def disconnect():       # Se déconnecte
    def scan_ticker():      # Analyse UNE action (11 filtres)
    def scan_watchlist():   # Analyse TOUTES les actions
    def execute_signal():   # Achète une action
    def run_cycle():        # Un cycle complet (5 min)
    def run():              # Boucle infinie
```

### Flux d'exécution

```
1. __init__() → Charge tous les modules
2. run() → Démarre boucle infinie
   ↓
3. run_cycle() → Exécuté toutes les 5 min
   ├─ Vérifier heures trading
   ├─ Vérifier marché haussier
   ├─ Vérifier limites risque
   ├─ Surveiller positions ouvertes
   └─ Scanner watchlist
      ↓
4. scan_watchlist() → Boucle sur tous tickers
   ↓
5. scan_ticker() → Pour chaque ticker
   ├─ Filtres de base (11 conditions)
   ├─ Détection pattern
   ├─ Validation volume
   └─ Détection breakout + orderflow
      ↓
6. execute_signal() → Si signal valide
   └─ Achète avec SL/TP automatiques
```

**Voir `bot_commented.py` pour version ligne par ligne commentée !**

---

## ⚙️ FICHIER : `config.py`

### Rôle
Contient **toutes les variables de configuration** utilisées par les autres modules.

### Sections

#### 1. **Variables environnement (.env)**
```python
IBKR_HOST = '127.0.0.1'     # IP serveur IBKR
IBKR_PORT = 7497            # Port (7497=paper, 7496=live)
TELEGRAM_BOT_TOKEN = '...'  # Token bot Telegram
DRY_RUN_MODE = True         # True = simulation
```

#### 2. **Paramètres trading**
```python
MAX_POSITIONS = 5           # Max 5 positions simultanées
DAILY_LOSS_LIMIT = 0.02     # Max -2% capital/jour
STOP_LOSS_PCT = 0.05        # Stop-loss à -5%
TAKE_PROFIT_PCT = 0.20      # Take-profit à +20%
```

#### 3. **ETFs sectoriels**
```python
SECTOR_ETFS = {
    'technology': 'XLK',
    'energy': 'XLE',
    ...
}
```

#### 4. **Seuils filtres**
```python
VIX_MAX_LEVEL = 25                    # VIX doit être < 25
MIN_VOLUME_MULTIPLIER = 1.2           # Volume >= 120% moyenne
BREAKOUT_VOLUME_MULTIPLIER = 1.5      # Breakout >= 150% volume
```

#### 5. **Mots-clés news négatives**
```python
NEGATIVE_KEYWORDS = [
    'downgrade',
    'lawsuit',
    'bankruptcy',
    ...
]
```

### Pourquoi ce fichier ?
**Centraliser la config** → Si on veut changer un seuil, on modifie UN SEUL fichier !

---

## 📊 MODULE : `stock_data.py`

### Rôle
**Interface avec Interactive Brokers** pour récupérer données prix/volumes.

### Classe principale : `StockDataProvider`

#### Méthodes importantes

```python
connect()
# Se connecte à TWS/IB Gateway
# Établit connexion socket TCP/IP

get_contract(ticker)
# Récupère contrat IBKR pour un ticker
# Ex: Stock('AAPL', 'SMART', 'USD')

get_current_price(ticker)
# Prix temps réel : last, bid, ask, volume
# Retourne dict avec toutes les infos

get_ohlcv(ticker, interval, duration)
# Données historiques OHLCV
# interval: '5 mins', '1 hour', '1 day'
# duration: '1 D', '1 W', '1 M'
# Retourne DataFrame pandas

get_orderflow(ticker)
# Orderflow : bid/ask sizes, spread, pression
# Calcule bid_pressure = bid_size / (bid + ask)
# Signal haussier si bid_pressure > 55%

get_volume_profile(ticker, periods=20)
# Analyse volume vs moyenne
# Retourne ratio volume actuel / moyenne
```

### Exemple utilisation

```python
provider = StockDataProvider()
provider.connect()

# Prix actuel
price = provider.get_current_price('AAPL')
print(f"AAPL: ${price['last']}")

# Données 5min
df = provider.get_ohlcv('AAPL', '5 mins', '1 D')
print(df.tail())  # 5 dernières bougies

# Orderflow
flow = provider.get_orderflow('AAPL')
print(f"Bid pressure: {flow['bid_pressure']}%")

provider.disconnect()
```

---

## 📋 MODULE : `watchlist_manager.py`

### Rôle
Gère les **listes d'actions autorisées/interdites**.

### Concept
Le bot **NE PEUT TRADER** que les actions dans watchlist ET pas dans blacklist.

### Fichiers gérés

1. **`watchlist_core.json`** : Leaders sectoriels (50 actions)
   - Actions grandes caps
   - Liquidité élevée
   - Mise à jour mensuelle

2. **`watchlist_secondary.json`** : Opportunités momentum
   - Mid-caps en breakout
   - Nouvelles tendances
   - Mise à jour hebdomadaire

3. **`blacklist_sectors.json`** : Interdictions
   - Secteurs exclus (banques, assurances)
   - Actions spécifiques (MRNA, JPM...)
   - Jamais tradées !

### Classe : `WatchlistManager`

#### Méthodes importantes

```python
load_all()
# Charge watchlists + blacklist
# Retire automatiquement tickers blacklistés

is_in_watchlist(ticker)
# True si ticker autorisé
# False sinon → ne PAS trader

is_blacklisted(ticker)
# True si ticker interdit
# False sinon

can_trade(ticker)
# Combine is_in_watchlist() + not is_blacklisted()
# Retourne (True/False, raison)

get_all_tickers()
# Retourne liste complète (core + secondary)
# Sans les blacklistés

add_to_secondary(ticker, category)
# Ajoute ticker à watchlist secondary
# Sauvegarde dans JSON

remove_from_secondary(ticker)
# Retire ticker de watchlist secondary
```

### Règles importantes

1. ✅ **Filtre appliqué EN PREMIER** (avant tous autres filtres)
2. ❌ **Jamais trader hors watchlist**
3. ❌ **Jamais trader blacklisté** (même si dans watchlist)
4. 🔄 **Mettre à jour régulièrement**

---

## 📰 MODULE : `news_monitor.py`

### Rôle
Surveille **actualités via API Benzinga Pro** pour détecter :
- Earnings à venir (dans 48h)
- Downgrades analystes
- News négatives (lawsuits, recalls)

### Classe : `NewsMonitor`

#### Méthodes importantes

```python
get_earnings_calendar(days_ahead=2)
# Récupère earnings prévus dans X jours
# Source : Benzinga calendar API
# Retourne liste earnings

has_earnings_soon(ticker, hours=48)
# True si ticker a earnings dans 48h
# False sinon
# Retourne (bool, earnings_info)

get_breaking_news(ticker, minutes=30)
# News des 30 dernières minutes
# Filtré par ticker (ou toutes news)
# Retourne liste articles

is_negative_news(news)
# Analyse titre + corps article
# Cherche mots-clés négatifs (config.NEGATIVE_KEYWORDS)
# Retourne True si news négative

has_negative_news(ticker, minutes=30)
# Combine get_breaking_news() + is_negative_news()
# Retourne (bool, liste_news_negatives)

get_ratings_changes(ticker, days=1)
# Récupère changements ratings (upgrades/downgrades)
# Source : Benzinga ratings API
# Retourne liste ratings

has_recent_downgrade(ticker, days=1)
# True si downgrade dans dernier jour
# Retourne (bool, liste_downgrades)
```

### Utilisation dans filtres

```python
# Filtre earnings (OBLIGATOIRE)
has_earnings, info = news_monitor.has_earnings_soon('AAPL', 48)
if has_earnings:
    return False, "Earnings dans 48h"

# Sortie urgente
has_negative, news = news_monitor.has_negative_news('AAPL', 10)
if has_negative:
    # Vendre immédiatement !
    trading_manager.exit_position('AAPL', 'News négative')
```

### Note importante
**Benzinga Pro coûte cher** (~200-500$/mois). Pour débuter :
- Commencer sans Benzinga
- Filtre earnings sera désactivé
- Reste 10 autres filtres actifs

---

## 📈 MODULE : `market_indices.py`

### Rôle
Analyse **état du marché** via SPY, QQQ, VIX.

### Concept
**On ne trade QUE si marché est haussier !**

### Classe : `MarketIndicesAnalyzer`

#### Méthodes

```python
get_spy_status()
# Analyse tendance SPY (S&P 500)
# Calcule variation 5min
# Compare à SMA 20 périodes
# Retourne dict avec:
#   - price: prix actuel
#   - change_pct: variation %
#   - is_bullish: True si >= +0.3%

get_qqq_status()
# Idem pour QQQ (Nasdaq 100)

get_vix_level()
# Niveau VIX (volatilité)
# Interprétation:
#   < 15: très calme 🟢
#   15-20: calme 🟢
#   20-25: normal 🟡
#   25-30: nerveux 🟠
#   > 30: panique 🔴
# Retourne is_favorable = True si < 25

is_market_bullish()
# Validation COMPLÈTE:
# ✅ SPY haussier (>= 0.3%)
# ✅ QQQ haussier (>= 0.3%)
# ✅ VIX < 25
# Retourne (bool, details)

get_market_score()
# Score 0-100
# 100 = très haussier
# 0 = très baissier
# Pondération SPY + QQQ + VIX
```

### Logique filtre marché

```python
is_bullish, details = market_analyzer.is_market_bullish()

if not is_bullish:
    # Ne PAS trader !
    # Conditions marché défavorables
    return False
```

### Pourquoi important ?
**80% réussite trades** dépend de **direction marché** !
- Marché baissier → Même bon signal échoue
- Marché haussier → Bon signal amplifié

---

## 🏭 MODULE : `market_sectors.py`

### Rôle
Analyse **force des secteurs** via ETFs sectoriels.

### Concept
Trader action dans **secteur haussier** augmente chances de réussite.

### ETFs surveillés (11 secteurs)
```python
XLK - Technology
XLY - Consumer Discretionary
XLE - Energy
XLF - Financials  (blacklisté)
XLV - Health Care
XLI - Industrials
XLP - Consumer Staples
XLU - Utilities  (blacklisté)
XLB - Materials
XLRE - Real Estate  (blacklisté)
XLC - Communication
```

### Classe : `MarketSectorsAnalyzer`

#### Méthodes

```python
get_sector_status(etf_symbol, sector_name)
# Analyse UN secteur
# Conditions haussier:
#   - Variation >= +0.5%
#   - Volume >= 120% moyenne
# Retourne dict avec tous détails

get_all_sectors_status()
# Analyse LES 11 secteurs
# Retourne dict par secteur

get_bullish_sectors()
# Retourne liste secteurs haussiers
# Triée par variation décroissante

is_sector_bullish(etf_symbol)
# True/False pour un secteur

get_sector_for_stock(ticker)
# Identifie secteur d'une action
# Mapping manuel (peut être amélioré)
# Retourne nom secteur

is_stock_sector_favorable(ticker)
# Vérifie si secteur de l'action est haussier
# Retourne (bool, sector_name)
```

### Utilisation dans filtres

```python
is_favorable, sector = sector_analyzer.is_stock_sector_favorable('AAPL')

if not is_favorable:
    # Secteur pas haussier → Ne pas trader
    return False, f"Secteur {sector} non favorable"
```

---

## 🔍 MODULES FILTRES

### `filters_time.py` - Filtres horaires

#### Règles
1. **Trading uniquement** : Lundi-Vendredi
2. **Heures** : 09h30 - 16h00 ET (Eastern Time)
3. **EXCLUSION** : 09h30 - 10h15 (volatilité ouverture)

#### Méthodes

```python
is_trading_hours()
# True si dans heures marché
# False si weekend/nuit

is_excluded_time()
# True si 09h30-10h15 (période volatile)
# False sinon

can_trade_now()
# Combine les deux
# True SEULEMENT si 10h15-16h00, Lun-Ven
```

### `filters.py` - TOUS les filtres combinés

#### Classe : `TradingFilters`

C'est le **module le plus important** ! Il regroupe **11 filtres** :

```python
1. filter_watchlist(ticker)
   # Ticker dans watchlist ET pas blacklisté

2. filter_time()
   # Heures trading (10h15-16h00)

3. filter_earnings(ticker)
   # Pas d'earnings dans 48h

4. filter_market_emotion()
   # SPY + QQQ haussiers, VIX < 25

5. filter_sector_emotion(ticker)
   # Secteur de l'action haussier

6. filter_stock_emotion(ticker)
   # Pas de doji, pas mèche haute, volume OK

7. filter_negative_news(ticker)
   # Pas de news négatives 30min

8. filter_downgrade(ticker)
   # Pas de downgrade récent

9. filter_spread(ticker)
   # Spread bid-ask < 0.5%

10-11. Pattern + Breakout (dans bot.py)
```

#### Méthode principale

```python
validate_all_filters(ticker)
# Exécute LES 9 premiers filtres
# Retourne (all_passed, results_dict)
# 
# all_passed = True SEULEMENT si TOUS passent
# results_dict = détails chaque filtre
```

### Pourquoi 11 filtres ?

**Qualité > Quantité**
- 11 filtres stricts = Peu de signaux MAIS haute qualité
- Mieux avoir 1 bon signal/jour que 10 mauvais

---

## 🕯️ MODULE : `candlestick_patterns.py`

### Rôle
Détecte **patterns de chandeliers japonais** (méthode Steve Nison).

### Patterns haussiers (autorisés)

```python
1. HAMMER (Marteau)
   - Corps en haut
   - Mèche basse >= 2x corps
   - Signale retournement haussier

2. INVERTED_HAMMER (Marteau inversé)
   - Corps en bas
   - Mèche haute >= 2x corps
   - Signale retournement haussier

3. BULLISH_ENGULFING (Englobante haussière)
   - Rouge puis vert
   - Vert englobe totalement rouge
   - Fort signal haussier

4. PIERCING_LINE (Ligne perforante)
   - Rouge puis vert
   - Vert clôture > 50% du rouge
   - Signal haussier

5. THREE_WHITE_SOLDIERS (3 soldats blancs)
   - 3 chandeliers verts consécutifs
   - Clôtures croissantes
   - Très fort signal haussier
```

### Patterns baissiers (interdits)

```python
DOJI
# Open ≈ Close (indécision)
# Signal de faiblesse

SHOOTING_STAR
# Mèche haute, corps bas
# Signal de retournement baissier

HANGING_MAN
# Mèche basse, corps haut
# Signal de faiblesse

BEARISH_ENGULFING
# Vert puis rouge qui englobe
# Signal baissier fort

EVENING_STAR
# Pattern 3 chandeliers baissier
```

### Classe : `CandlestickPatterns`

#### Méthodes détection

```python
detect_hammer(candle)
detect_inverted_hammer(candle)
detect_bullish_engulfing(prev, current)
detect_piercing_line(prev, current)
detect_three_white_soldiers(candles)

# Patterns baissiers
detect_doji(candle)
detect_shooting_star(candle)
detect_hanging_man(candle)
detect_bearish_engulfing(prev, current)
```

#### Méthodes principales

```python
detect_bullish_pattern(df)
# Cherche pattern haussier dans données
# Retourne {'pattern': nom, 'confidence': 70-90}
# Ou None si aucun pattern

detect_bearish_pattern(df)
# Cherche pattern baissier
# Si détecté → NE PAS trader !

validate_volume(candle, avg_volume)
# Vérifie volume >= 120% moyenne
# Pattern VALIDE seulement si volume OK
```

### Utilisation

```python
df = data_provider.get_ohlcv('AAPL', '5 mins', '1 D')

pattern = patterns.detect_bullish_pattern(df)
if pattern:
    print(f"Pattern: {pattern['pattern']}")  # Ex: HAMMER
    print(f"Confiance: {pattern['confidence']}%")  # Ex: 75%
```

---

## 🚀 MODULE : `breakout_detector.py`

### Rôle
Détecte **cassures de résistance** avec validation volume + orderflow.

### Concept breakout

```
Prix
 |
 |     ★ <- Breakout ! (cassure résistance)
 |  --------- Résistance (high des 20 dernières bougies)
 |    /\
 |   /  \
 |  /    \
```

### Conditions breakout valide

```python
1. Prix clôture > résistance (high max 20 périodes)
2. Chandelier VERT (close > open)
3. Volume >= 150% moyenne
4. Orderflow haussier (bid > ask)
5. Spread acceptable (< 0.5%)
```

### Classe : `BreakoutDetector`

#### Méthodes

```python
detect_breakout(ticker, periods=20)
# Détecte breakout technique
# Retourne (bool, details_dict)

is_orderflow_bullish(ticker)
# Valide orderflow IBKR
# bid_pressure > 55%
# spread < 0.5%
# Retourne (bool, orderflow_dict)

validate_breakout_with_orderflow(ticker)
# Combine les 2 validations
# Breakout ET orderflow doivent être OK
# Retourne (bool, combined_details)

get_support_level(ticker, periods=20)
# Calcule support (low min)

get_resistance_level(ticker, periods=20)
# Calcule résistance (high max)
```

### Utilisation

```python
is_valid, details = breakout_detector.validate_breakout_with_orderflow('AAPL')

if is_valid:
    # Breakout validé + orderflow haussier
    # Signal très fort ! ✅
    print(details['breakout']['breakout_pct'])  # % cassure
    print(details['orderflow']['bid_pressure'])  # Pression achat
```

---

## 🛡️ MODULE : `risk_manager.py`

### Rôle
**Gère le risque** et **limite les pertes**.

### Limites configurées

```python
MAX_POSITIONS = 5          # Max 5 positions simultanées
DAILY_LOSS_LIMIT = 0.02    # Max -2% capital/jour
WEEKLY_LOSS_LIMIT = 0.06   # Max -6% capital/semaine
POSITION_SIZE_PCT = 0.20   # 20% capital par position
```

### Classe : `RiskManager`

#### Méthodes positions

```python
get_open_positions()
# Retourne liste positions ouvertes

get_position(ticker)
# Récupère position spécifique

can_open_position()
# True si < 5 positions
# False sinon

calculate_position_size(price)
# Calcule quantité actions à acheter
# Formule: (capital * 0.20) / price
# Retourne nombre actions
```

#### Méthodes PnL

```python
get_daily_pnl()
# Calcule profit/perte du jour
# Somme PnL positions fermées aujourd'hui

get_weekly_pnl()
# Calcule PnL de la semaine

check_daily_loss_limit()
# Vérifie si perte jour > -2% capital
# Retourne (bool, raison)

check_weekly_loss_limit()
# Vérifie si perte semaine > -6% capital

can_trade()
# Validation COMPLÈTE:
# - Positions < 5
# - Perte jour < limite
# - Perte semaine < limite
# Retourne (bool, raison)
```

#### Méthodes gestion positions

```python
add_position(ticker, entry_price, quantity, sl, tp)
# Ajoute nouvelle position
# Sauvegarde dans positions.json

close_position(ticker, exit_price, reason)
# Ferme position
# Calcule PnL
# Met à jour statistiques
# Retourne closed_position dict

get_statistics()
# Retourne stats complètes:
# - Total trades
# - Win rate
# - Average gain/loss
# - Profit factor
# - Total PnL
```

### Fichier : `positions.json`

```json
{
  "open_positions": [
    {
      "ticker": "AAPL",
      "entry_price": 150.50,
      "quantity": 13,
      "stop_loss": 142.98,
      "take_profit": 180.60,
      "entry_time": "2025-12-03T14:30:00",
      "value": 1956.50
    }
  ],
  "closed_positions": [],
  "statistics": {
    "total_trades": 0,
    "win_rate": 0,
    "total_pnl": 0
  }
}
```

---

## 💰 MODULE : `trading_manager.py`

### Rôle
**Exécute les trades** sur Interactive Brokers.

### Classe : `TradingManager`

#### Méthodes principales

```python
enter_position(ticker, validation_details)
# ACHÈTE une action !
# 
# 1. Vérifie limites risque
# 2. Récupère prix actuel (ask)
# 3. Calcule quantité (20% capital)
# 4. Calcule SL (-5%) et TP (+20%)
# 5. Place bracket order IBKR
# 6. Enregistre position
# 7. Notifie Telegram
# 
# Retourne (success, trade_details)

exit_position(ticker, reason)
# VEND une action !
# 
# 1. Récupère position
# 2. Prix actuel (bid)
# 3. Market order vente
# 4. Ferme position
# 5. Calcule PnL
# 6. Notifie Telegram (TP/SL/Urgence)
# 
# Retourne (success, exit_details)

check_emergency_exit_conditions(ticker)
# Vérifie conditions sortie urgente:
# - News négative (10 min)
# - Downgrade récent
# - Spread > 1% (2x normal)
# 
# Retourne (should_exit, reason)

monitor_open_positions()
# Surveille TOUTES positions ouvertes
# Appelle check_emergency_exit_conditions()
# Si urgence → exit_position() automatique
```

#### Bracket Order (SL + TP automatiques)

```python
# Ordre parent (achat)
parent_order = LimitOrder(
    action='BUY',
    totalQuantity=13,
    lmtPrice=150.50
)

# Ordre stop-loss (vente si -5%)
stop_loss_order = Order(
    orderType='STP',
    action='SELL',
    totalQuantity=13,
    auxPrice=142.98  # -5%
)

# Ordre take-profit (vente si +20%)
take_profit_order = Order(
    orderType='LMT',
    action='SELL',
    totalQuantity=13,
    lmtPrice=180.60  # +20%
)

# Les 3 ordres liés ensemble = bracket
# SL et TP s'exécutent automatiquement !
```

### Mode DRY_RUN

```python
if DRY_RUN_MODE:
    # Mode simulation
    # Pas d'ordre réel envoyé
    # Tout est loggé
    # Positions enregistrées (pour suivi)
else:
    # Mode RÉEL
    # Ordres envoyés à IBKR
    # Argent réel !
```

---

## 📱 MODULE : `telegram_notifier.py`

### Rôle
Envoie **notifications sur votre téléphone Telegram**.

### Types de notifications

```python
notify_entry(ticker, price, quantity, filters)
# 🟢 ACHAT
# Ticker, prix, quantité
# Stop-Loss, Take-Profit

notify_take_profit(ticker, entry, exit, profit)
# 🎯 TAKE PROFIT
# Gain: +20% (ex: +$300)

notify_stop_loss(ticker, entry, exit, loss)
# 🛑 STOP LOSS
# Perte: -5% (ex: -$75)

notify_emergency_exit(ticker, reason, entry, exit)
# ⚠️ SORTIE URGENCE
# Raison: news négative, spread instable...
# PnL: variable

notify_error(error_msg)
# ❌ ERREUR
# Problème technique, API, connexion...

notify_pause(reason)
# ⏸️ PAUSE TRADING
# Limite atteinte (-2% jour ou -6% semaine)

notify_daily_summary(stats)
# 📊 RÉSUMÉ JOURNALIER
# Trades, win rate, PnL total

notify_signal_detected(ticker, pattern, confidence)
# 🔔 SIGNAL DÉTECTÉ (optionnel)
# Pattern, score confiance
```

### Anti-spam

```python
# Cooldown 5 minutes par ticker + type
# Évite spam si signal détecté plusieurs fois

last_notifications = {}

def _can_send(ticker, notification_type):
    key = f"{ticker}_{notification_type}"
    if key in last_notifications:
        elapsed = time.time() - last_notifications[key]
        if elapsed < 300:  # 5 minutes
            return False
    return True
```

### Exemple message Telegram

```
🟢 ACHAT 🟢

Ticker: AAPL
Prix: $150.50
Quantité: 13
Valeur: $1,956.50

Stop-Loss: -5% ($142.98)
Take-Profit: +20% ($180.60)

⏰ 14:32:15
```

---

## 🧪 FICHIER : `test_connections.py`

### Rôle
**Teste les 3 connexions API** avant de lancer le bot.

### Tests effectués

```python
def test_ibkr():
    # 1. Connexion socket à TWS/Gateway
    # 2. Vérification comptes
    # 3. Test récupération prix SPY
    # 4. Affichage bid/ask/volume
    # 
    # Retourne True si OK

def test_benzinga():
    # 1. Test endpoint earnings
    # 2. Récupération earnings du jour
    # 3. Affichage nombre résultats
    # 
    # Retourne True si OK

async def test_telegram():
    # 1. Connexion bot
    # 2. Vérification infos bot
    # 3. Envoi message test
    # 
    # Retourne True si OK

def main():
    # Exécute les 3 tests
    # Affiche résumé
    # Retourne 0 si tous OK, 1 sinon
```

### Utilisation

```bash
python test_connections.py
```

Résultat attendu :
```
============================================================
🔌 TEST CONNEXION IBKR
============================================================
✅ Connexion réussie à IBKR!
   - SPY Prix: $485.32

============================================================
📰 TEST API BENZINGA
============================================================
✅ Connexion Benzinga réussie!
   - Earnings aujourd'hui: 45

============================================================
📱 TEST TELEGRAM BOT
============================================================
✅ Bot connecté!
   - Nom: Momentum Trading Bot
✅ Message envoyé avec succès!

============================================================
📊 RÉSUMÉ DES TESTS
============================================================
IBKR...................................... ✅ OK
Benzinga.................................. ✅ OK
Telegram.................................. ✅ OK

============================================================
🎉 TOUS LES TESTS RÉUSSIS!
✅ Le bot est prêt à être configuré
============================================================
```

---

## 📊 FICHIERS DATA (JSON)

### `watchlist_core.json`
Structure :
```json
{
  "description": "Leaders sectoriels",
  "sectors": {
    "technology": {
      "etf": "XLK",
      "stocks": ["AAPL", "MSFT", "NVDA", ...]
    },
    ...
  },
  "total_stocks": 50,
  "updated": "2025-12-03"
}
```

### `watchlist_secondary.json`
Structure :
```json
{
  "categories": {
    "recent_breakouts": {
      "stocks": []
    },
    "earnings_winners": {
      "stocks": []
    },
    ...
  }
}
```

### `positions.json`
Voir section risk_manager ci-dessus.

### `blacklist_sectors.json`
```json
{
  "excluded_sectors": [
    "Banks",
    "Insurance",
    ...
  ],
  "excluded_tickers": [
    "JPM", "BAC", "MRNA", ...
  ],
  "reason": "...",
  "updated": "2025-12-03"
}
```

---

## 🔑 FICHIER : `.env`

**À CRÉER** (copier depuis `.env.example`)

```bash
# Interactive Brokers
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# Benzinga
BENZINGA_API_KEY=your_key

# Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id

# Trading
DRY_RUN_MODE=True
PAPER_TRADING_MODE=True
MAX_POSITIONS=5
DAILY_LOSS_LIMIT=0.02
WEEKLY_LOSS_LIMIT=0.06
POSITION_SIZE_PCT=0.20
STOP_LOSS_PCT=0.05
TAKE_PROFIT_PCT=0.20
TIMEZONE=America/New_York
```

---

## 🔄 FLUX COMPLET D'UN TRADE

```
1. Bot démarre → run()
   ↓
2. Toutes les 5 min → run_cycle()
   ↓
3. Vérifications préalables
   ├─ Heures trading ? (10h15-16h00)
   ├─ Marché haussier ? (SPY/QQQ/VIX)
   └─ Limites risque OK ? (positions, pertes)
   ↓
4. Surveillance positions ouvertes
   └─ Sorties urgentes ? (news, spread)
   ↓
5. Scanner watchlist → scan_watchlist()
   ├─ Pour chaque ticker → scan_ticker()
   │  ├─ 11 filtres validation
   │  ├─ Pattern chandelier
   │  ├─ Volume validé
   │  └─ Breakout + orderflow
   └─ Retourne signaux valides
   ↓
6. Trier par score
   └─ Prendre meilleur signal
   ↓
7. Exécuter signal → execute_signal()
   ├─ enter_position()
   │  ├─ Calcul quantité
   │  ├─ Bracket order IBKR
   │  └─ Notification Telegram 🟢
   │
   └─ Position enregistrée
   ↓
8. Attendre 5 minutes
   ↓
9. Retour étape 2 (boucle)
   ↓
10. Stop-Loss ou Take-Profit atteint
    └─ exit_position()
       ├─ Fermeture automatique
       ├─ Calcul PnL
       └─ Notification Telegram 🎯/🛑
```

---

## 🎓 CONCEPTS CLÉS

### 1. **Momentum Trading**
- Trader actions en **tendance forte**
- "La tendance est ton amie"
- Suivre le mouvement, ne pas prédire

### 2. **Filtres multiples**
- **11 filtres** pour qualité maximale
- Mieux 1 excellent signal que 10 moyens
- Taux réussite > 55% visé

### 3. **Gestion du risque**
- **-5% Stop-Loss** : Limite perte
- **+20% Take-Profit** : Ratio gain/perte = 4:1
- **Limites strictes** : -2%/jour, -6%/semaine

### 4. **Automatisation**
- Bot tourne **24/7** (pendant heures marché)
- Pas d'émotion, pas de fatigue
- Discipline parfaite

### 5. **Patterns chandeliers**
- Méthode **Steve Nison** (référence mondiale)
- Patterns validés depuis siècles
- Volume DOIT confirmer

### 6. **Breakout**
- Cassure résistance = Signal fort
- Volume exceptionnel requis (150%+)
- Orderflow confirme pression acheteuse

---

## 📚 POUR ALLER PLUS LOIN

### Lire le code

1. **bot_commented.py** : Version super commentée du bot principal
2. Chaque module a section `if __name__ == '__main__'` pour tests individuels
3. Docstrings expliquent chaque fonction

### Tester modules individuellement

```bash
# Test chaque module séparément
python stock_data.py
python market_indices.py
python candlestick_patterns.py
python risk_manager.py
# etc.
```

### Modifier configuration

```bash
# Ajuster seuils
nano config.py

# Exemples:
VIX_MAX_LEVEL = 20  # Plus strict
MIN_VOLUME_MULTIPLIER = 1.5  # Volume plus élevé requis
```

### Ajouter features

1. Créer nouveau module dans `/scripts`
2. Importer dans `bot.py`
3. Intégrer dans `scan_ticker()` ou `run_cycle()`

---

## 🎯 RÉSUMÉ

**Ce bot est un système complet de trading automatisé** avec :

✅ **11 filtres stricts** pour qualité signaux
✅ **Gestion risque intégrée** (SL/TP automatiques)
✅ **Surveillance continue** (news, spread, positions)
✅ **Notifications temps réel** (Telegram)
✅ **Mode test sécurisé** (dry run + paper trading)

**Chaque ligne de code a un but précis** expliqué dans :
- `bot_commented.py` : Version annotée fichier principal
- Ce document : Vue d'ensemble architecture
- Docstrings dans chaque fichier

**Prêt à coder ?** Lisez `bot_commented.py` puis explorez modules un par un ! 🚀

