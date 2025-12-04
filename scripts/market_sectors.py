"""
Surveillance des secteurs via ETFs sectoriels
"""
from typing import Dict, List, Optional
import pandas as pd
from stock_data import StockDataProvider
from config import SECTOR_ETFS, SECTOR_MIN_CHANGE, MIN_VOLUME_MULTIPLIER


class MarketSectorsAnalyzer:
    """Analyseur des secteurs de marché"""
    
    def __init__(self, data_provider: StockDataProvider):
        self.data_provider = data_provider
    
    def get_sector_status(self, etf_symbol: str, sector_name: str = '') -> Optional[Dict]:
        """Analyse un secteur via son ETF"""
        try:
            df = self.data_provider.get_ohlcv(etf_symbol, interval='5 mins', duration='1 D')
            if df is None or df.empty:
                return None
            
            # Dernière bougie
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            
            # Variation
            change_pct = ((last['close'] - prev['close']) / prev['close']) * 100
            
            # Volume
            recent = df.tail(20)
            avg_volume = recent['volume'].mean()
            volume_ratio = last['volume'] / avg_volume if avg_volume > 0 else 0
            
            # Tendance
            sma_20 = recent['close'].mean()
            trend = 'bullish' if last['close'] > sma_20 else 'bearish'
            
            # Signal haussier
            is_bullish = (
                change_pct >= SECTOR_MIN_CHANGE * 100 and
                volume_ratio >= MIN_VOLUME_MULTIPLIER
            )
            
            return {
                'sector': sector_name or etf_symbol,
                'etf': etf_symbol,
                'price': last['close'],
                'change_pct': change_pct,
                'volume': last['volume'],
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'sma_20': sma_20,
                'trend': trend,
                'is_bullish': is_bullish
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse secteur {etf_symbol}: {e}")
            return None
    
    def get_all_sectors_status(self) -> Dict[str, Dict]:
        """Analyse tous les secteurs"""
        results = {}
        
        for sector_name, etf_symbol in SECTOR_ETFS.items():
            status = self.get_sector_status(etf_symbol, sector_name)
            if status:
                results[sector_name] = status
        
        return results
    
    def get_bullish_sectors(self) -> List[Dict]:
        """Retourne secteurs haussiers triés par force"""
        all_sectors = self.get_all_sectors_status()
        
        bullish = [
            sector_data for sector_data in all_sectors.values()
            if sector_data['is_bullish']
        ]
        
        # Trier par variation décroissante
        bullish.sort(key=lambda x: x['change_pct'], reverse=True)
        
        return bullish
    
    def is_sector_bullish(self, etf_symbol: str) -> bool:
        """Vérifie si un secteur spécifique est haussier"""
        status = self.get_sector_status(etf_symbol)
        if not status:
            return False
        return status['is_bullish']
    
    def get_sector_for_stock(self, ticker: str) -> Optional[str]:
        """
        Identifie le secteur d'une action
        (simplifié - nécessiterait API supplémentaire pour être précis)
        """
        # Mapping manuel basique (à améliorer avec API fondamentaux)
        tech_stocks = ['AAPL', 'MSFT', 'NVDA', 'AMD', 'META', 'GOOGL', 'AVGO', 'ADBE']
        consumer_stocks = ['AMZN', 'TSLA', 'HD', 'NKE', 'SBUX', 'MCD', 'LOW']
        healthcare_stocks = ['UNH', 'JNJ', 'LLY', 'ABBV', 'TMO']
        energy_stocks = ['XOM', 'CVX', 'COP', 'SLB']
        
        ticker = ticker.upper()
        
        if ticker in tech_stocks:
            return 'technology'
        elif ticker in consumer_stocks:
            return 'consumer_discretionary'
        elif ticker in healthcare_stocks:
            return 'healthcare'
        elif ticker in energy_stocks:
            return 'energy'
        else:
            return None
    
    def is_stock_sector_favorable(self, ticker: str) -> tuple[bool, str]:
        """
        Vérifie si le secteur de l'action est favorable
        
        Returns: (is_favorable, sector_name)
        """
        sector = self.get_sector_for_stock(ticker)
        
        if not sector:
            # Si secteur inconnu, on ne bloque pas
            return True, 'unknown'
        
        etf = SECTOR_ETFS.get(sector)
        if not etf:
            return True, sector
        
        is_favorable = self.is_sector_bullish(etf)
        
        return is_favorable, sector
    
    def get_sector_strength_score(self) -> int:
        """
        Score global de force des secteurs (0-100)
        
        Basé sur le % de secteurs haussiers
        """
        all_sectors = self.get_all_sectors_status()
        
        if not all_sectors:
            return 50
        
        bullish_count = sum(1 for s in all_sectors.values() if s['is_bullish'])
        total_count = len(all_sectors)
        
        score = int((bullish_count / total_count) * 100)
        
        return score


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST MARKET SECTORS ANALYZER")
    print("="*60 + "\n")
    
    from stock_data import StockDataProvider
    
    provider = StockDataProvider()
    analyzer = MarketSectorsAnalyzer(provider)
    
    try:
        provider.connect()
        
        # Analyse tous secteurs
        print("📊 Analyse secteurs:\n")
        all_sectors = analyzer.get_all_sectors_status()
        
        for sector_name, data in all_sectors.items():
            emoji = "✅" if data['is_bullish'] else "❌"
            print(f"{emoji} {sector_name.upper():<25} ({data['etf']})")
            print(f"   Prix: ${data['price']:.2f} | Var: {data['change_pct']:+.2f}%")
            print(f"   Volume ratio: {data['volume_ratio']:.2f}x | Tendance: {data['trend']}")
            print()
        
        # Secteurs haussiers
        bullish = analyzer.get_bullish_sectors()
        print(f"\n🚀 Secteurs haussiers ({len(bullish)}):")
        for sector in bullish:
            print(f"   • {sector['sector'].upper()} ({sector['etf']}): {sector['change_pct']:+.2f}%")
        
        # Score global
        score = analyzer.get_sector_strength_score()
        print(f"\n🎯 Score force secteurs: {score}/100")
        
        # Test action spécifique
        test_ticker = 'AAPL'
        is_favorable, sector = analyzer.is_stock_sector_favorable(test_ticker)
        print(f"\n🔍 {test_ticker}:")
        print(f"   Secteur: {sector}")
        print(f"   Favorable: {'✅ Oui' if is_favorable else '❌ Non'}")
        
    finally:
        provider.disconnect()

