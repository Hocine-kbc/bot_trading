"""
Configuration centralisée du bot
================================
Ce fichier contient TOUTES les constantes et paramètres du bot.
Les valeurs sensibles (API keys, tokens) sont lues depuis le fichier .env

Pour modifier un paramètre:
1. Si c'est sensible (token, clé API) → modifier dans .env
2. Si c'est une constante (seuils, listes) → modifier ici directement
"""

# ============================================================
# IMPORTS
# ============================================================

import os  # Pour lire les variables d'environnement (os.getenv)
from pathlib import Path  # Pour gérer les chemins de fichiers
from dotenv import load_dotenv  # Pour charger le fichier .env

# ============================================================
# CHARGEMENT DU FICHIER .env
# ============================================================

# Trouver le dossier racine du projet (parent du dossier scripts/)
# __file__ = chemin de ce fichier (config.py)
# .resolve() = chemin absolu
# .parent = dossier parent (scripts/)
# .parent = dossier parent (action_momentum/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Charger les variables du fichier .env dans l'environnement
# Après ça, on peut utiliser os.getenv() pour lire les valeurs
load_dotenv(BASE_DIR / '.env')

# ============================================================
# INTERACTIVE BROKERS - Connexion au broker
# ============================================================

# Adresse IP de TWS ou IB Gateway (127.0.0.1 = localhost = même machine)
IBKR_HOST = os.getenv('IBKR_HOST', '127.0.0.1')

# Port de connexion:
# - 7497 = TWS Paper Trading (simulation)
# - 7496 = TWS Live Trading (argent réel)
# - 4002 = IB Gateway Paper
# - 4001 = IB Gateway Live
IBKR_PORT = int(os.getenv('IBKR_PORT', 7497))

# ID client unique (permet plusieurs connexions simultanées)
IBKR_CLIENT_ID = int(os.getenv('IBKR_CLIENT_ID', 1))

# ============================================================
# BENZINGA - API de news financières
# ============================================================

# Clé API pour récupérer les news (https://www.benzinga.com/apis)
BENZINGA_API_KEY = os.getenv('BENZINGA_API_KEY', '')

# ============================================================
# TELEGRAM - Notifications sur téléphone
# ============================================================

# Token du bot (obtenu via @BotFather sur Telegram)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# ID du chat où envoyer les messages (votre conversation avec le bot)
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# ============================================================
# CONFIGURATION DU TRADING
# ============================================================

# Mode DRY RUN = simulation sans passer de vrais ordres
# True = pas d'ordres réels, False = ordres réels
DRY_RUN_MODE = os.getenv('DRY_RUN_MODE', 'True').lower() == 'true'

# Mode Paper Trading = utiliser le compte de simulation IBKR
# True = paper trading, False = argent réel
PAPER_TRADING_MODE = os.getenv('PAPER_TRADING_MODE', 'True').lower() == 'true'

# Nombre maximum de positions ouvertes en même temps
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', 5))

# Limite de perte journalière (2% = 0.02)
# Si atteinte, le bot s'arrête pour la journée
DAILY_LOSS_LIMIT = float(os.getenv('DAILY_LOSS_LIMIT', 0.02))

# Limite de perte hebdomadaire (6% = 0.06)
WEEKLY_LOSS_LIMIT = float(os.getenv('WEEKLY_LOSS_LIMIT', 0.06))

# Taille de chaque position en % du capital (20% = 0.20)
# Ex: avec 10000$ de capital, chaque position = 2000$
POSITION_SIZE_PCT = float(os.getenv('POSITION_SIZE_PCT', 0.20))

# ============================================================
# GESTION DU RISQUE - Stop Loss & Take Profit
# ============================================================

# Stop Loss = vendre si le prix baisse de X%
# 5% = 0.05 → si acheté à 100$, vendre si tombe à 95$
STOP_LOSS_PCT = float(os.getenv('STOP_LOSS_PCT', 0.05))

# Take Profit = vendre si le prix monte de X%
# 20% = 0.20 → si acheté à 100$, vendre si atteint 120$
TAKE_PROFIT_PCT = float(os.getenv('TAKE_PROFIT_PCT', 0.20))

# ============================================================
# FUSEAU HORAIRE
# ============================================================

# Fuseau horaire pour les horaires de marché (New York)
TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')

# ============================================================
# CHEMINS DES DOSSIERS
# ============================================================

# Dossier des données (watchlists, positions)
DATA_DIR = BASE_DIR / 'data'

# Dossier des filtres (blacklist)
FILTERS_DIR = BASE_DIR / 'filters'

# Dossier des logs
LOGS_DIR = BASE_DIR / 'logs'

# ============================================================
# CHEMINS DES FICHIERS
# ============================================================

# Watchlist principale (leaders sectoriels - grandes entreprises)
WATCHLIST_CORE_FILE = DATA_DIR / 'watchlist_core.json'

# Watchlist secondaire (opportunités momentum)
WATCHLIST_SECONDARY_FILE = DATA_DIR / 'watchlist_secondary.json'

# Liste des secteurs/tickers à éviter
BLACKLIST_FILE = FILTERS_DIR / 'blacklist_sectors.json'

# Fichier de suivi des positions ouvertes
POSITIONS_FILE = DATA_DIR / 'positions.json'

# ============================================================
# HORAIRES DE TRADING (Heure de New York)
# ============================================================

# Ouverture du marché US
MARKET_OPEN = '09:30'

# Fermeture du marché US
MARKET_CLOSE = '16:00'

# Période d'exclusion (marché trop volatil à l'ouverture)
# Le bot n'achète pas pendant les 45 premières minutes
EXCLUDED_START = '09:30'
EXCLUDED_END = '10:15'

# ============================================================
# ETFs SECTORIELS
# ============================================================
# Ces ETFs représentent chaque secteur du S&P 500
# On les utilise pour analyser la santé de chaque secteur

SECTOR_ETFS = {
    'technology': 'XLK',           # Technologie (Apple, Microsoft, Nvidia)
    'consumer_discretionary': 'XLY',  # Consommation discrétionnaire (Amazon, Tesla)
    'energy': 'XLE',               # Énergie (Exxon, Chevron)
    'financials': 'XLF',           # Finance (JPMorgan, Bank of America)
    'healthcare': 'XLV',           # Santé (Johnson & Johnson, Pfizer)
    'industrials': 'XLI',          # Industrie (Boeing, Caterpillar)
    'consumer_staples': 'XLP',     # Biens de consommation (Procter & Gamble)
    'utilities': 'XLU',            # Services publics (électricité, gaz)
    'materials': 'XLB',            # Matériaux (Dow, DuPont)
    'real_estate': 'XLRE',         # Immobilier
    'communication': 'XLC'         # Communication (Google, Meta)
}

# ============================================================
# INDICES DE MARCHÉ
# ============================================================
# On surveille ces indices pour évaluer la santé globale du marché

MARKET_INDICES = [
    'SPY',  # S&P 500 - Les 500 plus grandes entreprises US
    'QQQ',  # Nasdaq 100 - Les 100 plus grandes entreprises tech
    'VIX'   # Indice de volatilité ("indice de la peur")
]

# ============================================================
# PATTERNS DE CHANDELIERS JAPONAIS
# ============================================================
# Basé sur les travaux de Steve Nison (père des chandeliers japonais)

# Patterns HAUSSIERS (signaux d'achat potentiels)
BULLISH_PATTERNS = [
    'HAMMER',              # Marteau - retournement haussier
    'INVERTED_HAMMER',     # Marteau inversé
    'BULLISH_ENGULFING',   # Englobante haussière - forte hausse
    'PIERCING_LINE',       # Ligne perçante
    'THREE_WHITE_SOLDIERS' # Trois soldats blancs - forte tendance haussière
]

# Patterns BAISSIERS (signaux de vente/à éviter)
BEARISH_PATTERNS = [
    'SHOOTING_STAR',       # Étoile filante - retournement baissier
    'HANGING_MAN',         # Homme pendu
    'DOJI',                # Doji - indécision du marché
    'BEARISH_ENGULFING',   # Englobante baissière
    'EVENING_STAR'         # Étoile du soir
]

# ============================================================
# SEUILS DES FILTRES
# ============================================================

# Volume minimum requis (120% de la moyenne)
# Si volume < 120% moyenne → pas d'achat (manque de liquidité)
MIN_VOLUME_MULTIPLIER = 1.2

# Volume requis pour un breakout (150% de la moyenne)
# Un breakout valide doit avoir beaucoup de volume
BREAKOUT_VOLUME_MULTIPLIER = 1.5

# Niveau maximum du VIX (indice de peur)
# VIX > 25 = marché très volatile, on n'achète pas
VIX_MAX_LEVEL = 25

# Variation minimum du SPY pour confirmer tendance haussière (0.3%)
SPY_MIN_CHANGE = 0.003

# Variation minimum du QQQ (0.3%)
QQQ_MIN_CHANGE = 0.003

# Variation minimum du secteur pour confirmer force sectorielle (0.5%)
SECTOR_MIN_CHANGE = 0.005

# Taille du corps pour détecter un Doji
# Si corps < 20% de la range totale → c'est un Doji
DOJI_BODY_PCT = 0.20

# Taille de la mèche haute pour détecter shooting star/hanging man
# Si mèche haute > 50% de la range → signal de retournement
HIGH_WICK_PCT = 0.50

# Spread maximum acceptable (0.5%)
# Si spread > 0.5% → trop cher à trader, on évite
SPREAD_MAX_PCT = 0.005

# ============================================================
# MOTS-CLÉS NÉGATIFS POUR LES NEWS
# ============================================================
# Si une news contient ces mots → on n'achète pas l'action

NEGATIVE_KEYWORDS = [
    'downgrade',           # Dégradation par un analyste
    'lawsuit',             # Procès
    'investigation',       # Enquête
    'recall',              # Rappel de produits
    'fraud',               # Fraude
    'bankruptcy',          # Faillite
    'miss',                # Objectifs manqués
    'below expectations',  # En dessous des attentes
    'disappointing',       # Décevant
    'weak',                # Faible
    'loss',                # Perte
    'decline'              # Déclin
]

# ============================================================
# NOTIFICATIONS TELEGRAM
# ============================================================

# Temps d'attente entre 2 notifications pour le même ticker (en secondes)
# 300 secondes = 5 minutes
# Évite le spam si le bot détecte plusieurs fois le même signal
NOTIFICATION_COOLDOWN_SECONDS = 300
