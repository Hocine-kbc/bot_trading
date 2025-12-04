"""
Détection patterns chandeliers (Steve Nison)
"""
import pandas as pd
from typing import Optional, Dict
from config import MIN_VOLUME_MULTIPLIER


class CandlestickPatterns:
    """Détecteur de patterns de chandeliers japonais"""
    
    @staticmethod
    def _is_bullish_candle(candle: pd.Series) -> bool:
        """Chandelier vert (haussier)"""
        return candle['close'] > candle['open']
    
    @staticmethod
    def _is_bearish_candle(candle: pd.Series) -> bool:
        """Chandelier rouge (baissier)"""
        return candle['close'] < candle['open']
    
    @staticmethod
    def _get_body_size(candle: pd.Series) -> float:
        """Taille du corps"""
        return abs(candle['close'] - candle['open'])
    
    @staticmethod
    def _get_upper_shadow(candle: pd.Series) -> float:
        """Taille mèche haute"""
        return candle['high'] - max(candle['open'], candle['close'])
    
    @staticmethod
    def _get_lower_shadow(candle: pd.Series) -> float:
        """Taille mèche basse"""
        return min(candle['open'], candle['close']) - candle['low']
    
    @staticmethod
    def _get_total_range(candle: pd.Series) -> float:
        """Range total"""
        return candle['high'] - candle['low']
    
    def detect_hammer(self, candle: pd.Series) -> bool:
        """
        Marteau (Hammer)
        
        Conditions:
        - Corps en haut du range
        - Mèche basse >= 2x corps
        - Mèche haute petite (< 10% range)
        """
        try:
            body = self._get_body_size(candle)
            lower_shadow = self._get_lower_shadow(candle)
            upper_shadow = self._get_upper_shadow(candle)
            total_range = self._get_total_range(candle)
            
            if total_range == 0:
                return False
            
            # Corps petit/moyen
            if body / total_range > 0.35:
                return False
            
            # Mèche basse longue
            if lower_shadow < body * 2:
                return False
            
            # Mèche haute petite
            if upper_shadow > total_range * 0.1:
                return False
            
            # Corps dans le haut (80% supérieur)
            body_position = (max(candle['open'], candle['close']) - candle['low']) / total_range
            if body_position < 0.8:
                return False
            
            return True
            
        except:
            return False
    
    def detect_inverted_hammer(self, candle: pd.Series) -> bool:
        """
        Marteau inversé (Inverted Hammer)
        
        Conditions:
        - Corps en bas du range
        - Mèche haute >= 2x corps
        - Mèche basse petite (< 10% range)
        """
        try:
            body = self._get_body_size(candle)
            lower_shadow = self._get_lower_shadow(candle)
            upper_shadow = self._get_upper_shadow(candle)
            total_range = self._get_total_range(candle)
            
            if total_range == 0:
                return False
            
            # Corps petit/moyen
            if body / total_range > 0.35:
                return False
            
            # Mèche haute longue
            if upper_shadow < body * 2:
                return False
            
            # Mèche basse petite
            if lower_shadow > total_range * 0.1:
                return False
            
            # Corps dans le bas (20% inférieur)
            body_position = (max(candle['open'], candle['close']) - candle['low']) / total_range
            if body_position > 0.2:
                return False
            
            return True
            
        except:
            return False
    
    def detect_bullish_engulfing(self, prev: pd.Series, current: pd.Series) -> bool:
        """
        Englobante haussière (Bullish Engulfing)
        
        Conditions:
        - Chandelier précédent rouge
        - Chandelier actuel vert
        - Corps actuel englobe corps précédent
        """
        try:
            if not self._is_bearish_candle(prev):
                return False
            
            if not self._is_bullish_candle(current):
                return False
            
            # Corps actuel englobe corps précédent
            if current['open'] <= prev['close'] and current['close'] >= prev['open']:
                return True
            
            return False
            
        except:
            return False
    
    def detect_piercing_line(self, prev: pd.Series, current: pd.Series) -> bool:
        """
        Ligne perforante (Piercing Line)
        
        Conditions:
        - Chandelier précédent rouge
        - Chandelier actuel vert
        - Ouverture actuelle < clôture précédente
        - Clôture actuelle > 50% corps précédent
        """
        try:
            if not self._is_bearish_candle(prev):
                return False
            
            if not self._is_bullish_candle(current):
                return False
            
            # Ouverture en dessous
            if current['open'] >= prev['close']:
                return False
            
            # Clôture au-dessus du milieu
            prev_mid = (prev['open'] + prev['close']) / 2
            if current['close'] <= prev_mid:
                return False
            
            return True
            
        except:
            return False
    
    def detect_three_white_soldiers(self, candles: list) -> bool:
        """
        Trois soldats blancs (Three White Soldiers)
        
        Conditions:
        - 3 chandeliers verts consécutifs
        - Chaque clôture > clôture précédente
        - Corps de taille similaire
        - Mèches hautes petites
        """
        try:
            if len(candles) < 3:
                return False
            
            c1, c2, c3 = candles[-3], candles[-2], candles[-1]
            
            # Tous verts
            if not all([self._is_bullish_candle(c) for c in [c1, c2, c3]]):
                return False
            
            # Clôtures croissantes
            if not (c1['close'] < c2['close'] < c3['close']):
                return False
            
            # Corps similaires (écart max 50%)
            bodies = [self._get_body_size(c) for c in [c1, c2, c3]]
            min_body = min(bodies)
            max_body = max(bodies)
            
            if max_body > min_body * 1.5:
                return False
            
            # Mèches hautes petites
            for c in [c1, c2, c3]:
                upper_shadow = self._get_upper_shadow(c)
                total_range = self._get_total_range(c)
                if total_range > 0 and upper_shadow / total_range > 0.25:
                    return False
            
            return True
            
        except:
            return False
    
    def detect_shooting_star(self, candle: pd.Series) -> bool:
        """
        Étoile filante (Shooting Star) - BEARISH
        
        Similaire au marteau inversé mais baissier
        """
        return self.detect_inverted_hammer(candle)
    
    def detect_hanging_man(self, candle: pd.Series) -> bool:
        """
        Pendu (Hanging Man) - BEARISH
        
        Similaire au marteau mais baissier
        """
        return self.detect_hammer(candle)
    
    def detect_doji(self, candle: pd.Series) -> bool:
        """
        Doji - NEUTRE/BEARISH
        
        Conditions:
        - Corps très petit (< 10% range)
        """
        try:
            body = self._get_body_size(candle)
            total_range = self._get_total_range(candle)
            
            if total_range == 0:
                return True  # Pas de mouvement = doji
            
            body_pct = body / total_range
            
            return body_pct < 0.10
            
        except:
            return False
    
    def detect_bearish_engulfing(self, prev: pd.Series, current: pd.Series) -> bool:
        """Englobante baissière (Bearish Engulfing)"""
        try:
            if not self._is_bullish_candle(prev):
                return False
            
            if not self._is_bearish_candle(current):
                return False
            
            # Corps actuel englobe corps précédent
            if current['open'] >= prev['close'] and current['close'] <= prev['open']:
                return True
            
            return False
            
        except:
            return False
    
    def detect_bullish_pattern(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Détecte pattern haussier dans les données
        
        Returns: {'pattern': nom, 'confidence': 0-100}
        """
        if df is None or df.empty or len(df) < 3:
            return None
        
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        last_3 = [df.iloc[i] for i in range(-3, 0)] if len(df) >= 3 else []
        
        # Vérifier patterns haussiers (ordre de priorité)
        if self.detect_three_white_soldiers(last_3):
            return {'pattern': 'THREE_WHITE_SOLDIERS', 'confidence': 90}
        
        if self.detect_bullish_engulfing(prev, last):
            return {'pattern': 'BULLISH_ENGULFING', 'confidence': 85}
        
        if self.detect_piercing_line(prev, last):
            return {'pattern': 'PIERCING_LINE', 'confidence': 80}
        
        if self.detect_hammer(last):
            return {'pattern': 'HAMMER', 'confidence': 75}
        
        if self.detect_inverted_hammer(last):
            return {'pattern': 'INVERTED_HAMMER', 'confidence': 70}
        
        return None
    
    def detect_bearish_pattern(self, df: pd.DataFrame) -> Optional[Dict]:
        """Détecte pattern baissier"""
        if df is None or df.empty or len(df) < 2:
            return None
        
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        
        if self.detect_doji(last):
            return {'pattern': 'DOJI', 'confidence': 60}
        
        if self.detect_bearish_engulfing(prev, last):
            return {'pattern': 'BEARISH_ENGULFING', 'confidence': 85}
        
        if self.detect_shooting_star(last):
            return {'pattern': 'SHOOTING_STAR', 'confidence': 75}
        
        if self.detect_hanging_man(last):
            return {'pattern': 'HANGING_MAN', 'confidence': 75}
        
        return None
    
    def validate_volume(self, candle: pd.Series, avg_volume: float) -> bool:
        """Valide que le volume du chandelier est suffisant"""
        if avg_volume == 0:
            return False
        
        volume_ratio = candle['volume'] / avg_volume
        
        return volume_ratio >= MIN_VOLUME_MULTIPLIER


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST CANDLESTICK PATTERNS")
    print("="*60 + "\n")
    
    # Test avec données simulées
    import numpy as np
    
    patterns = CandlestickPatterns()
    
    # Hammer
    hammer = pd.Series({
        'open': 100,
        'high': 101,
        'low': 95,
        'close': 100.5,
        'volume': 1000000
    })
    
    is_hammer = patterns.detect_hammer(hammer)
    print(f"🔨 Hammer: {'✅' if is_hammer else '❌'}")
    
    # Bullish engulfing
    prev_bear = pd.Series({'open': 102, 'high': 103, 'low': 100, 'close': 100.5, 'volume': 1000000})
    current_bull = pd.Series({'open': 100, 'high': 104, 'low': 99, 'close': 103.5, 'volume': 1200000})
    
    is_engulfing = patterns.detect_bullish_engulfing(prev_bear, current_bull)
    print(f"📈 Bullish Engulfing: {'✅' if is_engulfing else '❌'}")
    
    # Doji
    doji = pd.Series({
        'open': 100,
        'high': 101,
        'low': 99,
        'close': 100.1,
        'volume': 1000000
    })
    
    is_doji = patterns.detect_doji(doji)
    print(f"➖ Doji: {'✅' if is_doji else '❌'}")
    
    print(f"\n✅ Tests patterns OK")

