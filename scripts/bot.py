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
from logger import (
    log_info, log_warning, log_error, log_trade, 
    log_signal, log_market_status, log_startup, 
    log_shutdown, log_cycle
)


class MomentumBot:
    """Bot principal de trading momentum"""
    
    def __init__(self, capital: float = 10000):
        log_info("=" * 60)
        log_info("🤖 BOT ACTIONS US MOMENTUM - INITIALISATION")
        log_info("=" * 60)
        
        # Initialisation des composants
        log_info("📦 Chargement modules...")
        
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
        self.cycle_count = 0
        
        log_info("✅ Modules chargés")
        
        # Stats
        stats = self.watchlist_manager.get_stats()
        log_startup(
            capital=capital,
            dry_run=DRY_RUN_MODE,
            paper=PAPER_TRADING_MODE,
            watchlist_count=stats['total_count']
        )
        log_info(f"📊 Blacklist: {stats['blacklist_count']} exclus")
    
    def connect(self):
        """Connexion IBKR"""
        log_info("🔌 Connexion IBKR...")
        self.data_provider.connect()
        log_info("✅ Connecté à IBKR")
    
    def disconnect(self):
        """Déconnexion"""
        log_info("🔌 Déconnexion...")
        self.data_provider.disconnect()
        log_info("✅ Déconnecté")
    
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
        log_info(f"🔍 SCAN {ticker}")
        
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
            log_info(f"   ❌ {ticker}: Filtres échoués ({len(failed)}): {', '.join(failed)}")
            return result
        
        log_info(f"   ✅ {ticker}: Filtres de base passés")
        
        # 2. Détection pattern chandelier
        df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')
        if df is not None and not df.empty:
            pattern = self.patterns.detect_bullish_pattern(df)
            if pattern:
                result['pattern'] = pattern
                log_info(f"   🕯️  {ticker}: Pattern {pattern['pattern']} ({pattern['confidence']}%)")
            else:
                log_info(f"   ❌ {ticker}: Pas de pattern haussier")
                return result
        else:
            log_warning(f"   ❌ {ticker}: Pas de données OHLCV")
            return result
        
        # 3. Validation volume du pattern
        last_candle = df.iloc[-1]
        recent = df.tail(20)
        avg_volume = recent['volume'].iloc[:-1].mean()
        
        is_volume_ok = self.patterns.validate_volume(last_candle, avg_volume)
        if not is_volume_ok:
            log_info(f"   ❌ {ticker}: Volume insuffisant")
            return result
        
        volume_ratio = last_candle['volume'] / avg_volume
        log_info(f"   ✅ {ticker}: Volume validé ({volume_ratio:.2f}x)")
        
        # 4. Détection breakout + orderflow
        is_breakout_valid, breakout_details = self.breakout_detector.validate_breakout_with_orderflow(ticker)
        result['breakout'] = breakout_details
        
        if not is_breakout_valid:
            reason = breakout_details.get('reason', 'Inconnu')
            log_info(f"   ❌ {ticker}: Breakout non validé - {reason}")
            return result
        
        log_info(f"   ✅ {ticker}: Breakout validé avec orderflow haussier")
        
        # 5. Calcul score global
        score = 0
        score += pattern['confidence']  # 70-90
        if breakout_details['breakout']['volume_ratio'] > 2.0:
            score += 10  # Bonus volume exceptionnel
        if breakout_details['orderflow']['bid_pressure'] > 60:
            score += 5  # Bonus pression acheteuse forte
        
        result['score'] = min(100, score)
        result['valid'] = True
        
        log_signal(ticker, pattern['pattern'], {
            'score': result['score'],
            'volume': f"{volume_ratio:.1f}x"
        })
        
        return result
    
    def scan_watchlist(self) -> List[Dict]:
        """Scan toute la watchlist"""
        log_info("=" * 60)
        log_info("📡 SCAN WATCHLIST")
        log_info("=" * 60)
        
        # Récupérer tous les tickers
        all_tickers = self.watchlist_manager.get_all_tickers()
        
        log_info(f"📋 {len(all_tickers)} tickers à scanner")
        
        valid_signals = []
        
        for i, ticker in enumerate(all_tickers, 1):
            try:
                result = self.scan_ticker(ticker)
                
                if result['valid']:
                    valid_signals.append(result)
                    
                    # Notification Telegram
                    asyncio.run(
                        self.telegram.notify_signal_detected(
                            ticker,
                            result['pattern']['pattern'],
                            result['score']
                        )
                    )
                
                time.sleep(1)  # Éviter rate limiting
                
            except Exception as e:
                log_error(f"Erreur scan {ticker}: {e}")
                continue
        
        # Trier par score
        valid_signals.sort(key=lambda x: x['score'], reverse=True)
        
        log_info(f"📊 RÉSULTATS: {len(valid_signals)}/{len(all_tickers)} signaux valides")
        
        if valid_signals:
            log_info("Top signaux:")
            for signal in valid_signals[:5]:
                ticker = signal['ticker']
                score = signal['score']
                pattern = signal['pattern']['pattern']
                log_info(f"   {ticker}: {score}/100 ({pattern})")
        
        return valid_signals
    
    def execute_signal(self, signal: Dict) -> bool:
        """Exécute un signal validé"""
        ticker = signal['ticker']
        
        log_info(f"💰 EXÉCUTION {ticker}")
        
        success, trade_details = self.trading_manager.enter_position(
            ticker,
            signal['filters_passed']
        )
        
        if success:
            price = trade_details.get('entry_price', 0)
            quantity = trade_details.get('quantity', 0)
            log_trade("BUY", ticker, price, quantity, reason=f"Score: {signal['score']}")
            return True
        else:
            log_warning(f"Échec ouverture position: {ticker}")
            return False
    
    def run_cycle(self):
        """Un cycle complet de trading"""
        self.cycle_count += 1
        
        log_info("=" * 60)
        log_info(f"🔄 CYCLE #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_info("=" * 60)
        
        # 1. Vérifier conditions marché
        log_info("1️⃣ Vérification conditions marché...")
        can_trade, reason = self.filters.filter_time()
        if not can_trade:
            log_info(f"   ❌ {reason}")
            return
        log_info("   ✅ Heures de trading OK")
        
        can_trade, reason = self.filters.filter_market_emotion()
        if not can_trade:
            log_info(f"   ❌ {reason}")
            return
        log_info("   ✅ Marché favorable")
        
        # 2. Vérifier limites risque
        log_info("2️⃣ Vérification risque...")
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            log_warning(f"Limite risque atteinte: {reason}")
            asyncio.run(self.telegram.notify_pause(reason))
            return
        log_info("   ✅ Limites risque OK")
        
        # 3. Surveiller positions ouvertes
        log_info("3️⃣ Surveillance positions ouvertes...")
        self.trading_manager.monitor_open_positions()
        open_count = len(self.risk_manager.get_open_positions())
        log_info(f"   📊 {open_count} position(s) ouverte(s)")
        
        # 4. Scanner watchlist si capacité disponible
        opportunities = 0
        if open_count < self.risk_manager.positions.get('max_positions', 5):
            log_info("4️⃣ Scan watchlist...")
            signals = self.scan_watchlist()
            opportunities = len(signals)
            
            # 5. Exécuter meilleur signal
            if signals:
                best_signal = signals[0]
                log_info(f"5️⃣ Exécution meilleur signal: {best_signal['ticker']}")
                self.execute_signal(best_signal)
        else:
            log_info("4️⃣ Capacité max atteinte - Pas de nouveau scan")
        
        log_cycle(self.cycle_count, opportunities, open_count)
    
    def run(self, interval_seconds: int = 300):
        """
        Lance le bot en boucle
        
        Args:
            interval_seconds: Intervalle entre cycles (défaut 300 = 5min)
        """
        self.running = True
        
        log_info("🚀 " * 20)
        log_info(f"BOT DÉMARRÉ - Intervalle {interval_seconds}s")
        log_info("🚀 " * 20)
        
        asyncio.run(
            self.telegram.send_message(
                f"🤖 **Bot démarré**\n\nMode: {'DRY RUN' if DRY_RUN_MODE else 'RÉEL'}\nIntervalle: {interval_seconds}s"
            )
        )
        
        try:
            self.connect()
            
            while self.running:
                try:
                    self.run_cycle()
                except Exception as e:
                    log_error(f"Erreur cycle {self.cycle_count}: {str(e)}")
                    asyncio.run(self.telegram.notify_error(str(e)))
                
                # Attendre prochain cycle
                log_info(f"⏸️  Attente {interval_seconds}s avant prochain cycle...")
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            log_warning("Arrêt demandé par utilisateur (Ctrl+C)")
        
        finally:
            self.running = False
            self.disconnect()
            
            # Résumé final
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
