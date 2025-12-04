# 🚀 QUICK START - BOT MOMENTUM

## ✅ ÉTAPES RAPIDES

### 1. Installer python-dotenv (manquant)

```bash
cd /home/houhou/bot/action_momentum
source venv/bin/activate
pip install python-dotenv
```

### 2. Créer fichier .env

```bash
cd /home/houhou/bot/action_momentum
cp .env.example .env
nano .env
```

Remplir **AU MINIMUM** :
```bash
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id
```

Les autres peuvent rester vides pour les tests initiaux.

### 3. Test connexions

```bash
cd scripts
python test_connections.py
```

### 4. Lancer bot (mode test)

```bash
python bot.py --scan-once
```

---

## 📋 PROCHAINES ÉTAPES

1. **Obtenir clés API** :
   - IBKR : Ouvrir compte + activer API
   - Benzinga : S'abonner à Benzinga Pro
   - Telegram : Créer bot via @BotFather

2. **Configurer TWS/IB Gateway** :
   - Installer et lancer
   - Activer API dans paramètres
   - Port 7497 (Paper) ou 7496 (Live)

3. **Phase à blanc** (2 semaines) :
   - DRY_RUN_MODE=True
   - Observer logs et signaux
   - Pas d'argent réel

4. **Paper trading** (4-12 semaines) :
   - DRY_RUN_MODE=False
   - PAPER_TRADING_MODE=True
   - Valider performances

5. **Trading réel** (progressif) :
   - Petit capital de test
   - Surveillance quotidienne
   - Ajustements si besoin

---

## 🎯 COMMANDES ESSENTIELLES

```bash
# Activer environnement
source venv/bin/activate

# Test connexions
cd scripts && python test_connections.py

# Scan unique (test)
python bot.py --scan-once

# Lancer bot (5min cycles)
python bot.py

# Arrêter : Ctrl+C
```

---

## 📁 FICHIERS IMPORTANTS

- `.env` : Configuration API (À CRÉER)
- `README.md` : Documentation complète
- `PLAN_IMPLEMENTATION.md` : Plan détaillé
- `data/watchlist_core.json` : Watchlist principale
- `data/positions.json` : Positions ouvertes

---

## ⚠️ RAPPELS IMPORTANTS

1. **Toujours commencer en mode DRY_RUN**
2. **Ne jamais sauter la phase paper trading**
3. **Commencer avec petit capital en réel**
4. **Surveiller quotidiennement les positions**
5. **Respecter les limites de risque**

---

## 🆘 PROBLÈMES COURANTS

**Bot ne démarre pas** :
- Vérifier venv activé
- Vérifier .env existe et complet
- Vérifier python-dotenv installé

**Pas de signaux** :
- Normal si marché défavorable
- Vérifier heures de trading US
- Vérifier VIX < 25

**Erreur IBKR** :
- TWS/Gateway lancé ?
- API activée ?
- Port correct ?

---

Voir `README.md` pour documentation complète !

