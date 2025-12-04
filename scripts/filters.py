"""
Tous les filtres de trading regroupés
"""
from typing import Dict, Optional
import pandas as pd
from filters_time import TimeFilters
from news_monitor import NewsMonitor
from market_indices import MarketIndicesAnalyzer
from market_sectors import MarketSectorsAnalyzer
from stock_data import StockDataProvider
from watchlist_manager import WatchlistManager
from config import (
    DOJI_BODY_PCT,
    HIGH_WICK_PCT,
    MIN_VOLUME_MULTIPLIER,
    SPREAD_MAX_PCT
)


class TradingFilters:
    """Ensemble complet des filtres de trading"""
    
    def __init__(
        self,
        data_provider: StockDataProvider,
        watchlist_manager: WatchlistManager,
        news_monitor: NewsMonitor,
        market_analyzer: MarketIndicesAnalyzer,
        sector_analyzer: MarketSectorsAnalyzer
    ):
        self.data_provider = data_provider
        self.watchlist_manager = watchlist_manager
        self.news_monitor = news_monitor
        self.market_analyzer = market_analyzer
        self.sector_analyzer = sector_analyzer
        self.time_filters = TimeFilters()
    
    def filter_watchlist(self, ticker: str) -> tuple[bool, str]:
        """Filtre: Action dans watchlist et non blacklistée"""
        return self.watchlist_manager.can_trade(ticker)
    
    def filter_time(self) -> tuple[bool, str]:
        """Filtre: Horaires de trading valides"""
        return self.time_filters.can_trade_now()
    
    def filter_earnings(self, ticker: str, hours: int = 48) -> tuple[bool, str]:
        """Filtre: Pas d'earnings dans les X heures"""
        has_earnings, info = self.news_monitor.has_earnings_soon(ticker, hours)
        
        if has_earnings:
            return False, f"Earnings dans {info['hours_until']:.1f}h"
        
        return True, "OK"
    
    def filter_market_emotion(self) -> tuple[bool, str]:
        """
        Filtre: Émotions marché favorables
        
        Conditions:
        - SPY haussier
        - QQQ haussier
        - VIX < 25
        """
        is_bullish, details = self.market_analyzer.is_market_bullish()
        
        if not is_bullish:
            if 'error' in details:
                return False, f"Erreur données marché: {details['error']}"
            
            conditions = details.get('conditions', {})
            failed = [k for k, v in conditions.items() if not v]
            return False, f"Marché non favorable: {', '.join(failed)}"
        
        return True, "OK"
    
    def filter_sector_emotion(self, ticker: str) -> tuple[bool, str]:
        """
        Filtre: Secteur de l'action est haussier
        
        Conditions:
        - ETF secteur > 0.5%
        - Volume ETF > moyenne
        """
        is_favorable, sector = self.sector_analyzer.is_stock_sector_favorable(ticker)
        
        if not is_favorable:
            return False, f"Secteur {sector} non haussier"
        
        return True, f"Secteur {sector} favorable"
    
    def filter_stock_emotion(self, ticker: str) -> tuple[bool, str]:
        """
        Filtre: Émotions action (pas de doji, pas mèche haute)
        
        Conditions interdites:
        - Doji (body < 20% range)
        - Mèche haute > 50% range
        - Volume < 50% moyenne
        """
        try:
            df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')
            if df is None or df.empty:
                return False, "Pas de données"
            
            last = df.iloc[-1]
            
            # Vérifier doji
            body = abs(last['close'] - last['open'])
            total_range = last['high'] - last['low']
            
            if total_range == 0:
                return False, "Range nulle (suspect)"
            
            body_pct = body / total_range
            
            if body_pct < DOJI_BODY_PCT:
                return False, f"Doji détecté (body {body_pct*100:.1f}%)"
            
            # Vérifier mèche haute
            upper_shadow = last['high'] - max(last['open'], last['close'])
            upper_shadow_pct = upper_shadow / total_range
            
            if upper_shadow_pct > HIGH_WICK_PCT:
                return False, f"Mèche haute excessive ({upper_shadow_pct*100:.1f}%)"
            
            # Vérifier volume
            recent = df.tail(20)
            avg_volume = recent['volume'].iloc[:-1].mean()
            
            if last['volume'] < avg_volume * 0.5:
                return False, f"Volume faible ({last['volume']/avg_volume*100:.0f}% moy)"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def filter_negative_news(self, ticker: str, minutes: int = 30) -> tuple[bool, str]:
        """Filtre: Pas de news négatives récentes"""
        has_negative, news_list = self.news_monitor.has_negative_news(ticker, minutes)
        
        if has_negative:
            return False, f"{len(news_list)} news négative(s) récente(s)"
        
        return True, "OK"
    
    def filter_downgrade(self, ticker: str, days: int = 1) -> tuple[bool, str]:
        """Filtre: Pas de downgrade récent"""
        has_downgrade, downgrades = self.news_monitor.has_recent_downgrade(ticker, days)
        
        if has_downgrade:
            return False, f"{len(downgrades)} downgrade(s) récent(s)"
        
        return True, "OK"
    
    def filter_spread(self, ticker: str) -> tuple[bool, str]:
        """Filtre: Spread bid-ask acceptable"""
        try:
            orderflow = self.data_provider.get_orderflow(ticker)
            if not orderflow:
                return False, "Pas de données orderflow"
            
            spread_pct = orderflow['spread_pct']
            
            if spread_pct > SPREAD_MAX_PCT * 100:
                return False, f"Spread trop large ({spread_pct:.2f}%)"
            
            return True, f"Spread OK ({spread_pct:.2f}%)"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def validate_all_filters(self, ticker: str) -> tuple[bool, Dict]:
        """
        Validation COMPLÈTE de tous les filtres
        
        Returns: (all_passed, results_dict)
        """
        results = {}
        
        # 1. Watchlist & Blacklist
        passed, reason = self.filter_watchlist(ticker)
        results['watchlist'] = {'passed': passed, 'reason': reason}
        
        # 2. Horaires
        passed, reason = self.filter_time()
        results['time'] = {'passed': passed, 'reason': reason}
        
        # 3. Earnings
        passed, reason = self.filter_earnings(ticker)
        results['earnings'] = {'passed': passed, 'reason': reason}
        
        # 4. Marché
        passed, reason = self.filter_market_emotion()
        results['market'] = {'passed': passed, 'reason': reason}
        
        # 5. Secteur
        passed, reason = self.filter_sector_emotion(ticker)
        results['sector'] = {'passed': passed, 'reason': reason}
        
        # 6. Action
        passed, reason = self.filter_stock_emotion(ticker)
        results['stock'] = {'passed': passed, 'reason': reason}
        
        # 7. News négatives
        passed, reason = self.filter_negative_news(ticker)
        results['negative_news'] = {'passed': passed, 'reason': reason}
        
        # 8. Downgrade
        passed, reason = self.filter_downgrade(ticker)
        results['downgrade'] = {'passed': passed, 'reason': reason}
        
        # 9. Spread
        passed, reason = self.filter_spread(ticker)
        results['spread'] = {'passed': passed, 'reason': reason}
        
        # Tous passés ?
        all_passed = all(r['passed'] for r in results.values())
        
        return all_passed, results
    
    def get_failed_filters(self, results: Dict) -> list:
        """Retourne liste des filtres échoués"""
        failed = [
            f"{name}: {data['reason']}"
            for name, data in results.items()
            if not data['passed']
        ]
        return failed


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST TRADING FILTERS")
    print("="*60 + "\n")
    
    from stock_data import StockDataProvider
    from watchlist_manager import WatchlistManager
    from news_monitor import NewsMonitor
    from market_indices import MarketIndicesAnalyzer
    from market_sectors import MarketSectorsAnalyzer
    
    # Initialisation
    provider = StockDataProvider()
    watchlist_mgr = WatchlistManager()
    news_mon = NewsMonitor()
    market_analyzer = MarketIndicesAnalyzer(provider)
    sector_analyzer = MarketSectorsAnalyzer(provider)
    
    filters = TradingFilters(
        provider,
        watchlist_mgr,
        news_mon,
        market_analyzer,
        sector_analyzer
    )
    
    test_ticker = 'AAPL'
    
    try:
        provider.connect()
        
        print(f"🔍 Validation filtres pour {test_ticker}:\n")
        
        all_passed, results = filters.validate_all_filters(test_ticker)
        
        for filter_name, data in results.items():
            emoji = "✅" if data['passed'] else "❌"
            print(f"{emoji} {filter_name:<20} {data['reason']}")
        
        print("\n" + "="*60)
        if all_passed:
            print(f"🎉 TOUS LES FILTRES PASSÉS - {test_ticker} VALIDÉ")
        else:
            failed = filters.get_failed_filters(results)
            print(f"⛔ {len(failed)} FILTRE(S) ÉCHOUÉ(S):")
            for f in failed:
                print(f"   • {f}")
        print("="*60)
        
    finally:
        provider.disconnect()

