"""
BOT TRADING ACTIONS US MOMENTUM
===============================
Stratégie: +20% Take Profit / -5% Stop Loss

Ce fichier est le CERVEAU du bot.
Il orchestre tous les modules et exécute la stratégie complète de trading.

Fonctionnement:
1. Scanne la watchlist pour trouver des opportunités
2. Valide les signaux avec plusieurs filtres
3. Exécute les trades automatiquement
4. Surveille les positions ouvertes
5. Applique stop-loss et take-profit
"""

# ============================================================
# IMPORTS - Bibliothèques nécessaires
# ============================================================

import time  # Pour faire des pauses entre les cycles (time.sleep)
import asyncio  # Pour exécuter du code asynchrone (notifications Telegram)
from datetime import datetime  # Pour obtenir la date/heure actuelle
from typing import List, Dict  # Pour typer les variables (List = liste, Dict = dictionnaire)

# ============================================================
# IMPORTS - Nos propres modules du bot
# ============================================================

# Configuration globale (depuis .env)
from config import DRY_RUN_MODE, PAPER_TRADING_MODE

# Fournisseur de données boursières (via Interactive Brokers)
from stock_data import StockDataProvider

# Gestionnaire de la liste d'actions à surveiller
from watchlist_manager import WatchlistManager

# Moniteur de news (filtre les mauvaises nouvelles)
from news_monitor import NewsMonitor

# Analyseur des indices de marché (SPY, QQQ, VIX)
from market_indices import MarketIndicesAnalyzer

# Analyseur des secteurs (XLK, XLF, etc.)
from market_sectors import MarketSectorsAnalyzer

# Filtres de validation (volume, timing, etc.)
from filters import TradingFilters

# Détecteur de patterns de chandeliers japonais (Hammer, Engulfing, etc.)
from candlestick_patterns import CandlestickPatterns

# Détecteur de breakouts (cassure de résistance)
from breakout_detector import BreakoutDetector

# Gestionnaire du risque (stop-loss, limites de pertes)
from risk_manager import RiskManager

# Gestionnaire des trades (achats/ventes)
from trading_manager import TradingManager

# Notifications Telegram
from telegram_notifier import TelegramNotifier

# Fonctions de logging (écrire dans les logs)
from logger import (
    log_info,  # Information normale
    log_warning,  # Avertissement
    log_error,  # Erreur
    log_trade,  # Log d'un trade
    log_signal,  # Log d'un signal détecté
    log_market_status,  # Status du marché
    log_startup,  # Démarrage du bot
    log_shutdown,  # Arrêt du bot
    log_cycle  # Log d'un cycle terminé
)


# ============================================================
# CLASSE PRINCIPALE - MomentumBot
# ============================================================

class MomentumBot:
    """
    Bot principal de trading momentum
    
    Cette classe coordonne tous les autres modules pour:
    - Scanner les opportunités
    - Valider les signaux
    - Exécuter les trades
    - Gérer le risque
    """
    
    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    
    def __init__(self, capital: float = 10000):
        """
        Constructeur - Initialise le bot avec un capital de départ
        
        Args:
            capital: Le montant en $ pour trader (défaut: 10000$)
        """
        # Afficher un en-tête dans les logs
        log_info("=" * 60)
        log_info("🤖 BOT ACTIONS US MOMENTUM - INITIALISATION")
        log_info("=" * 60)
        
        # ---- Création de tous les composants du bot ----
        log_info("📦 Chargement modules...")
        
        # Fournisseur de données (connexion à Interactive Brokers)
        self.data_provider = StockDataProvider()
        
        # Gestionnaire de la watchlist (liste des actions à surveiller)
        self.watchlist_manager = WatchlistManager()
        
        # Moniteur de news (pour filtrer les actions avec mauvaises nouvelles)
        self.news_monitor = NewsMonitor()
        
        # Analyseur des indices de marché (SPY, QQQ, VIX)
        self.market_analyzer = MarketIndicesAnalyzer(self.data_provider)
        
        # Analyseur des secteurs (technologie, finance, santé, etc.)
        self.sector_analyzer = MarketSectorsAnalyzer(self.data_provider)
        
        # Gestionnaire du risque (limite les pertes)
        self.risk_manager = RiskManager(capital)
        
        # Notificateur Telegram (envoie des alertes sur votre téléphone)
        self.telegram = TelegramNotifier()
        
        # ---- Création des filtres de validation ----
        # Les filtres vérifient si une action est bonne à acheter
        self.filters = TradingFilters(
            self.data_provider,  # Pour récupérer les prix
            self.watchlist_manager,  # Pour vérifier la watchlist
            self.news_monitor,  # Pour vérifier les news
            self.market_analyzer,  # Pour vérifier le marché global
            self.sector_analyzer  # Pour vérifier le secteur
        )
        
        # Détecteur de patterns de chandeliers japonais
        self.patterns = CandlestickPatterns()
        
        # Détecteur de breakouts (cassure de résistance avec volume)
        self.breakout_detector = BreakoutDetector(self.data_provider)
        
        # ---- Création du gestionnaire de trading ----
        # C'est lui qui exécute les achats et ventes
        self.trading_manager = TradingManager(
            self.data_provider,  # Pour récupérer les prix
            self.risk_manager,  # Pour respecter les limites de risque
            self.telegram,  # Pour envoyer les notifications
            self.news_monitor  # Pour vérifier les news avant d'acheter
        )
        
        # ---- Variables d'état du bot ----
        self.running = False  # True quand le bot tourne, False quand arrêté
        self.cycle_count = 0  # Compteur de cycles (un cycle = un scan complet)
        
        log_info("✅ Modules chargés")
        
        # ---- Afficher les statistiques de démarrage ----
        stats = self.watchlist_manager.get_stats()  # Récupérer stats watchlist
        log_startup(
            capital=capital,  # Capital de départ
            dry_run=DRY_RUN_MODE,  # Mode test (pas de vrais ordres)
            paper=PAPER_TRADING_MODE,  # Mode paper trading IBKR
            watchlist_count=stats['total_count']  # Nombre d'actions à surveiller
        )
        log_info(f"📊 Blacklist: {stats['blacklist_count']} exclus")
    
    # --------------------------------------------------------
    # CONNEXION / DÉCONNEXION
    # --------------------------------------------------------
    
    def connect(self):
        """
        Se connecte à Interactive Brokers
        Cette connexion est nécessaire pour récupérer les prix et passer des ordres
        """
        log_info("🔌 Connexion IBKR...")
        self.data_provider.connect()  # Appelle la méthode connect() de StockDataProvider
        log_info("✅ Connecté à IBKR")
    
    def disconnect(self):
        """
        Se déconnecte d'Interactive Brokers
        Important de se déconnecter proprement à la fin
        """
        log_info("🔌 Déconnexion...")
        self.data_provider.disconnect()  # Appelle la méthode disconnect()
        log_info("✅ Déconnecté")
    
    # --------------------------------------------------------
    # SCAN D'UNE ACTION
    # --------------------------------------------------------
    
    def scan_ticker(self, ticker: str) -> Dict:
        """
        Scan complet d'une action (ticker)
        
        Cette méthode vérifie si une action est une bonne opportunité d'achat
        en passant par plusieurs étapes de validation.
        
        Args:
            ticker: Le symbole de l'action (ex: 'AAPL', 'MSFT', 'GOOGL')
        
        Returns:
            Un dictionnaire contenant:
            - 'ticker': Le symbole
            - 'valid': True si c'est une opportunité valide
            - 'filters_passed': Résultats de chaque filtre
            - 'pattern': Le pattern de chandelier détecté
            - 'breakout': Les détails du breakout
            - 'score': Score de 0 à 100 (plus c'est haut, meilleur c'est)
        """
        log_info(f"🔍 SCAN {ticker}")
        
        # Créer le dictionnaire de résultat avec valeurs par défaut
        result = {
            'ticker': ticker,
            'valid': False,  # Par défaut, pas valide
            'filters_passed': {},  # Résultats des filtres
            'pattern': None,  # Pattern détecté (ou None)
            'breakout': None,  # Breakout détecté (ou None)
            'score': 0  # Score de qualité
        }
        
        # ================================================
        # ÉTAPE 1: Validation des filtres de base
        # ================================================
        # Vérifie: volume, news, timing, marché global, secteur
        all_passed, filters_results = self.filters.validate_all_filters(ticker)
        result['filters_passed'] = filters_results
        
        # Si un filtre a échoué, on arrête là
        if not all_passed:
            # Récupérer la liste des filtres qui ont échoué
            failed = self.filters.get_failed_filters(filters_results)
            log_info(f"   ❌ {ticker}: Filtres échoués ({len(failed)}): {', '.join(failed)}")
            return result  # Retourner résultat négatif
        
        log_info(f"   ✅ {ticker}: Filtres de base passés")
        
        # ================================================
        # ÉTAPE 2: Détection d'un pattern de chandelier haussier
        # ================================================
        # Récupère les données OHLCV (Open, High, Low, Close, Volume)
        df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')  # Bougies 5 min sur 1 jour
        
        if df is not None and not df.empty:  # Si on a des données
            # Chercher un pattern haussier (Hammer, Engulfing, etc.)
            pattern = self.patterns.detect_bullish_pattern(df)
            
            if pattern:  # Pattern trouvé !
                result['pattern'] = pattern
                log_info(f"   🕯️  {ticker}: Pattern {pattern['pattern']} ({pattern['confidence']}%)")
            else:  # Pas de pattern
                log_info(f"   ❌ {ticker}: Pas de pattern haussier")
                return result  # Arrêter ici
        else:  # Pas de données
            log_warning(f"   ❌ {ticker}: Pas de données OHLCV")
            return result
        
        # ================================================
        # ÉTAPE 3: Validation du volume
        # ================================================
        # Le pattern doit être accompagné d'un volume supérieur à la moyenne
        last_candle = df.iloc[-1]  # Dernière bougie (la plus récente)
        recent = df.tail(20)  # 20 dernières bougies
        avg_volume = recent['volume'].iloc[:-1].mean()  # Volume moyen (sans la dernière)
        
        # Vérifier si le volume est suffisant
        is_volume_ok = self.patterns.validate_volume(last_candle, avg_volume)
        
        if not is_volume_ok:
            log_info(f"   ❌ {ticker}: Volume insuffisant")
            return result
        
        # Calculer le ratio de volume (actuel / moyenne)
        volume_ratio = last_candle['volume'] / avg_volume
        log_info(f"   ✅ {ticker}: Volume validé ({volume_ratio:.2f}x)")
        
        # ================================================
        # ÉTAPE 4: Détection de breakout + validation orderflow
        # ================================================
        # Un breakout = le prix casse une résistance
        # Orderflow = pression acheteuse (bid) vs vendeuse (ask)
        is_breakout_valid, breakout_details = self.breakout_detector.validate_breakout_with_orderflow(ticker)
        result['breakout'] = breakout_details
        
        if not is_breakout_valid:
            reason = breakout_details.get('reason', 'Inconnu')
            log_info(f"   ❌ {ticker}: Breakout non validé - {reason}")
            return result
        
        log_info(f"   ✅ {ticker}: Breakout validé avec orderflow haussier")
        
        # ================================================
        # ÉTAPE 5: Calcul du score global (0-100)
        # ================================================
        score = 0
        
        # Score de base = confiance du pattern (70-90 généralement)
        score += pattern['confidence']
        
        # Bonus si volume exceptionnel (> 2x la moyenne)
        if breakout_details['breakout']['volume_ratio'] > 2.0:
            score += 10
        
        # Bonus si forte pression acheteuse (bid pressure > 60%)
        if breakout_details['orderflow']['bid_pressure'] > 60:
            score += 5
        
        # Limiter le score à 100 maximum
        result['score'] = min(100, score)
        result['valid'] = True  # Signal validé !
        
        # Logger le signal détecté
        log_signal(ticker, pattern['pattern'], {
            'score': result['score'],
            'volume': f"{volume_ratio:.1f}x"
        })
        
        return result
    
    # --------------------------------------------------------
    # SCAN DE TOUTE LA WATCHLIST
    # --------------------------------------------------------
    
    def scan_watchlist(self) -> List[Dict]:
        """
        Scanne toute la watchlist pour trouver des opportunités
        
        Returns:
            Liste des signaux valides, triés par score décroissant
        """
        log_info("=" * 60)
        log_info("📡 SCAN WATCHLIST")
        log_info("=" * 60)
        
        # Récupérer tous les tickers de la watchlist
        all_tickers = self.watchlist_manager.get_all_tickers()
        
        log_info(f"📋 {len(all_tickers)} tickers à scanner")
        
        valid_signals = []  # Liste pour stocker les signaux valides
        
        # Parcourir chaque ticker
        for i, ticker in enumerate(all_tickers, 1):  # enumerate ajoute un compteur
            try:
                # Scanner le ticker
                result = self.scan_ticker(ticker)
                
                # Si signal valide, l'ajouter à la liste
                if result['valid']:
                    valid_signals.append(result)
                    
                    # Envoyer notification Telegram
                    asyncio.run(
                        self.telegram.notify_signal_detected(
                            ticker,
                            result['pattern']['pattern'],
                            result['score']
                        )
                    )
                
                # Pause de 1 seconde entre chaque ticker
                # Pour éviter de surcharger l'API (rate limiting)
                time.sleep(1)
                
            except Exception as e:  # Si erreur, continuer avec le suivant
                log_error(f"Erreur scan {ticker}: {e}")
                continue
        
        # Trier par score décroissant (meilleur en premier)
        valid_signals.sort(key=lambda x: x['score'], reverse=True)
        
        log_info(f"📊 RÉSULTATS: {len(valid_signals)}/{len(all_tickers)} signaux valides")
        
        # Afficher le top 5 des signaux
        if valid_signals:
            log_info("Top signaux:")
            for signal in valid_signals[:5]:  # [:5] = les 5 premiers
                ticker = signal['ticker']
                score = signal['score']
                pattern = signal['pattern']['pattern']
                log_info(f"   {ticker}: {score}/100 ({pattern})")
        
        return valid_signals
    
    # --------------------------------------------------------
    # EXÉCUTION D'UN SIGNAL (ACHAT)
    # --------------------------------------------------------
    
    def execute_signal(self, signal: Dict) -> bool:
        """
        Exécute un signal validé (passe un ordre d'achat)
        
        Args:
            signal: Le dictionnaire du signal (retourné par scan_ticker)
        
        Returns:
            True si l'achat a réussi, False sinon
        """
        ticker = signal['ticker']
        
        log_info(f"💰 EXÉCUTION {ticker}")
        
        # Appeler le trading manager pour ouvrir une position
        success, trade_details = self.trading_manager.enter_position(
            ticker,
            signal['filters_passed']
        )
        
        if success:
            # Récupérer les détails du trade
            price = trade_details.get('entry_price', 0)
            quantity = trade_details.get('quantity', 0)
            # Logger le trade
            log_trade("BUY", ticker, price, quantity, reason=f"Score: {signal['score']}")
            return True
        else:
            log_warning(f"Échec ouverture position: {ticker}")
            return False
    
    # --------------------------------------------------------
    # UN CYCLE COMPLET DE TRADING
    # --------------------------------------------------------
    
    def run_cycle(self):
        """
        Exécute un cycle complet de trading
        
        Un cycle comprend:
        1. Vérifier les conditions de marché
        2. Vérifier les limites de risque
        3. Surveiller les positions ouvertes
        4. Scanner la watchlist
        5. Exécuter le meilleur signal
        """
        self.cycle_count += 1  # Incrémenter le compteur de cycles
        
        log_info("=" * 60)
        log_info(f"🔄 CYCLE #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_info("=" * 60)
        
        # ================================================
        # ÉTAPE 1: Vérifier les conditions de marché
        # ================================================
        log_info("1️⃣ Vérification conditions marché...")
        
        # Vérifier si on est dans les heures de trading
        can_trade, reason = self.filters.filter_time()
        if not can_trade:
            log_info(f"   ❌ {reason}")
            return  # Arrêter le cycle
        log_info("   ✅ Heures de trading OK")
        
        # Vérifier l'émotion du marché (VIX, SPY, QQQ)
        can_trade, reason = self.filters.filter_market_emotion()
        if not can_trade:
            log_info(f"   ❌ {reason}")
            # Envoyer notification marché défavorable (seulement au 1er cycle)
            if self.cycle_count == 1:
                is_bullish, market_details = self.market_analyzer.is_market_bullish()
                asyncio.run(self.telegram.notify_market_unfavorable(market_details))
            return
        log_info("   ✅ Marché favorable")
        
        # ================================================
        # ÉTAPE 2: Vérifier les limites de risque
        # ================================================
        log_info("2️⃣ Vérification risque...")
        
        # Vérifier si on peut encore trader (pas de limite atteinte)
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            log_warning(f"Limite risque atteinte: {reason}")
            # Envoyer notification de pause
            asyncio.run(self.telegram.notify_pause(reason))
            return
        log_info("   ✅ Limites risque OK")
        
        # ================================================
        # ÉTAPE 3: Surveiller les positions ouvertes
        # ================================================
        log_info("3️⃣ Surveillance positions ouvertes...")
        
        # Vérifier stop-loss et take-profit sur les positions
        self.trading_manager.monitor_open_positions()
        
        # Compter les positions ouvertes
        open_count = len(self.risk_manager.get_open_positions())
        log_info(f"   📊 {open_count} position(s) ouverte(s)")
        
        # ================================================
        # ÉTAPE 4: Scanner la watchlist si capacité disponible
        # ================================================
        opportunities = 0  # Compteur d'opportunités trouvées
        
        # Vérifier si on a de la place pour une nouvelle position
        max_positions = self.risk_manager.positions.get('max_positions', 5)
        
        if open_count < max_positions:  # Si on peut encore ouvrir des positions
            log_info("4️⃣ Scan watchlist...")
            signals = self.scan_watchlist()  # Scanner toutes les actions
            opportunities = len(signals)
            
            # ================================================
            # ÉTAPE 5: Exécuter le meilleur signal
            # ================================================
            if signals:  # Si on a trouvé des signaux
                best_signal = signals[0]  # Le premier = le meilleur (trié par score)
                log_info(f"5️⃣ Exécution meilleur signal: {best_signal['ticker']}")
                self.execute_signal(best_signal)  # Acheter !
        else:
            log_info("4️⃣ Capacité max atteinte - Pas de nouveau scan")
        
        # Logger la fin du cycle
        log_cycle(self.cycle_count, opportunities, open_count)
    
    # --------------------------------------------------------
    # BOUCLE PRINCIPALE DU BOT
    # --------------------------------------------------------
    
    def run(self, interval_seconds: int = 300):
        """
        Lance le bot en boucle continue
        
        Le bot va répéter les cycles de trading indéfiniment
        jusqu'à ce qu'on l'arrête avec Ctrl+C
        
        Args:
            interval_seconds: Temps d'attente entre chaque cycle
                              Défaut: 300 secondes = 5 minutes
        """
        self.running = True  # Marquer le bot comme actif
        
        # Afficher message de démarrage
        log_info("🚀 " * 20)
        log_info(f"BOT DÉMARRÉ - Intervalle {interval_seconds}s")
        log_info("🚀 " * 20)
        
        try:
            # Se connecter à Interactive Brokers
            self.connect()
            
            # Envoyer notification Telegram de démarrage (après connexion réussie)
            asyncio.run(
                self.telegram.notify_bot_started(
                    capital=self.risk_manager.positions.get('capital', 10000),
                    dry_run=DRY_RUN_MODE,
                    watchlist_count=len(self.watchlist_manager.get_watchlist())
                )
            )
            
            # Boucle infinie
            while self.running:
                try:
                    # Exécuter un cycle de trading
                    self.run_cycle()
                    
                except Exception as e:
                    # Si erreur pendant le cycle, la logger et continuer
                    log_error(f"Erreur cycle {self.cycle_count}: {str(e)}")
                    asyncio.run(self.telegram.notify_error(str(e)))
                
                # Attendre avant le prochain cycle
                log_info(f"⏸️  Attente {interval_seconds}s avant prochain cycle...")
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            # L'utilisateur a appuyé sur Ctrl+C
            log_warning("Arrêt demandé par utilisateur (Ctrl+C)")
        
        finally:
            # Ce code s'exécute TOUJOURS à la fin (arrêt propre)
            self.running = False
            self.disconnect()  # Se déconnecter d'IBKR
            
            # ---- Afficher le résumé final ----
            stats = self.risk_manager.get_statistics()
            
            log_info("=" * 60)
            log_info("📊 RÉSUMÉ FINAL")
            log_info("=" * 60)
            log_info(f"Cycles: {self.cycle_count}")
            log_info(f"Trades: {stats.get('total_trades', 0)}")
            log_info(f"Win rate: {stats.get('win_rate', 0):.1f}%")
            log_info(f"PnL: ${stats.get('total_pnl', 0):+,.2f}")
            log_info("=" * 60)
            
            log_shutdown()
            
            # Envoyer résumé sur Telegram
            asyncio.run(
                self.telegram.notify_daily_summary(stats)
            )


# ============================================================
# POINT D'ENTRÉE - Quand on lance le fichier directement
# ============================================================

# Ce code ne s'exécute QUE si on lance: python bot.py
# Il ne s'exécute PAS si on importe le fichier depuis un autre fichier

if __name__ == '__main__':
    # Créer le bot avec 10,000$ de capital
    bot = MomentumBot(capital=10000)
    
    # Importer sys pour lire les arguments de ligne de commande
    import sys
    
    # Vérifier si l'argument --scan-once a été passé
    # Usage: python bot.py --scan-once
    if len(sys.argv) > 1 and sys.argv[1] == '--scan-once':
        # MODE SCAN UNIQUE: un seul cycle puis arrêt
        # Utile pour tester
        bot.connect()
        try:
            bot.run_cycle()  # Un seul cycle
        finally:
            bot.disconnect()
    else:
        # MODE NORMAL: boucle continue
        # Le bot tourne indéfiniment (Ctrl+C pour arrêter)
        # Cycle toutes les 300 secondes (5 minutes)
        bot.run(interval_seconds=300)
