"""
Analyse des indices majeurs : SPY, QQQ, VIX
"""
from typing import Dict, Optional
import pandas as pd
from stock_data import StockDataProvider
from config import VIX_MAX_LEVEL, SPY_MIN_CHANGE, QQQ_MIN_CHANGE


class MarketIndicesAnalyzer:
    """Analyseur des indices de marché"""
    
    def __init__(self, data_provider: StockDataProvider):
        self.data_provider = data_provider
    
    def get_spy_status(self) -> Optional[Dict]:
        """Analyse tendance SPY"""
        try:
            df = self.data_provider.get_ohlcv('SPY', interval='5 mins', duration='1 D')
            if df is None or df.empty:
                return None
            
            # Dernière bougie
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            
            # Variation
            change_pct = ((last['close'] - prev['close']) / prev['close']) * 100
            
            # Tendance (sur 20 dernières bougies)
            recent = df.tail(20)
            sma_20 = recent['close'].mean()
            trend = 'bullish' if last['close'] > sma_20 else 'bearish'
            
            # Signal
            is_bullish = change_pct >= SPY_MIN_CHANGE * 100
            
            return {
                'ticker': 'SPY',
                'price': last['close'],
                'change_pct': change_pct,
                'volume': last['volume'],
                'sma_20': sma_20,
                'trend': trend,
                'is_bullish': is_bullish
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse SPY: {e}")
            return None
    
    def get_qqq_status(self) -> Optional[Dict]:
        """Analyse tendance QQQ"""
        try:
            df = self.data_provider.get_ohlcv('QQQ', interval='5 mins', duration='1 D')
            if df is None or df.empty:
                return None
            
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            
            change_pct = ((last['close'] - prev['close']) / prev['close']) * 100
            
            recent = df.tail(20)
            sma_20 = recent['close'].mean()
            trend = 'bullish' if last['close'] > sma_20 else 'bearish'
            
            is_bullish = change_pct >= QQQ_MIN_CHANGE * 100
            
            return {
                'ticker': 'QQQ',
                'price': last['close'],
                'change_pct': change_pct,
                'volume': last['volume'],
                'sma_20': sma_20,
                'trend': trend,
                'is_bullish': is_bullish
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse QQQ: {e}")
            return None
    
    def get_vix_level(self) -> Optional[Dict]:
        """Analyse niveau VIX"""
        try:
            price_data = self.data_provider.get_current_price('VIX')
            if not price_data:
                return None
            
            vix_level = price_data['last']
            
            # Interprétation
            if vix_level < 15:
                mood = 'très calme'
                color = '🟢'
            elif vix_level < 20:
                mood = 'calme'
                color = '🟢'
            elif vix_level < 25:
                mood = 'normal'
                color = '🟡'
            elif vix_level < 30:
                mood = 'nerveux'
                color = '🟠'
            else:
                mood = 'panique'
                color = '🔴'
            
            is_favorable = vix_level < VIX_MAX_LEVEL
            
            return {
                'ticker': 'VIX',
                'level': vix_level,
                'mood': mood,
                'color': color,
                'is_favorable': is_favorable
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse VIX: {e}")
            return None
    
    def is_market_bullish(self) -> tuple[bool, Dict]:
        """
        Validation marché haussier
        
        Conditions:
        - SPY haussier (>= 0.3%)
        - QQQ haussier (>= 0.3%)
        - VIX < 25
        
        Returns: (is_bullish, details)
        """
        try:
            spy = self.get_spy_status()
            qqq = self.get_qqq_status()
            vix = self.get_vix_level()
            
            if not all([spy, qqq, vix]):
                return False, {'error': 'Données manquantes'}
            
            conditions = {
                'spy_bullish': spy['is_bullish'],
                'qqq_bullish': qqq['is_bullish'],
                'vix_favorable': vix['is_favorable']
            }
            
            is_bullish = all(conditions.values())
            
            details = {
                'spy': spy,
                'qqq': qqq,
                'vix': vix,
                'conditions': conditions,
                'is_bullish': is_bullish
            }
            
            return is_bullish, details
            
        except Exception as e:
            print(f"❌ Erreur validation marché: {e}")
            return False, {'error': str(e)}
    
    def get_market_score(self) -> int:
        """
        Score de marché 0-100
        
        100 = très haussier
        0 = très baissier
        """
        try:
            is_bullish, details = self.is_market_bullish()
            
            if 'error' in details:
                return 50  # Neutre si erreur
            
            spy = details['spy']
            qqq = details['qqq']
            vix = details['vix']
            
            score = 50  # Base neutre
            
            # SPY contribution (0-25 points)
            if spy['is_bullish']:
                score += 25
            elif spy['change_pct'] > 0:
                score += 15
            elif spy['change_pct'] < -0.5:
                score -= 20
            
            # QQQ contribution (0-25 points)
            if qqq['is_bullish']:
                score += 25
            elif qqq['change_pct'] > 0:
                score += 15
            elif qqq['change_pct'] < -0.5:
                score -= 20
            
            # VIX contribution (-20 à 0 points)
            if vix['level'] < 15:
                score += 0
            elif vix['level'] < 20:
                score -= 5
            elif vix['level'] < 25:
                score -= 10
            elif vix['level'] < 30:
                score -= 15
            else:
                score -= 25
            
            # Clamp 0-100
            score = max(0, min(100, score))
            
            return score
            
        except Exception as e:
            print(f"❌ Erreur calcul score marché: {e}")
            return 50


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST MARKET INDICES ANALYZER")
    print("="*60 + "\n")
    
    from stock_data import StockDataProvider
    
    provider = StockDataProvider()
    analyzer = MarketIndicesAnalyzer(provider)
    
    try:
        provider.connect()
        
        # SPY
        print("📊 SPY:")
        spy = analyzer.get_spy_status()
        if spy:
            print(f"   Prix: ${spy['price']:.2f}")
            print(f"   Variation: {spy['change_pct']:+.2f}%")
            print(f"   Tendance: {spy['trend']}")
            print(f"   Signal: {'✅ Haussier' if spy['is_bullish'] else '❌ Non haussier'}")
        
        # QQQ
        print(f"\n📊 QQQ:")
        qqq = analyzer.get_qqq_status()
        if qqq:
            print(f"   Prix: ${qqq['price']:.2f}")
            print(f"   Variation: {qqq['change_pct']:+.2f}%")
            print(f"   Tendance: {qqq['trend']}")
            print(f"   Signal: {'✅ Haussier' if qqq['is_bullish'] else '❌ Non haussier'}")
        
        # VIX
        print(f"\n📊 VIX:")
        vix = analyzer.get_vix_level()
        if vix:
            print(f"   Niveau: {vix['level']:.2f}")
            print(f"   Humeur: {vix['color']} {vix['mood']}")
            print(f"   Favorable: {'✅ Oui' if vix['is_favorable'] else '❌ Non'}")
        
        # Validation globale
        print(f"\n🎯 Validation marché:")
        is_bullish, details = analyzer.is_market_bullish()
        score = analyzer.get_market_score()
        
        print(f"   Marché haussier: {'✅ OUI' if is_bullish else '❌ NON'}")
        print(f"   Score: {score}/100")
        
        if 'conditions' in details:
            print(f"\n   Conditions:")
            for cond, status in details['conditions'].items():
                emoji = "✅" if status else "❌"
                print(f"      {emoji} {cond}")
        
    finally:
        provider.disconnect()

