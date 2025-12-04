# 🤖 BOT TRADING ACTIONS US MOMENTUM

Bot de trading automatique sur actions US avec stratégie momentum : **+20% Take Profit / -5% Stop Loss**

---

## 📋 PRÉREQUIS

### Comptes requis
1. **Interactive Brokers** (IBKR)
   - Compte ouvert et vérifié
   - TWS ou IB Gateway installé
   - API activée dans les paramètres
   
2. **Benzinga Pro** (optionnel mais recommandé)
   - Abonnement API
   - Clé API obtenue
   
3. **Telegram Bot**
   - Bot créé via @BotFather
   - Token récupéré
   - Chat ID obtenu

### Système
- Ubuntu 20.04+ (ou WSL2)
- Python 3.12+
- Connexion internet stable

---

## 🚀 INSTALLATION

### 1. Installation des dépendances

```bash
cd /home/houhou/bot/action_momentum

# Activer environnement virtuel
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt
```

### 2. Configuration API

Créer fichier `.env` :

```bash
cp .env.example .env
nano .env
```

Remplir avec vos clés :

```bash
# Interactive Brokers
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # 7497 = Paper, 7496 = Live
IBKR_CLIENT_ID=1

# Benzinga Pro
BENZINGA_API_KEY=votre_cle_ici

# Telegram
TELEGRAM_BOT_TOKEN=votre_token_ici
TELEGRAM_CHAT_ID=votre_chat_id_ici

# Mode
DRY_RUN_MODE=True
PAPER_TRADING_MODE=True
```

### 3. Test des connexions

```bash
cd scripts
python test_connections.py
```

Vous devez voir :
```
✅ IBKR : OK
✅ Benzinga : OK
✅ Telegram : OK
```

---

## 📊 UTILISATION

### Lancer le bot (mode continu)

```bash
cd scripts
python bot.py
```

Le bot :
- Scanne la watchlist toutes les 5 minutes
- Détecte les opportunités
- Entre en position automatiquement
- Gère les stop-loss et take-profit
- Envoie des alertes Telegram

### Scan unique (test)

```bash
python bot.py --scan-once
```

Exécute un seul cycle de scan puis s'arrête.

### Arrêter le bot

Appuyez sur `Ctrl+C`

---

## 🔧 CONFIGURATION

### Watchlists

Éditer les fichiers :
- `data/watchlist_core.json` : Leaders sectoriels (mise à jour mensuelle)
- `data/watchlist_secondary.json` : Opportunités momentum (mise à jour hebdomadaire)

### Blacklist

Éditer `filters/blacklist_sectors.json` pour ajouter/retirer secteurs ou tickers interdits.

### Paramètres de risque

Dans `.env` :
```bash
MAX_POSITIONS=5           # Max positions simultanées
DAILY_LOSS_LIMIT=0.02     # -2% max par jour
WEEKLY_LOSS_LIMIT=0.06    # -6% max par semaine
POSITION_SIZE_PCT=0.20    # 20% capital par position
```

---

## 🧪 PHASES DE TEST

### 1. Phase à blanc (2 semaines)

```bash
# Dans .env
DRY_RUN_MODE=True
PAPER_TRADING_MODE=True
```

- Pas d'ordres réels
- Logs des opportunités
- Validation stratégie

### 2. Paper Trading (4-12 semaines)

```bash
# Dans .env
DRY_RUN_MODE=False
PAPER_TRADING_MODE=True
```

- Ordres réels sur compte démo
- Validation performances
- Ajustement paramètres

### 3. Trading réel (progressif)

```bash
# Dans .env
DRY_RUN_MODE=False
PAPER_TRADING_MODE=False
```

⚠️ **Commencer avec petit capital !**

---

## 📁 STRUCTURE

```
/bot/action_momentum/
├── .env                       # Configuration API (à créer)
├── requirements.txt           # Dépendances Python
├── README.md                  # Ce fichier
├── PLAN_IMPLEMENTATION.md     # Plan détaillé
│
├── /data/
│   ├── watchlist_core.json
│   ├── watchlist_secondary.json
│   └── positions.json
│
├── /filters/
│   └── blacklist_sectors.json
│
├── /logs/
│   └── (logs générés automatiquement)
│
├── /scripts/
│   ├── bot.py                    # 🎯 BOT PRINCIPAL
│   ├── config.py                 # Configuration
│   ├── test_connections.py       # Test API
│   │
│   ├── stock_data.py             # Données IBKR
│   ├── watchlist_manager.py      # Gestion watchlists
│   ├── news_monitor.py           # News Benzinga
│   ├── market_indices.py         # SPY, QQQ, VIX
│   ├── market_sectors.py         # Secteurs
│   │
│   ├── filters_time.py           # Filtres horaires
│   ├── filters.py                # Tous filtres
│   │
│   ├── candlestick_patterns.py   # Patterns Nison
│   ├── breakout_detector.py      # Breakouts
│   │
│   ├── risk_manager.py           # Gestion risque
│   ├── trading_manager.py        # Exécution trades
│   └── telegram_notifier.py      # Notifications
│
└── /venv/                        # Environnement virtuel
```

---

## 🎯 STRATÉGIE

### Conditions d'entrée (TOUTES requises)

1. **Watchlist** : Ticker dans watchlist core ou secondary
2. **Blacklist** : Ticker non blacklisté
3. **Horaires** : 10h15-16h00 US (exclusion 9h30-10h15)
4. **Earnings** : Pas d'earnings dans 48h
5. **Marché** : SPY + QQQ haussiers, VIX < 25
6. **Secteur** : ETF sectoriel haussier (>0.5% + volume)
7. **Action** : Pas de doji, pas mèche haute excessive
8. **Pattern** : Pattern haussier Steve Nison détecté
9. **Volume** : Volume >= 120% moyenne sur pattern
10. **Breakout** : Cassure résistance avec volume >= 150%
11. **Orderflow** : Bid > Ask, spread < 0.5%

### Gestion position

- **Entrée** : Limit order à ask + 0.02%
- **Stop-Loss** : -5% automatique (bracket order)
- **Take-Profit** : +20% automatique (bracket order)

### Sortie urgente (si détecté)

- News négative majeure
- Downgrade analyste
- Spread > 1% (2x limite normale)

### Limites risque

- Max 5 positions simultanées
- Max -2% capital par jour
- Max -6% capital par semaine
- Taille position : 20% capital

---

## 📱 NOTIFICATIONS TELEGRAM

Le bot envoie automatiquement :

- 🟢 **Achat** : Ticker, prix, quantité, SL, TP
- 🎯 **Take Profit** : Gain réalisé
- 🛑 **Stop Loss** : Perte limitée
- ⚠️ **Sortie urgence** : Raison
- ❌ **Erreurs** : Problèmes techniques
- ⏸️ **Pause** : Limites atteintes
- 📊 **Résumé journalier** : Performances

---

## 🔍 SURVEILLANCE & LOGS

### Positions ouvertes

```bash
cat data/positions.json
```

### Logs temps réel

```bash
tail -f logs/trades.json
```

### Statistiques

```python
python -c "
from risk_manager import RiskManager
rm = RiskManager(10000)
print(rm.get_statistics())
"
```

---

## ⚠️ POINTS D'ATTENTION

### Avant de lancer en réel

- [ ] Tests à blanc validés (2 semaines)
- [ ] Paper trading validé (Win rate > 55%)
- [ ] Capital de test uniquement
- [ ] TWS/Gateway lancé et connecté
- [ ] Notifications Telegram fonctionnelles
- [ ] Watchlist à jour
- [ ] Stop-loss bien configurés

### Surveillance quotidienne

- Vérifier positions ouvertes
- Vérifier PnL journalier
- Vérifier messages Telegram
- Vérifier connexion IBKR stable

### Maintenance

- **Hebdomadaire** : Mise à jour watchlist secondary
- **Mensuelle** : Mise à jour watchlist core
- **Mensuelle** : Revue blacklist
- **Bi-mensuel** : Optimisation filtres

---

## 🆘 DÉPANNAGE

### Bot ne démarre pas

1. Vérifier `.env` complet
2. Vérifier venv activé
3. Vérifier dépendances installées
4. Vérifier TWS/Gateway lancé

### Pas de signaux détectés

- Normal si marché pas favorable
- Vérifier VIX < 25
- Vérifier SPY/QQQ haussiers
- Vérifier heures de trading

### Erreurs connexion IBKR

1. TWS/Gateway lancé ?
2. API activée ?
3. Port correct (7497/7496) ?
4. Firewall autorise connexion ?

### Pas de notifications Telegram

1. Token valide ?
2. Chat ID correct ?
3. Bot ajouté au chat ?
4. Test manuel : `python scripts/telegram_notifier.py`

---

## 📚 RESSOURCES

- **Interactive Brokers API** : https://ib-insync.readthedocs.io/
- **Benzinga API** : https://www.benzinga.com/apis
- **Telegram Bots** : https://core.telegram.org/bots
- **Steve Nison Candlesticks** : "Japanese Candlestick Charting Techniques"

---

## 📞 SUPPORT

Pour questions ou problèmes :

1. Vérifier `PLAN_IMPLEMENTATION.md` pour détails
2. Consulter logs : `logs/errors.log`
3. Tester modules individuellement (chaque .py a section `if __name__ == '__main__'`)

---

## ⚖️ AVERTISSEMENT

**Trading comportant des risques de perte en capital.**

- Ce bot est fourni à titre éducatif
- Utilisez à vos propres risques
- Commencez toujours par paper trading
- Ne tradez que ce que vous pouvez vous permettre de perdre
- Les performances passées ne garantissent pas les résultats futurs

**L'auteur n'est pas responsable des pertes éventuelles.**

---

## 🎉 BON TRADING !

**Remember** : La discipline et la gestion du risque sont plus importantes que la stratégie elle-même.

**PATIENCE • DISCIPLINE • GESTION DU RISQUE**

