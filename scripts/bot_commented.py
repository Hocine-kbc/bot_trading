"""
BOT TRADING ACTIONS US MOMENTUM
Stratégie: +20% Take Profit / -5% Stop Loss

Ce fichier est le CERVEAU du bot. Il orchestre tous les autres modules.
"""

# ============================================================================
# IMPORTS - Bibliothèques nécessaires
# ============================================================================

import time  # Pour les pauses entre cycles (sleep)
import asyncio  # Pour exécuter code asynchrone (Telegram)
from datetime import datetime  # Pour horodatage et dates
from typing import List, Dict  # Pour typage des fonctions (clarté code)

# ============================================================================
# IMPORTS MODULES PERSONNALISÉS - Nos propres modules
# ============================================================================

# Configuration : Variables globales (DRY_RUN, PAPER_TRADING, etc.)
from config import DRY_RUN_MODE, PAPER_TRADING_MODE

# Module données : Récupère prix, volumes, orderflow depuis IBKR
from stock_data import StockDataProvider

# Module watchlist : Gère liste actions autorisées/interdites
from watchlist_manager import WatchlistManager

# Module news : Surveille actualités Benzinga (earnings, downgrades)
from news_monitor import NewsMonitor

# Module indices : Analyse SPY, QQQ, VIX pour état marché
from market_indices import MarketIndicesAnalyzer

# Module secteurs : Analyse ETF sectoriels (XLK, XLY, XLE...)
from market_sectors import MarketSectorsAnalyzer

# Module filtres : Regroupe TOUS les filtres de validation
from filters import TradingFilters

# Module patterns : Détecte chandeliers japonais (Steve Nison)
from candlestick_patterns import CandlestickPatterns

# Module breakout : Détecte cassures de résistance
from breakout_detector import BreakoutDetector

# Module risque : Gère limites pertes, taille positions
from risk_manager import RiskManager

# Module trading : Exécute achats/ventes sur IBKR
from trading_manager import TradingManager

# Module Telegram : Envoie notifications sur votre téléphone
from telegram_notifier import TelegramNotifier


# ============================================================================
# CLASSE PRINCIPALE - Le bot lui-même
# ============================================================================

class MomentumBot:
    """
    Bot principal de trading momentum
    
    C'est la classe qui contient toute la logique du bot.
    Elle initialise tous les modules et orchestre le trading.
    """
    
    def __init__(self, capital: float = 10000):
        """
        Constructeur : Initialise le bot avec un capital de départ
        
        Args:
            capital: Capital initial en dollars (défaut 10000$)
        """
        
        # Affichage bannière de démarrage
        print("\n" + "🤖 "*30)  # Ligne de décoration
        print("BOT ACTIONS US MOMENTUM - INITIALISATION")
        print("🤖 " * 30 + "\n")
        
        # ========================================================================
        # INITIALISATION DES MODULES
        # ========================================================================
        
        print("📦 Chargement modules...")
        
        # Module 1 : Fournisseur de données IBKR
        # Ce module se connecte à Interactive Brokers pour récupérer prix/volumes
        self.data_provider = StockDataProvider()
        
        # Module 2 : Gestionnaire de watchlist
        # Charge watchlist_core.json et watchlist_secondary.json
        # Vérifie qu'on ne trade QUE les actions autorisées
        self.watchlist_manager = WatchlistManager()
        
        # Module 3 : Moniteur de news Benzinga
        # Surveille earnings, downgrades, news négatives
        self.news_monitor = NewsMonitor()
        
        # Module 4 : Analyseur indices (SPY, QQQ, VIX)
        # Détermine si marché est haussier ou baissier
        self.market_analyzer = MarketIndicesAnalyzer(self.data_provider)
        
        # Module 5 : Analyseur secteurs (ETF sectoriels)
        # Détermine quels secteurs sont en momentum haussier
        self.sector_analyzer = MarketSectorsAnalyzer(self.data_provider)
        
        # Module 6 : Gestionnaire de risque
        # Surveille limites pertes journalières/hebdomadaires
        # Gère taille des positions (20% capital max par action)
        self.risk_manager = RiskManager(capital)
        
        # Module 7 : Notificateur Telegram
        # Envoie messages sur votre téléphone (achats, ventes, erreurs)
        self.telegram = TelegramNotifier()
        
        # Module 8 : Gestionnaire de filtres (LE PLUS IMPORTANT !)
        # Combine TOUS les filtres (horaires, earnings, marché, secteur, action)
        # Doit valider 11 conditions avant d'autoriser un trade
        self.filters = TradingFilters(
            self.data_provider,      # Pour récupérer données prix/volume
            self.watchlist_manager,  # Pour vérifier watchlist/blacklist
            self.news_monitor,       # Pour vérifier news/earnings
            self.market_analyzer,    # Pour vérifier état marché
            self.sector_analyzer     # Pour vérifier état secteur
        )
        
        # Module 9 : Détecteur de patterns chandeliers
        # Détecte hammer, engulfing, three white soldiers...
        self.patterns = CandlestickPatterns()
        
        # Module 10 : Détecteur de breakouts
        # Détecte cassures de résistance avec volume
        self.breakout_detector = BreakoutDetector(self.data_provider)
        
        # Module 11 : Gestionnaire de trading (EXÉCUTION)
        # Entre en position, place stop-loss/take-profit
        # Surveille positions ouvertes pour sorties urgentes
        self.trading_manager = TradingManager(
            self.data_provider,  # Pour prix temps réel
            self.risk_manager,   # Pour taille position
            self.telegram,       # Pour notifications
            self.news_monitor    # Pour sorties urgentes
        )
        
        # Variable d'état : Le bot est-il en cours d'exécution ?
        self.running = False
        
        print("✅ Modules chargés\n")
        
        # ========================================================================
        # AFFICHAGE CONFIGURATION
        # ========================================================================
        
        # Récupérer statistiques watchlist
        stats = self.watchlist_manager.get_stats()
        
        # Afficher configuration au démarrage
        print(f"📊 Configuration:")
        print(f"   Capital: ${capital:,.2f}")  # Ex: $10,000.00
        
        # Afficher mode (DRY RUN = simulation, RÉEL = vrais ordres)
        print(f"   Mode: {'🧪 DRY RUN' if DRY_RUN_MODE else '💰 RÉEL'}")
        
        # Afficher si paper trading (compte démo IBKR)
        print(f"   Paper Trading: {'✅' if PAPER_TRADING_MODE else '❌'}")
        
        # Afficher nombre actions dans watchlist
        print(f"   Watchlist: {stats['total_count']} actions")
        
        # Afficher nombre actions blacklistées
        print(f"   Blacklist: {stats['blacklist_count']} exclus")
        print()
    
    
    # ========================================================================
    # MÉTHODE : Connexion IBKR
    # ========================================================================
    
    def connect(self):
        """
        Se connecte à Interactive Brokers (TWS ou IB Gateway)
        
        Doit être appelé AVANT de lancer le bot.
        Établit connexion socket avec TWS sur port 7497 (paper) ou 7496 (live).
        """
        print("🔌 Connexion IBKR...")
        
        # Appeler méthode connect() du data_provider
        # Établit connexion TCP/IP avec TWS/Gateway
        self.data_provider.connect()
        
        print("✅ Connecté\n")
    
    
    # ========================================================================
    # MÉTHODE : Déconnexion IBKR
    # ========================================================================
    
    def disconnect(self):
        """
        Se déconnecte d'Interactive Brokers
        
        Appelé automatiquement à la fin du bot.
        Ferme proprement la connexion socket.
        """
        print("\n🔌 Déconnexion...")
        
        # Fermer connexion IBKR
        self.data_provider.disconnect()
        
        print("✅ Déconnecté")
    
    
    # ========================================================================
    # MÉTHODE : Scanner un ticker (CŒUR DU BOT)
    # ========================================================================
    
    def scan_ticker(self, ticker: str) -> Dict:
        """
        Analyse COMPLÈTE d'une action pour déterminer si on peut l'acheter
        
        Cette méthode applique TOUS les filtres dans l'ordre :
        1. Filtres de base (watchlist, horaires, earnings, marché, secteur, action)
        2. Détection pattern chandelier
        3. Validation volume
        4. Détection breakout
        5. Validation orderflow
        
        Args:
            ticker: Symbole action (ex: "AAPL", "TSLA")
        
        Returns:
            Dictionnaire avec résultats :
            {
                'ticker': 'AAPL',
                'valid': True/False,  # True = OK pour acheter
                'filters_passed': {...},  # Détails chaque filtre
                'pattern': {...},  # Pattern détecté (ex: HAMMER)
                'breakout': {...},  # Infos breakout
                'score': 85  # Score 0-100 (confiance signal)
            }
        """
        
        # Affichage bannière scan
        print(f"\n{'='*60}")
        print(f"🔍 SCAN {ticker}")
        print(f"{'='*60}\n")
        
        # Préparer structure résultat
        result = {
            'ticker': ticker,
            'valid': False,  # Par défaut : pas valide
            'filters_passed': {},  # Détails filtres
            'pattern': None,  # Pattern chandelier détecté
            'breakout': None,  # Détails breakout
            'score': 0  # Score confiance
        }
        
        # ========================================================================
        # ÉTAPE 1 : VALIDATION FILTRES DE BASE (11 conditions)
        # ========================================================================
        
        # Appeler méthode qui teste TOUS les filtres :
        # - Watchlist/Blacklist
        # - Horaires (pas 09h30-10h15)
        # - Earnings (pas dans 48h)
        # - Marché (SPY/QQQ haussiers, VIX < 25)
        # - Secteur (ETF sectoriel haussier)
        # - Action (pas doji, pas mèche haute, volume OK)
        # - News négatives (pas de downgrade)
        # - Spread (< 0.5%)
        all_passed, filters_results = self.filters.validate_all_filters(ticker)
        
        # Stocker résultats filtres
        result['filters_passed'] = filters_results
        
        # Si au moins 1 filtre échoue : STOP, on ne continue pas
        if not all_passed:
            # Récupérer liste filtres échoués
            failed = self.filters.get_failed_filters(filters_results)
            
            # Afficher raisons échec
            print(f"❌ Filtres échoués ({len(failed)}):")
            for f in failed:
                print(f"   • {f}")
            
            # Retourner résultat avec valid=False
            return result
        
        # Si on arrive ici : TOUS les filtres de base sont passés ! ✅
        print(f"✅ Tous les filtres de base passés")
        
        # ========================================================================
        # ÉTAPE 2 : DÉTECTION PATTERN CHANDELIER
        # ========================================================================
        
        # Récupérer données OHLCV (Open, High, Low, Close, Volume)
        # Sur intervalle 5 minutes, dernières 24h
        df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')
        
        # Vérifier qu'on a bien reçu des données
        if df is not None and not df.empty:
            
            # Chercher pattern haussier (hammer, engulfing, etc.)
            pattern = self.patterns.detect_bullish_pattern(df)
            
            # Si pattern trouvé
            if pattern:
                # Stocker dans résultat
                result['pattern'] = pattern
                
                # Afficher quel pattern détecté + confiance
                print(f"🕯️  Pattern: {pattern['pattern']} ({pattern['confidence']}%)")
            else:
                # Pas de pattern haussier : STOP
                print(f"❌ Pas de pattern haussier détecté")
                return result
        else:
            # Pas de données OHLCV : STOP
            print(f"❌ Pas de données OHLCV")
            return result
        
        # ========================================================================
        # ÉTAPE 3 : VALIDATION VOLUME DU PATTERN
        # ========================================================================
        
        # Récupérer dernière bougie (chandelier le plus récent)
        last_candle = df.iloc[-1]
        
        # Récupérer 20 dernières bougies pour calcul moyenne
        recent = df.tail(20)
        
        # Calculer volume moyen des 19 bougies précédentes
        # (on exclut la dernière pour ne pas biaiser la moyenne)
        avg_volume = recent['volume'].iloc[:-1].mean()
        
        # Vérifier que volume actuel >= 120% volume moyen
        is_volume_ok = self.patterns.validate_volume(last_candle, avg_volume)
        
        if not is_volume_ok:
            # Volume insuffisant : STOP
            print(f"❌ Volume insuffisant pour pattern")
            return result
        
        # Volume validé : afficher ratio
        print(f"✅ Volume validé ({last_candle['volume']/avg_volume:.2f}x)")
        
        # ========================================================================
        # ÉTAPE 4 : DÉTECTION BREAKOUT + VALIDATION ORDERFLOW
        # ========================================================================
        
        # Vérifier breakout (cassure résistance) ET orderflow (bid/ask)
        # Cette méthode fait 2 vérifications en une :
        # 1. Prix casse résistance des 20 dernières bougies
        # 2. Volume >= 150% moyenne
        # 3. Orderflow haussier (bid > ask, spread < 0.5%)
        is_breakout_valid, breakout_details = self.breakout_detector.validate_breakout_with_orderflow(ticker)
        
        # Stocker détails breakout
        result['breakout'] = breakout_details
        
        if not is_breakout_valid:
            # Breakout non validé : STOP
            reason = breakout_details.get('reason', 'Inconnu')
            print(f"❌ Breakout non validé: {reason}")
            return result
        
        # Breakout validé ! ✅
        print(f"✅ Breakout validé avec orderflow haussier")
        
        # ========================================================================
        # ÉTAPE 5 : CALCUL SCORE GLOBAL
        # ========================================================================
        
        # Calculer score de confiance (0-100)
        score = 0
        
        # Base : Confiance du pattern (70-90 selon pattern)
        score += pattern['confidence']
        
        # Bonus si volume exceptionnel (> 2x moyenne)
        if breakout_details['breakout']['volume_ratio'] > 2.0:
            score += 10  # +10 points
        
        # Bonus si pression acheteuse très forte (> 60% bid)
        if breakout_details['orderflow']['bid_pressure'] > 60:
            score += 5  # +5 points
        
        # Limiter score à 100 maximum
        result['score'] = min(100, score)
        
        # Marquer signal comme VALIDE
        result['valid'] = True
        
        # Afficher validation finale
        print(f"\n🎯 SIGNAL VALIDÉ - Score: {result['score']}/100")
        print(f"{'='*60}\n")
        
        # Retourner résultat complet
        return result
    
    
    # ========================================================================
    # MÉTHODE : Scanner toute la watchlist
    # ========================================================================
    
    def scan_watchlist(self) -> List[Dict]:
        """
        Scanne TOUTES les actions de la watchlist
        
        Appelle scan_ticker() sur chaque action de watchlist_core + watchlist_secondary.
        Retourne liste des signaux valides triés par score.
        
        Returns:
            Liste de dictionnaires (un par signal valide)
            Triée par score décroissant (meilleur signal en premier)
        """
        
        # Affichage bannière scan watchlist
        print("\n" + "📡 "*30)
        print("SCAN WATCHLIST")
        print("📡 " * 30 + "\n")
        
        # Récupérer TOUS les tickers (core + secondary)
        all_tickers = self.watchlist_manager.get_all_tickers()
        
        print(f"📋 {len(all_tickers)} tickers à scanner\n")
        
        # Liste pour stocker signaux valides
        valid_signals = []
        
        # Boucle sur chaque ticker
        for i, ticker in enumerate(all_tickers, 1):
            # Afficher progression (ex: [1/50] Scan AAPL...)
            print(f"[{i}/{len(all_tickers)}] Scan {ticker}...", end=' ')
            
            try:
                # Scanner ce ticker
                result = self.scan_ticker(ticker)
                
                # Si signal valide
                if result['valid']:
                    # Ajouter à liste signaux
                    valid_signals.append(result)
                    print(f"✅ SIGNAL")
                    
                    # Envoyer notification Telegram (optionnel)
                    asyncio.run(
                        self.telegram.notify_signal_detected(
                            ticker,
                            result['pattern']['pattern'],
                            result['score']
                        )
                    )
                else:
                    # Pas de signal valide
                    print(f"❌")
                
                # Pause 1 seconde pour ne pas surcharger API
                time.sleep(1)
                
            except Exception as e:
                # En cas d'erreur : afficher et continuer
                print(f"❌ Erreur: {e}")
                continue
        
        # Trier signaux par score décroissant (meilleur en premier)
        valid_signals.sort(key=lambda x: x['score'], reverse=True)
        
        # Affichage résultats
        print(f"\n{'='*60}")
        print(f"📊 RÉSULTATS SCAN")
        print(f"{'='*60}")
        print(f"Signaux valides: {len(valid_signals)}/{len(all_tickers)}")
        
        # Si au moins 1 signal : afficher top 5
        if valid_signals:
            print(f"\nTop signaux:")
            for signal in valid_signals[:5]:
                ticker = signal['ticker']
                score = signal['score']
                pattern = signal['pattern']['pattern']
                print(f"   {ticker}: {score}/100 ({pattern})")
        
        print(f"{'='*60}\n")
        
        # Retourner liste signaux valides
        return valid_signals
    
    
    # ========================================================================
    # MÉTHODE : Exécuter un signal (ACHETER !)
    # ========================================================================
    
    def execute_signal(self, signal: Dict) -> bool:
        """
        Exécute un signal valide = Achète l'action !
        
        Appelle le trading_manager qui va :
        1. Calculer taille position (20% capital)
        2. Placer ordre bracket (entrée + SL + TP)
        3. Envoyer notification Telegram
        
        Args:
            signal: Dictionnaire signal validé (de scan_ticker)
        
        Returns:
            True si achat réussi, False sinon
        """
        
        ticker = signal['ticker']
        
        # Affichage bannière exécution
        print(f"\n{'='*60}")
        print(f"💰 EXÉCUTION {ticker}")
        print(f"{'='*60}\n")
        
        # Appeler trading_manager pour entrer en position
        success, trade_details = self.trading_manager.enter_position(
            ticker,
            signal['filters_passed']  # Passer détails filtres
        )
        
        if success:
            # Achat réussi
            print(f"✅ Position ouverte: {ticker}")
            return True
        else:
            # Achat échoué
            print(f"❌ Échec ouverture position: {ticker}")
            return False
    
    
    # ========================================================================
    # MÉTHODE : Un cycle complet de trading
    # ========================================================================
    
    def run_cycle(self):
        """
        Exécute UN cycle complet de trading
        
        Un cycle fait :
        1. Vérifier conditions marché (heures, marché haussier)
        2. Vérifier limites risque
        3. Surveiller positions ouvertes
        4. Scanner watchlist si capacité disponible
        5. Exécuter meilleur signal
        
        Cette méthode est appelée toutes les 5 minutes par run().
        """
        
        # Affichage bannière cycle
        print(f"\n{'🔄 '*30}")
        print(f"CYCLE TRADING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'🔄 ' * 30}\n")
        
        # ========================================================================
        # ÉTAPE 1 : VÉRIFIER CONDITIONS MARCHÉ
        # ========================================================================
        
        print("1️⃣ Vérification conditions marché...")
        
        # Vérifier heures de trading (pas weekend, pas avant 10h15)
        can_trade, reason = self.filters.filter_time()
        if not can_trade:
            # Hors heures trading : arrêter cycle
            print(f"   ❌ {reason}")
            return
        print(f"   ✅ Heures de trading")
        
        # Vérifier marché haussier (SPY/QQQ/VIX)
        can_trade, reason = self.filters.filter_market_emotion()
        if not can_trade:
            # Marché pas favorable : arrêter cycle
            print(f"   ❌ {reason}")
            return
        print(f"   ✅ Marché favorable")
        
        # ========================================================================
        # ÉTAPE 2 : VÉRIFIER LIMITES RISQUE
        # ========================================================================
        
        print("\n2️⃣ Vérification risque...")
        
        # Vérifier qu'on n'a pas dépassé limites pertes ou positions
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            # Limite atteinte : arrêter cycle + notifier
            print(f"   ❌ {reason}")
            asyncio.run(self.telegram.notify_pause(reason))
            return
        print(f"   ✅ Limites risque OK")
        
        # ========================================================================
        # ÉTAPE 3 : SURVEILLER POSITIONS OUVERTES
        # ========================================================================
        
        print("\n3️⃣ Surveillance positions ouvertes...")
        
        # Surveiller positions pour sorties urgentes
        # (news négatives, spread instable)
        self.trading_manager.monitor_open_positions()
        
        # Compter positions ouvertes
        open_count = len(self.risk_manager.get_open_positions())
        print(f"   📊 {open_count} position(s) ouverte(s)")
        
        # ========================================================================
        # ÉTAPE 4 : SCANNER WATCHLIST (si capacité disponible)
        # ========================================================================
        
        # Vérifier si on a encore de la capacité (< 5 positions)
        if open_count < self.risk_manager.positions.get('max_positions', 5):
            print("\n4️⃣ Scan watchlist...")
            
            # Scanner toute la watchlist
            signals = self.scan_watchlist()
            
            # ====================================================================
            # ÉTAPE 5 : EXÉCUTER MEILLEUR SIGNAL
            # ====================================================================
            
            if signals:
                # Prendre signal avec meilleur score
                best_signal = signals[0]
                
                print(f"\n5️⃣ Exécution meilleur signal: {best_signal['ticker']}")
                
                # Acheter !
                self.execute_signal(best_signal)
        else:
            # Capacité max atteinte : pas de nouveau scan
            print("\n4️⃣ Capacité max atteinte - Pas de nouveau scan")
    
    
    # ========================================================================
    # MÉTHODE : Lancer le bot en boucle continue
    # ========================================================================
    
    def run(self, interval_seconds: int = 300):
        """
        Lance le bot en boucle infinie
        
        Exécute run_cycle() toutes les X secondes (défaut 300 = 5 minutes).
        Tourne jusqu'à Ctrl+C ou erreur fatale.
        
        Args:
            interval_seconds: Délai entre cycles en secondes (défaut 300 = 5min)
        """
        
        # Marquer bot comme en cours d'exécution
        self.running = True
        
        # Affichage bannière démarrage
        print(f"\n{'🚀 '*30}")
        print(f"BOT DÉMARRÉ - Intervalle {interval_seconds}s")
        print(f"{'🚀 ' * 30}\n")
        
        # Envoyer notification Telegram de démarrage
        asyncio.run(
            self.telegram.send_message(
                f"🤖 **Bot démarré**\n\nMode: {'DRY RUN' if DRY_RUN_MODE else 'RÉEL'}\nIntervalle: {interval_seconds}s"
            )
        )
        
        try:
            # Se connecter à IBKR
            self.connect()
            
            # Compteur cycles
            cycle_count = 0
            
            # ====================================================================
            # BOUCLE INFINIE
            # ====================================================================
            
            while self.running:
                cycle_count += 1
                
                try:
                    # Exécuter un cycle complet
                    self.run_cycle()
                    
                except Exception as e:
                    # En cas d'erreur : logger + notifier + continuer
                    error_msg = f"Erreur cycle {cycle_count}: {str(e)}"
                    print(f"\n❌ {error_msg}\n")
                    asyncio.run(self.telegram.notify_error(error_msg))
                
                # Afficher message attente
                print(f"\n⏸️  Attente {interval_seconds}s avant prochain cycle...\n")
                
                # Pause avant prochain cycle
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            # Si utilisateur appuie sur Ctrl+C
            print(f"\n\n⛔ Arrêt demandé par utilisateur")
        
        finally:
            # Code exécuté dans TOUS les cas (arrêt normal ou erreur)
            
            # Marquer bot comme arrêté
            self.running = False
            
            # Se déconnecter d'IBKR
            self.disconnect()
            
            # ====================================================================
            # RÉSUMÉ FINAL
            # ====================================================================
            
            # Récupérer statistiques finales
            stats = self.risk_manager.get_statistics()
            
            print(f"\n{'📊 '*30}")
            print(f"RÉSUMÉ FINAL")
            print(f"{'📊 ' * 30}")
            print(f"Cycles: {cycle_count}")
            print(f"Trades: {stats.get('total_trades', 0)}")
            print(f"Win rate: {stats.get('win_rate', 0):.1f}%")
            print(f"PnL: ${stats.get('total_pnl', 0):+,.2f}")
            print(f"{'📊 ' * 30}\n")
            
            # Envoyer résumé par Telegram
            asyncio.run(
                self.telegram.notify_daily_summary(stats)
            )


# ============================================================================
# POINT D'ENTRÉE - Code exécuté quand on lance : python bot.py
# ============================================================================

if __name__ == '__main__':
    # Créer instance du bot avec capital 10000$
    bot = MomentumBot(capital=10000)
    
    # Récupérer arguments ligne de commande
    import sys
    
    # Vérifier si on a passé argument --scan-once
    if len(sys.argv) > 1 and sys.argv[1] == '--scan-once':
        # Mode scan unique : exécuter 1 seul cycle puis arrêter
        bot.connect()  # Se connecter
        try:
            bot.run_cycle()  # Exécuter 1 cycle
        finally:
            bot.disconnect()  # Se déconnecter
    else:
        # Mode normal : boucle continue (5 minutes par cycle)
        bot.run(interval_seconds=300)

