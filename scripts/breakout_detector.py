"""
Détection de breakouts avec validation volume et orderflow
"""
import pandas as pd
from typing import Optional, Dict
from stock_data import StockDataProvider
from config import BREAKOUT_VOLUME_MULTIPLIER, SPREAD_MAX_PCT


class BreakoutDetector:
    """Détecteur de breakouts techniques"""
    
    def __init__(self, data_provider: StockDataProvider):
        self.data_provider = data_provider
    
    def detect_breakout(self, ticker: str, periods: int = 20) -> tuple[bool, Optional[Dict]]:
        """
        Détecte breakout de résistance
        
        Conditions:
        - Prix clôture > high des N dernières bougies
        - Chandelier vert (close > open)
        - Volume >= 150% moyenne
        
        Returns: (is_breakout, details)
        """
        try:
            df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')
            if df is None or df.empty or len(df) < periods + 1:
                return False, None
            
            # Dernière bougie
            last = df.iloc[-1]
            
            # Bougies précédentes (pour résistance)
            recent = df.iloc[-periods-1:-1]
            
            # Résistance = max des highs
            resistance = recent['high'].max()
            
            # Volume moyen
            avg_volume = recent['volume'].mean()
            
            # Conditions breakout
            is_above_resistance = last['close'] > resistance
            is_green_candle = last['close'] > last['open']
            volume_ratio = last['volume'] / avg_volume if avg_volume > 0 else 0
            is_high_volume = volume_ratio >= BREAKOUT_VOLUME_MULTIPLIER
            
            is_breakout = is_above_resistance and is_green_candle and is_high_volume
            
            details = {
                'ticker': ticker,
                'current_price': last['close'],
                'resistance': resistance,
                'breakout_pct': ((last['close'] - resistance) / resistance) * 100,
                'is_green': is_green_candle,
                'volume': last['volume'],
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'is_breakout': is_breakout
            }
            
            return is_breakout, details
            
        except Exception as e:
            print(f"❌ Erreur détection breakout {ticker}: {e}")
            return False, None
    
    def is_orderflow_bullish(self, ticker: str) -> tuple[bool, Optional[Dict]]:
        """
        Valide orderflow haussier
        
        Conditions:
        - Bid size > Ask size (pression acheteuse)
        - Spread acceptable (< 0.5%)
        
        Returns: (is_bullish, orderflow_data)
        """
        try:
            orderflow = self.data_provider.get_orderflow(ticker)
            if not orderflow:
                return False, None
            
            # Pression acheteuse (bid > 55%)
            bid_pressure = orderflow['bid_pressure']
            is_bid_dominant = bid_pressure > 55
            
            # Spread acceptable
            spread_pct = orderflow['spread_pct']
            is_spread_ok = spread_pct < SPREAD_MAX_PCT * 100
            
            is_bullish = is_bid_dominant and is_spread_ok
            
            orderflow['is_bullish'] = is_bullish
            
            return is_bullish, orderflow
            
        except Exception as e:
            print(f"❌ Erreur orderflow {ticker}: {e}")
            return False, None
    
    def validate_breakout_with_orderflow(self, ticker: str) -> tuple[bool, Dict]:
        """
        Validation COMPLÈTE breakout + orderflow
        
        Returns: (is_valid, combined_details)
        """
        # Détection breakout
        is_breakout, breakout_details = self.detect_breakout(ticker)
        
        if not is_breakout:
            return False, {
                'breakout': breakout_details,
                'orderflow': None,
                'valid': False,
                'reason': 'Pas de breakout détecté'
            }
        
        # Validation orderflow
        is_orderflow_ok, orderflow_details = self.is_orderflow_bullish(ticker)
        
        if not is_orderflow_ok:
            return False, {
                'breakout': breakout_details,
                'orderflow': orderflow_details,
                'valid': False,
                'reason': 'Orderflow non favorable'
            }
        
        # Tout validé
        return True, {
            'breakout': breakout_details,
            'orderflow': orderflow_details,
            'valid': True,
            'reason': 'Breakout validé avec orderflow haussier'
        }
    
    def get_support_level(self, ticker: str, periods: int = 20) -> Optional[float]:
        """Calcule niveau de support"""
        try:
            df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')
            if df is None or df.empty or len(df) < periods:
                return None
            
            recent = df.tail(periods)
            support = recent['low'].min()
            
            return support
            
        except Exception as e:
            print(f"❌ Erreur support {ticker}: {e}")
            return None
    
    def get_resistance_level(self, ticker: str, periods: int = 20) -> Optional[float]:
        """Calcule niveau de résistance"""
        try:
            df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')
            if df is None or df.empty or len(df) < periods:
                return None
            
            recent = df.tail(periods)
            resistance = recent['high'].max()
            
            return resistance
            
        except Exception as e:
            print(f"❌ Erreur résistance {ticker}: {e}")
            return None


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST BREAKOUT DETECTOR")
    print("="*60 + "\n")
    
    from stock_data import StockDataProvider
    
    provider = StockDataProvider()
    detector = BreakoutDetector(provider)
    
    test_ticker = 'AAPL'
    
    try:
        provider.connect()
        
        print(f"🔍 Analyse breakout {test_ticker}:\n")
        
        # Support & Résistance
        support = detector.get_support_level(test_ticker)
        resistance = detector.get_resistance_level(test_ticker)
        
        if support and resistance:
            print(f"📊 Niveaux techniques:")
            print(f"   Support: ${support:.2f}")
            print(f"   Résistance: ${resistance:.2f}")
            print()
        
        # Détection breakout
        is_breakout, details = detector.detect_breakout(test_ticker)
        
        if is_breakout and details:
            print(f"🚀 BREAKOUT DÉTECTÉ!")
            print(f"   Prix: ${details['current_price']:.2f}")
            print(f"   Résistance cassée: ${details['resistance']:.2f}")
            print(f"   Breakout: +{details['breakout_pct']:.2f}%")
            print(f"   Volume: {details['volume_ratio']:.2f}x moyenne")
        else:
            print(f"❌ Pas de breakout")
            if details:
                print(f"   Prix: ${details['current_price']:.2f}")
                print(f"   Résistance: ${details['resistance']:.2f}")
        
        # Orderflow
        print(f"\n📈 Orderflow:")
        is_bullish, orderflow = detector.is_orderflow_bullish(test_ticker)
        
        if orderflow:
            print(f"   Bid: ${orderflow['bid']:.2f} x {orderflow['bid_size']}")
            print(f"   Ask: ${orderflow['ask']:.2f} x {orderflow['ask_size']}")
            print(f"   Spread: {orderflow['spread_pct']:.2f}%")
            print(f"   Bid pressure: {orderflow['bid_pressure']:.1f}%")
            print(f"   Signal: {'✅ Haussier' if is_bullish else '❌ Non haussier'}")
        
        # Validation complète
        print(f"\n🎯 Validation complète:")
        is_valid, combined = detector.validate_breakout_with_orderflow(test_ticker)
        
        if is_valid:
            print(f"   ✅ BREAKOUT VALIDÉ")
            print(f"   {combined['reason']}")
        else:
            print(f"   ❌ BREAKOUT NON VALIDÉ")
            print(f"   Raison: {combined['reason']}")
        
    finally:
        provider.disconnect()

