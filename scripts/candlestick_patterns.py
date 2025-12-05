"""
Détection de Patterns de Chandeliers Japonais
=============================================
Ce fichier détecte les patterns de chandeliers (candlestick patterns)
basés sur les travaux de Steve Nison, père de l'analyse en chandeliers.

Un chandelier a 4 composants:
- Open (ouverture): Prix au début de la période
- High (plus haut): Prix le plus haut de la période
- Low (plus bas): Prix le plus bas de la période
- Close (clôture): Prix à la fin de la période

Le CORPS = |Close - Open| (partie colorée)
La MÈCHE HAUTE = High - max(Open, Close)
La MÈCHE BASSE = min(Open, Close) - Low

Patterns HAUSSIERS détectés (signaux d'achat):
- Hammer (Marteau)
- Inverted Hammer (Marteau inversé)
- Bullish Engulfing (Englobante haussière)
- Piercing Line (Ligne perforante)
- Three White Soldiers (Trois soldats blancs)

Patterns BAISSIERS détectés (signaux de vente):
- Doji
- Shooting Star (Étoile filante)
- Hanging Man (Pendu)
- Bearish Engulfing (Englobante baissière)
"""

# ============================================================
# IMPORTS
# ============================================================

import pandas as pd  # Pour manipuler les données
from typing import Optional, Dict  # Pour typer les variables

from config import MIN_VOLUME_MULTIPLIER  # Volume minimum requis (1.2x)


# ============================================================
# CLASSE PRINCIPALE - CandlestickPatterns
# ============================================================

class CandlestickPatterns:
    """
    Détecteur de patterns de chandeliers japonais
    
    Permet de:
    - Détecter les patterns haussiers (signaux d'achat)
    - Détecter les patterns baissiers (signaux de danger)
    - Valider le volume accompagnant le pattern
    """
    
    # --------------------------------------------------------
    # MÉTHODES UTILITAIRES (pour analyser un chandelier)
    # --------------------------------------------------------
    
    @staticmethod
    def _is_bullish_candle(candle: pd.Series) -> bool:
        """
        Vérifie si le chandelier est vert (haussier)
        
        Vert = Close > Open = le prix a monté pendant la période
        """
        return candle['close'] > candle['open']
    
    @staticmethod
    def _is_bearish_candle(candle: pd.Series) -> bool:
        """
        Vérifie si le chandelier est rouge (baissier)
        
        Rouge = Close < Open = le prix a baissé pendant la période
        """
        return candle['close'] < candle['open']
    
    @staticmethod
    def _get_body_size(candle: pd.Series) -> float:
        """
        Calcule la taille du corps du chandelier
        
        Corps = |Close - Open|
        """
        return abs(candle['close'] - candle['open'])
    
    @staticmethod
    def _get_upper_shadow(candle: pd.Series) -> float:
        """
        Calcule la taille de la mèche haute
        
        Mèche haute = High - max(Open, Close)
        """
        return candle['high'] - max(candle['open'], candle['close'])
    
    @staticmethod
    def _get_lower_shadow(candle: pd.Series) -> float:
        """
        Calcule la taille de la mèche basse
        
        Mèche basse = min(Open, Close) - Low
        """
        return min(candle['open'], candle['close']) - candle['low']
    
    @staticmethod
    def _get_total_range(candle: pd.Series) -> float:
        """
        Calcule le range total du chandelier
        
        Range = High - Low
        """
        return candle['high'] - candle['low']
    
    # --------------------------------------------------------
    # PATTERNS HAUSSIERS
    # --------------------------------------------------------
    
    def detect_hammer(self, candle: pd.Series) -> bool:
        """
        Détecte un Marteau (Hammer)
        
        Le marteau est un signal de retournement haussier.
        Il apparaît après une baisse et suggère que les vendeurs
        ont essayé de pousser le prix plus bas mais les acheteurs
        ont repris le contrôle.
        
        Caractéristiques:
        - Corps petit en haut du range
        - Mèche basse très longue (>= 2x le corps)
        - Mèche haute très petite (< 10% du range)
        
              |  ← petite mèche haute
             █|█ ← petit corps (vert ou rouge)
              |
              |
              |  ← longue mèche basse
        """
        try:
            # Calculer les composants
            body = self._get_body_size(candle)
            lower_shadow = self._get_lower_shadow(candle)
            upper_shadow = self._get_upper_shadow(candle)
            total_range = self._get_total_range(candle)
            
            if total_range == 0:
                return False
            
            # Condition 1: Corps petit/moyen (< 35% du range)
            if body / total_range > 0.35:
                return False
            
            # Condition 2: Mèche basse longue (>= 2x le corps)
            if lower_shadow < body * 2:
                return False
            
            # Condition 3: Mèche haute petite (< 10% du range)
            if upper_shadow > total_range * 0.1:
                return False
            
            # Condition 4: Corps dans le haut du range (80% supérieur)
            body_position = (max(candle['open'], candle['close']) - candle['low']) / total_range
            if body_position < 0.8:
                return False
            
            return True
            
        except:
            return False
    
    def detect_inverted_hammer(self, candle: pd.Series) -> bool:
        """
        Détecte un Marteau Inversé (Inverted Hammer)
        
        Signal de retournement haussier similaire au marteau,
        mais avec la longue mèche en haut au lieu du bas.
        
        Caractéristiques:
        - Corps petit en bas du range
        - Mèche haute très longue (>= 2x le corps)
        - Mèche basse très petite (< 10% du range)
        
              |
              |
              |  ← longue mèche haute
             █|█ ← petit corps
              |  ← petite mèche basse
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
        Détecte une Englobante Haussière (Bullish Engulfing)
        
        Pattern très puissant de retournement haussier.
        Le chandelier vert actuel "englobe" complètement
        le chandelier rouge précédent.
        
        Caractéristiques:
        - Chandelier précédent: Rouge (baissier)
        - Chandelier actuel: Vert (haussier)
        - Corps actuel englobe entièrement le corps précédent
        
            |          |
           █|█ rouge   |  
            |        ████ vert (plus grand)
                       |
        """
        try:
            # Le précédent doit être rouge (baissier)
            if not self._is_bearish_candle(prev):
                return False
            
            # L'actuel doit être vert (haussier)
            if not self._is_bullish_candle(current):
                return False
            
            # Corps actuel englobe corps précédent
            # Open actuel <= Close précédent (commence en dessous)
            # Close actuel >= Open précédent (finit au-dessus)
            if current['open'] <= prev['close'] and current['close'] >= prev['open']:
                return True
            
            return False
            
        except:
            return False
    
    def detect_piercing_line(self, prev: pd.Series, current: pd.Series) -> bool:
        """
        Détecte une Ligne Perforante (Piercing Line)
        
        Signal de retournement haussier.
        Le chandelier vert actuel ouvre en dessous du précédent
        puis remonte au-delà du milieu du corps précédent.
        
        Caractéristiques:
        - Chandelier précédent: Rouge
        - Chandelier actuel: Vert
        - Ouverture actuelle < clôture précédente
        - Clôture actuelle > 50% du corps précédent
        """
        try:
            # Précédent rouge
            if not self._is_bearish_candle(prev):
                return False
            
            # Actuel vert
            if not self._is_bullish_candle(current):
                return False
            
            # Ouverture en dessous de la clôture précédente
            if current['open'] >= prev['close']:
                return False
            
            # Clôture au-dessus du milieu du corps précédent
            prev_mid = (prev['open'] + prev['close']) / 2
            if current['close'] <= prev_mid:
                return False
            
            return True
            
        except:
            return False
    
    def detect_three_white_soldiers(self, candles: list) -> bool:
        """
        Détecte Trois Soldats Blancs (Three White Soldiers)
        
        Pattern très puissant de continuation/retournement haussier.
        Trois grands chandeliers verts consécutifs avec clôtures croissantes.
        
        Caractéristiques:
        - 3 chandeliers verts consécutifs
        - Chaque clôture > clôture précédente
        - Corps de tailles similaires
        - Mèches hautes petites (pas de pression vendeuse)
        
           |      |      |
          ███   ███   ███
           |      |      |
        """
        try:
            if len(candles) < 3:
                return False
            
            # Récupérer les 3 derniers chandeliers
            c1, c2, c3 = candles[-3], candles[-2], candles[-1]
            
            # Condition 1: Tous les 3 sont verts
            if not all([self._is_bullish_candle(c) for c in [c1, c2, c3]]):
                return False
            
            # Condition 2: Clôtures croissantes
            if not (c1['close'] < c2['close'] < c3['close']):
                return False
            
            # Condition 3: Corps de tailles similaires (écart max 50%)
            bodies = [self._get_body_size(c) for c in [c1, c2, c3]]
            min_body = min(bodies)
            max_body = max(bodies)
            
            if max_body > min_body * 1.5:
                return False
            
            # Condition 4: Mèches hautes petites (< 25% du range)
            for c in [c1, c2, c3]:
                upper_shadow = self._get_upper_shadow(c)
                total_range = self._get_total_range(c)
                if total_range > 0 and upper_shadow / total_range > 0.25:
                    return False
            
            return True
            
        except:
            return False
    
    # --------------------------------------------------------
    # PATTERNS BAISSIERS
    # --------------------------------------------------------
    
    def detect_shooting_star(self, candle: pd.Series) -> bool:
        """
        Détecte une Étoile Filante (Shooting Star) - BEARISH
        
        Signal de retournement baissier.
        Visuellement similaire au marteau inversé mais apparaît
        après une hausse et signale un affaiblissement.
        """
        return self.detect_inverted_hammer(candle)
    
    def detect_hanging_man(self, candle: pd.Series) -> bool:
        """
        Détecte un Pendu (Hanging Man) - BEARISH
        
        Signal de retournement baissier.
        Visuellement similaire au marteau mais apparaît
        après une hausse et signale un affaiblissement.
        """
        return self.detect_hammer(candle)
    
    def detect_doji(self, candle: pd.Series) -> bool:
        """
        Détecte un Doji - NEUTRE/BEARISH
        
        Le doji signale l'indécision du marché.
        Open et Close sont très proches (corps minuscule).
        
        Caractéristiques:
        - Corps très petit (< 10% du range)
        
              |
              +  ← corps minuscule (presque une ligne)
              |
        """
        try:
            body = self._get_body_size(candle)
            total_range = self._get_total_range(candle)
            
            if total_range == 0:
                return True  # Pas de mouvement = doji
            
            body_pct = body / total_range
            
            # Doji si corps < 10% du range
            return body_pct < 0.10
            
        except:
            return False
    
    def detect_bearish_engulfing(self, prev: pd.Series, current: pd.Series) -> bool:
        """
        Détecte une Englobante Baissière (Bearish Engulfing)
        
        L'inverse de l'englobante haussière.
        Le chandelier rouge englobe le vert précédent.
        """
        try:
            # Précédent vert
            if not self._is_bullish_candle(prev):
                return False
            
            # Actuel rouge
            if not self._is_bearish_candle(current):
                return False
            
            # Corps actuel englobe corps précédent
            if current['open'] >= prev['close'] and current['close'] <= prev['open']:
                return True
            
            return False
            
        except:
            return False
    
    # --------------------------------------------------------
    # DÉTECTION AUTOMATIQUE
    # --------------------------------------------------------
    
    def detect_bullish_pattern(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Détecte automatiquement un pattern haussier
        
        Parcourt les patterns haussiers par ordre de priorité/confiance
        et retourne le premier trouvé.
        
        Args:
            df: DataFrame avec les données OHLCV
        
        Returns:
            Dictionnaire {'pattern': nom, 'confidence': 0-100} ou None
        """
        if df is None or df.empty or len(df) < 3:
            return None
        
        # Récupérer les chandeliers nécessaires
        last = df.iloc[-1]  # Dernier chandelier
        prev = df.iloc[-2] if len(df) > 1 else last  # Avant-dernier
        last_3 = [df.iloc[i] for i in range(-3, 0)] if len(df) >= 3 else []
        
        # Vérifier les patterns par ordre de confiance (du plus fiable au moins fiable)
        
        # 1. Three White Soldiers (90% confiance)
        if self.detect_three_white_soldiers(last_3):
            return {'pattern': 'THREE_WHITE_SOLDIERS', 'confidence': 90}
        
        # 2. Bullish Engulfing (85% confiance)
        if self.detect_bullish_engulfing(prev, last):
            return {'pattern': 'BULLISH_ENGULFING', 'confidence': 85}
        
        # 3. Piercing Line (80% confiance)
        if self.detect_piercing_line(prev, last):
            return {'pattern': 'PIERCING_LINE', 'confidence': 80}
        
        # 4. Hammer (75% confiance)
        if self.detect_hammer(last):
            return {'pattern': 'HAMMER', 'confidence': 75}
        
        # 5. Inverted Hammer (70% confiance)
        if self.detect_inverted_hammer(last):
            return {'pattern': 'INVERTED_HAMMER', 'confidence': 70}
        
        return None  # Aucun pattern trouvé
    
    def detect_bearish_pattern(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Détecte automatiquement un pattern baissier
        
        Args:
            df: DataFrame avec les données OHLCV
        
        Returns:
            Dictionnaire {'pattern': nom, 'confidence': 0-100} ou None
        """
        if df is None or df.empty or len(df) < 2:
            return None
        
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        
        # Vérifier les patterns baissiers
        
        if self.detect_doji(last):
            return {'pattern': 'DOJI', 'confidence': 60}
        
        if self.detect_bearish_engulfing(prev, last):
            return {'pattern': 'BEARISH_ENGULFING', 'confidence': 85}
        
        if self.detect_shooting_star(last):
            return {'pattern': 'SHOOTING_STAR', 'confidence': 75}
        
        if self.detect_hanging_man(last):
            return {'pattern': 'HANGING_MAN', 'confidence': 75}
        
        return None
    
    # --------------------------------------------------------
    # VALIDATION DU VOLUME
    # --------------------------------------------------------
    
    def validate_volume(self, candle: pd.Series, avg_volume: float) -> bool:
        """
        Valide que le volume accompagnant le pattern est suffisant
        
        Un pattern sans volume n'est pas fiable.
        Le volume doit être au moins 1.2x la moyenne.
        
        Args:
            candle: Le chandelier à vérifier
            avg_volume: Le volume moyen de référence
        
        Returns:
            True si le volume est suffisant
        """
        if avg_volume == 0:
            return False
        
        # Calculer le ratio
        volume_ratio = candle['volume'] / avg_volume
        
        # Valide si >= 1.2x (MIN_VOLUME_MULTIPLIER)
        return volume_ratio >= MIN_VOLUME_MULTIPLIER


# ============================================================
# CODE DE TEST
# ============================================================

if __name__ == '__main__':
    # Afficher en-tête
    print("\n" + "="*60)
    print("TEST CANDLESTICK PATTERNS")
    print("="*60 + "\n")
    
    # Importer numpy pour créer des données de test
    import numpy as np
    
    # Créer un détecteur de patterns
    patterns = CandlestickPatterns()
    
    # ---- Test 1: Hammer ----
    # Créer un chandelier qui ressemble à un marteau
    hammer = pd.Series({
        'open': 100,
        'high': 101,
        'low': 95,
        'close': 100.5,
        'volume': 1000000
    })
    
    is_hammer = patterns.detect_hammer(hammer)
    print(f"🔨 Hammer: {'✅' if is_hammer else '❌'}")
    
    # ---- Test 2: Bullish Engulfing ----
    # Créer deux chandeliers pour l'englobante
    prev_bear = pd.Series({
        'open': 102, 'high': 103, 'low': 100, 'close': 100.5, 'volume': 1000000
    })
    current_bull = pd.Series({
        'open': 100, 'high': 104, 'low': 99, 'close': 103.5, 'volume': 1200000
    })
    
    is_engulfing = patterns.detect_bullish_engulfing(prev_bear, current_bull)
    print(f"📈 Bullish Engulfing: {'✅' if is_engulfing else '❌'}")
    
    # ---- Test 3: Doji ----
    # Créer un doji (corps minuscule)
    doji = pd.Series({
        'open': 100,
        'high': 101,
        'low': 99,
        'close': 100.1,  # Très proche de l'open
        'volume': 1000000
    })
    
    is_doji = patterns.detect_doji(doji)
    print(f"➖ Doji: {'✅' if is_doji else '❌'}")
    
    print(f"\n✅ Tests patterns OK")
