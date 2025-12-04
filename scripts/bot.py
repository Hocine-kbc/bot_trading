"""
BOT TRADING ACTIONS US MOMENTUM
Stratégie: +20% Take Profit / -5% Stop Loss

Orchestre tous les modules et exécute la stratégie complète
"""
import time
import asyncio
from datetime import datetime
from typing import List, Dict

# Imports modules
from config import DRY_RUN_MODE, PAPER_TRADING_MODE
from stock_data import StockDataProvider
from watchlist_manager import WatchlistManager
from news_monitor import NewsMonitor
from market_indices import MarketIndicesAnalyzer
from market_sectors import MarketSectorsAnalyzer
from filters import TradingFilters
from candlestick_patterns import CandlestickPatterns
from breakout_detector import BreakoutDetector
from risk_manager import RiskManager
from trading_manager import TradingManager
from telegram_notifier import TelegramNotifier


class MomentumBot:
    """Bot principal de trading momentum"""
    
    def __init__(self, capital: float = 10000):
        print("\n" + "🤖 "*30)
        print("BOT ACTIONS US MOMENTUM - INITIALISATION")
        print("🤖 " * 30 + "\n")
        
        # Initialisation des composants
        print("📦 Chargement modules...")
        
        self.data_provider = StockDataProvider()
        self.watchlist_manager = WatchlistManager()
        self.news_monitor = NewsMonitor()
        self.market_analyzer = MarketIndicesAnalyzer(self.data_provider)
        self.sector_analyzer = MarketSectorsAnalyzer(self.data_provider)
        self.risk_manager = RiskManager(capital)
        self.telegram = TelegramNotifier()
        
        self.filters = TradingFilters(
            self.data_provider,
            self.watchlist_manager,
            self.news_monitor,
            self.market_analyzer,
            self.sector_analyzer
        )
        
        self.patterns = CandlestickPatterns()
        self.breakout_detector = BreakoutDetector(self.data_provider)
        
        self.trading_manager = TradingManager(
            self.data_provider,
            self.risk_manager,
            self.telegram,
            self.news_monitor
        )
        
        self.running = False
        
        print("✅ Modules chargés\n")
        
        # Stats
        stats = self.watchlist_manager.get_stats()
        print(f"📊 Configuration:")
        print(f"   Capital: ${capital:,.2f}")
        print(f"   Mode: {'🧪 DRY RUN' if DRY_RUN_MODE else '💰 RÉEL'}")
        print(f"   Paper Trading: {'✅' if PAPER_TRADING_MODE else '❌'}")
        print(f"   Watchlist: {stats['total_count']} actions")
        print(f"   Blacklist: {stats['blacklist_count']} exclus")
        print()
    
    def connect(self):
        """Connexion IBKR"""
        print("🔌 Connexion IBKR...")
        self.data_provider.connect()
        print("✅ Connecté\n")
    
    def disconnect(self):
        """Déconnexion"""
        print("\n🔌 Déconnexion...")
        self.data_provider.disconnect()
        print("✅ Déconnecté")
    
    def scan_ticker(self, ticker: str) -> Dict:
        """
        Scan complet d'un ticker
        
        Returns: {
            'ticker': str,
            'valid': bool,
            'filters_passed': dict,
            'pattern': dict or None,
            'breakout': dict or None,
            'score': int
        }
        """
        print(f"\n{'='*60}")
        print(f"🔍 SCAN {ticker}")
        print(f"{'='*60}\n")
        
        result = {
            'ticker': ticker,
            'valid': False,
            'filters_passed': {},
            'pattern': None,
            'breakout': None,
            'score': 0
        }
        
        # 1. Validation filtres de base
        all_passed, filters_results = self.filters.validate_all_filters(ticker)
        result['filters_passed'] = filters_results
        
        if not all_passed:
            failed = self.filters.get_failed_filters(filters_results)
            print(f"❌ Filtres échoués ({len(failed)}):")
            for f in failed:
                print(f"   • {f}")
            return result
        
        print(f"✅ Tous les filtres de base passés")
        
        # 2. Détection pattern chandelier
        df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')
        if df is not None and not df.empty:
            pattern = self.patterns.detect_bullish_pattern(df)
            if pattern:
                result['pattern'] = pattern
                print(f"🕯️  Pattern: {pattern['pattern']} ({pattern['confidence']}%)")
            else:
                print(f"❌ Pas de pattern haussier détecté")
                return result
        else:
            print(f"❌ Pas de données OHLCV")
            return result
        
        # 3. Validation volume du pattern
        last_candle = df.iloc[-1]
        recent = df.tail(20)
        avg_volume = recent['volume'].iloc[:-1].mean()
        
        is_volume_ok = self.patterns.validate_volume(last_candle, avg_volume)
        if not is_volume_ok:
            print(f"❌ Volume insuffisant pour pattern")
            return result
        
        print(f"✅ Volume validé ({last_candle['volume']/avg_volume:.2f}x)")
        
        # 4. Détection breakout + orderflow
        is_breakout_valid, breakout_details = self.breakout_detector.validate_breakout_with_orderflow(ticker)
        result['breakout'] = breakout_details
        
        if not is_breakout_valid:
            reason = breakout_details.get('reason', 'Inconnu')
            print(f"❌ Breakout non validé: {reason}")
            return result
        
        print(f"✅ Breakout validé avec orderflow haussier")
        
        # 5. Calcul score global
        score = 0
        score += pattern['confidence']  # 70-90
        if breakout_details['breakout']['volume_ratio'] > 2.0:
            score += 10  # Bonus volume exceptionnel
        if breakout_details['orderflow']['bid_pressure'] > 60:
            score += 5  # Bonus pression acheteuse forte
        
        result['score'] = min(100, score)
        result['valid'] = True
        
        print(f"\n🎯 SIGNAL VALIDÉ - Score: {result['score']}/100")
        print(f"{'='*60}\n")
        
        return result
    
    def scan_watchlist(self) -> List[Dict]:
        """Scan toute la watchlist"""
        print("\n" + "📡 "*30)
        print("SCAN WATCHLIST")
        print("📡 " * 30 + "\n")
        
        # Récupérer tous les tickers
        all_tickers = self.watchlist_manager.get_all_tickers()
        
        print(f"📋 {len(all_tickers)} tickers à scanner\n")
        
        valid_signals = []
        
        for i, ticker in enumerate(all_tickers, 1):
            print(f"[{i}/{len(all_tickers)}] Scan {ticker}...", end=' ')
            
            try:
                result = self.scan_ticker(ticker)
                
                if result['valid']:
                    valid_signals.append(result)
                    print(f"✅ SIGNAL")
                    
                    # Notification optionnelle
                    asyncio.run(
                        self.telegram.notify_signal_detected(
                            ticker,
                            result['pattern']['pattern'],
                            result['score']
                        )
                    )
                else:
                    print(f"❌")
                
                time.sleep(1)  # Éviter rate limiting
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
                continue
        
        # Trier par score
        valid_signals.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n{'='*60}")
        print(f"📊 RÉSULTATS SCAN")
        print(f"{'='*60}")
        print(f"Signaux valides: {len(valid_signals)}/{len(all_tickers)}")
        
        if valid_signals:
            print(f"\nTop signaux:")
            for signal in valid_signals[:5]:
                ticker = signal['ticker']
                score = signal['score']
                pattern = signal['pattern']['pattern']
                print(f"   {ticker}: {score}/100 ({pattern})")
        
        print(f"{'='*60}\n")
        
        return valid_signals
    
    def execute_signal(self, signal: Dict) -> bool:
        """Exécute un signal validé"""
        ticker = signal['ticker']
        
        print(f"\n{'='*60}")
        print(f"💰 EXÉCUTION {ticker}")
        print(f"{'='*60}\n")
        
        success, trade_details = self.trading_manager.enter_position(
            ticker,
            signal['filters_passed']
        )
        
        if success:
            print(f"✅ Position ouverte: {ticker}")
            return True
        else:
            print(f"❌ Échec ouverture position: {ticker}")
            return False
    
    def run_cycle(self):
        """Un cycle complet de trading"""
        print(f"\n{'🔄 '*30}")
        print(f"CYCLE TRADING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'🔄 ' * 30}\n")
        
        # 1. Vérifier conditions marché
        print("1️⃣ Vérification conditions marché...")
        can_trade, reason = self.filters.filter_time()
        if not can_trade:
            print(f"   ❌ {reason}")
            return
        print(f"   ✅ Heures de trading")
        
        can_trade, reason = self.filters.filter_market_emotion()
        if not can_trade:
            print(f"   ❌ {reason}")
            return
        print(f"   ✅ Marché favorable")
        
        # 2. Vérifier limites risque
        print("\n2️⃣ Vérification risque...")
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            print(f"   ❌ {reason}")
            asyncio.run(self.telegram.notify_pause(reason))
            return
        print(f"   ✅ Limites risque OK")
        
        # 3. Surveiller positions ouvertes
        print("\n3️⃣ Surveillance positions ouvertes...")
        self.trading_manager.monitor_open_positions()
        open_count = len(self.risk_manager.get_open_positions())
        print(f"   📊 {open_count} position(s) ouverte(s)")
        
        # 4. Scanner watchlist si capacité disponible
        if open_count < self.risk_manager.positions.get('max_positions', 5):
            print("\n4️⃣ Scan watchlist...")
            signals = self.scan_watchlist()
            
            # 5. Exécuter meilleur signal
            if signals:
                best_signal = signals[0]
                print(f"\n5️⃣ Exécution meilleur signal: {best_signal['ticker']}")
                self.execute_signal(best_signal)
        else:
            print("\n4️⃣ Capacité max atteinte - Pas de nouveau scan")
    
    def run(self, interval_seconds: int = 300):
        """
        Lance le bot en boucle
        
        Args:
            interval_seconds: Intervalle entre cycles (défaut 300 = 5min)
        """
        self.running = True
        
        print(f"\n{'🚀 '*30}")
        print(f"BOT DÉMARRÉ - Intervalle {interval_seconds}s")
        print(f"{'🚀 ' * 30}\n")
        
        asyncio.run(
            self.telegram.send_message(
                f"🤖 **Bot démarré**\n\nMode: {'DRY RUN' if DRY_RUN_MODE else 'RÉEL'}\nIntervalle: {interval_seconds}s"
            )
        )
        
        try:
            self.connect()
            
            cycle_count = 0
            
            while self.running:
                cycle_count += 1
                
                try:
                    self.run_cycle()
                except Exception as e:
                    error_msg = f"Erreur cycle {cycle_count}: {str(e)}"
                    print(f"\n❌ {error_msg}\n")
                    asyncio.run(self.telegram.notify_error(error_msg))
                
                # Attendre prochain cycle
                print(f"\n⏸️  Attente {interval_seconds}s avant prochain cycle...\n")
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print(f"\n\n⛔ Arrêt demandé par utilisateur")
        
        finally:
            self.running = False
            self.disconnect()
            
            # Résumé final
            stats = self.risk_manager.get_statistics()
            print(f"\n{'📊 '*30}")
            print(f"RÉSUMÉ FINAL")
            print(f"{'📊 ' * 30}")
            print(f"Cycles: {cycle_count}")
            print(f"Trades: {stats.get('total_trades', 0)}")
            print(f"Win rate: {stats.get('win_rate', 0):.1f}%")
            print(f"PnL: ${stats.get('total_pnl', 0):+,.2f}")
            print(f"{'📊 ' * 30}\n")
            
            asyncio.run(
                self.telegram.notify_daily_summary(stats)
            )


if __name__ == '__main__':
    # Lancement du bot
    bot = MomentumBot(capital=10000)
    
    # Mode: scan unique ou boucle continue
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--scan-once':
        # Un seul scan
        bot.connect()
        try:
            bot.run_cycle()
        finally:
            bot.disconnect()
    else:
        # Boucle continue (5 minutes par cycle)
        bot.run(interval_seconds=300)

