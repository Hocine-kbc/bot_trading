"""
Analyse des Indices de Marché (SPY, QQQ, VIX)
=============================================
Ce fichier analyse la santé globale du marché via les grands indices:

1. SPY (S&P 500): Les 500 plus grandes entreprises US
   → Représente l'économie américaine dans son ensemble

2. QQQ (Nasdaq 100): Les 100 plus grandes entreprises tech
   → Représente le secteur technologique

3. VIX (Indice de volatilité): "L'indice de la peur"
   → Mesure la nervosité des marchés
   → VIX bas = marché calme
   → VIX élevé = marché nerveux/panique

Le bot n'achète que si le marché global est favorable !
"""

# ============================================================
# IMPORTS
# ============================================================

from typing import Dict, Optional  # Pour typer les variables
import pandas as pd  # Pour manipuler les données

# Nos modules
from stock_data import StockDataProvider  # Pour récupérer les données
from config import VIX_MAX_LEVEL, SPY_MIN_CHANGE, QQQ_MIN_CHANGE  # Nos seuils


# ============================================================
# CLASSE PRINCIPALE - MarketIndicesAnalyzer
# ============================================================

class MarketIndicesAnalyzer:
    """
    Analyseur des indices de marché
    
    Permet de:
    - Analyser la tendance du SPY (S&P 500)
    - Analyser la tendance du QQQ (Nasdaq)
    - Vérifier le niveau du VIX (volatilité)
    - Valider si le marché est favorable pour acheter
    """
    
    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    
    def __init__(self, data_provider: StockDataProvider):
        """
        Constructeur
        
        Args:
            data_provider: Instance de StockDataProvider pour récupérer les données
        """
        self.data_provider = data_provider
    
    # --------------------------------------------------------
    # ANALYSE SPY (S&P 500)
    # --------------------------------------------------------
    
    def get_spy_status(self) -> Optional[Dict]:
        """
        Analyse la tendance du SPY (S&P 500)
        
        Le SPY est l'ETF qui suit les 500 plus grandes entreprises US.
        Si le SPY monte, le marché est globalement haussier.
        
        Returns:
            Dictionnaire avec:
            - price: prix actuel
            - change_pct: variation en %
            - trend: 'bullish' ou 'bearish'
            - is_bullish: True si variation >= 0.3%
        """
        try:
            # Récupérer les données OHLCV (bougies 5 min sur 1 jour)
            df = self.data_provider.get_ohlcv('SPY', interval='5 mins', duration='1 D')
            if df is None or df.empty:
                return None
            
            # Récupérer la dernière bougie et la précédente
            last = df.iloc[-1]  # Dernière bougie
            prev = df.iloc[-2] if len(df) > 1 else last  # Bougie précédente
            
            # Calculer la variation en %
            # Formule: ((nouveau - ancien) / ancien) * 100
            change_pct = ((last['close'] - prev['close']) / prev['close']) * 100
            
            # Calculer la tendance sur les 20 dernières bougies
            recent = df.tail(20)
            sma_20 = recent['close'].mean()  # Moyenne mobile simple sur 20 périodes
            
            # Tendance: haussière si prix > SMA20, baissière sinon
            trend = 'bullish' if last['close'] > sma_20 else 'bearish'
            
            # Signal haussier si variation >= seuil (0.3% par défaut)
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
    
    # --------------------------------------------------------
    # ANALYSE QQQ (Nasdaq 100)
    # --------------------------------------------------------
    
    def get_qqq_status(self) -> Optional[Dict]:
        """
        Analyse la tendance du QQQ (Nasdaq 100)
        
        Le QQQ suit les 100 plus grandes entreprises tech.
        Important car beaucoup d'actions momentum sont dans la tech.
        
        Returns:
            Même structure que get_spy_status()
        """
        try:
            # Récupérer les données
            df = self.data_provider.get_ohlcv('QQQ', interval='5 mins', duration='1 D')
            if df is None or df.empty:
                return None
            
            # Dernière et précédente bougie
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            
            # Variation
            change_pct = ((last['close'] - prev['close']) / prev['close']) * 100
            
            # Tendance
            recent = df.tail(20)
            sma_20 = recent['close'].mean()
            trend = 'bullish' if last['close'] > sma_20 else 'bearish'
            
            # Signal
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
    
    # --------------------------------------------------------
    # ANALYSE VIX (Indice de volatilité)
    # --------------------------------------------------------
    
    def get_vix_level(self) -> Optional[Dict]:
        """
        Analyse le niveau du VIX (indice de volatilité)
        
        Le VIX mesure la volatilité attendue du marché:
        - < 15: Très calme (excellent pour acheter)
        - 15-20: Calme (bon)
        - 20-25: Normal (acceptable)
        - 25-30: Nerveux (prudence)
        - > 30: Panique (ne pas acheter !)
        
        Returns:
            Dictionnaire avec:
            - level: niveau actuel du VIX
            - mood: interprétation ('calme', 'nerveux', etc.)
            - color: emoji correspondant
            - is_favorable: True si VIX < seuil max (25 par défaut)
        """
        try:
            # Récupérer le niveau du VIX (utilise la méthode spéciale pour les indices)
            vix_level = self.data_provider.get_vix_level()
            if vix_level is None:
                # Si VIX non disponible, utiliser une valeur par défaut favorable
                print("⚠️  VIX non disponible, utilisation valeur par défaut (20)")
                vix_level = 20.0
            
            # Interpréter le niveau du VIX
            if vix_level < 15:
                mood = 'très calme'
                color = '🟢'  # Vert = excellent
            elif vix_level < 20:
                mood = 'calme'
                color = '🟢'  # Vert = bon
            elif vix_level < 25:
                mood = 'normal'
                color = '🟡'  # Jaune = acceptable
            elif vix_level < 30:
                mood = 'nerveux'
                color = '🟠'  # Orange = prudence
            else:
                mood = 'panique'
                color = '🔴'  # Rouge = danger
            
            # Favorable si sous le seuil max (25 par défaut)
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
    
    # --------------------------------------------------------
    # VALIDATION GLOBALE DU MARCHÉ
    # --------------------------------------------------------
    
    def is_market_bullish(self) -> tuple[bool, Dict]:
        """
        Validation complète: le marché est-il haussier ?
        
        Conditions pour un marché haussier:
        1. SPY en hausse (>= 0.3%)
        2. QQQ en hausse (>= 0.3%)
        3. VIX bas (< 25)
        
        Returns:
            Tuple (is_bullish, details):
            - is_bullish: True si TOUTES les conditions sont remplies
            - details: Détails de chaque indice
        """
        try:
            # Analyser chaque indice
            spy = self.get_spy_status()
            qqq = self.get_qqq_status()
            vix = self.get_vix_level()
            
            # Vérifier qu'on a toutes les données
            if not all([spy, qqq, vix]):
                return False, {'error': 'Données manquantes'}
            
            # Vérifier chaque condition
            conditions = {
                'spy_bullish': spy['is_bullish'],      # SPY haussier ?
                'qqq_bullish': qqq['is_bullish'],      # QQQ haussier ?
                'vix_favorable': vix['is_favorable']   # VIX acceptable ?
            }
            
            # all() retourne True si TOUTES les valeurs sont True
            is_bullish = all(conditions.values())
            
            # Préparer les détails
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
    
    # --------------------------------------------------------
    # SCORE DE MARCHÉ
    # --------------------------------------------------------
    
    def get_market_score(self) -> int:
        """
        Calcule un score de marché de 0 à 100
        
        100 = Marché très haussier (idéal pour acheter)
        50 = Marché neutre
        0 = Marché très baissier (ne pas acheter)
        
        Returns:
            Score de 0 à 100
        """
        try:
            # Récupérer les données
            is_bullish, details = self.is_market_bullish()
            
            if 'error' in details:
                return 50  # Score neutre si erreur
            
            spy = details['spy']
            qqq = details['qqq']
            vix = details['vix']
            
            score = 50  # Commencer au milieu (neutre)
            
            # ---- Contribution du SPY (0 à 25 points) ----
            if spy['is_bullish']:
                score += 25  # SPY très haussier
            elif spy['change_pct'] > 0:
                score += 15  # SPY légèrement positif
            elif spy['change_pct'] < -0.5:
                score -= 20  # SPY très négatif
            
            # ---- Contribution du QQQ (0 à 25 points) ----
            if qqq['is_bullish']:
                score += 25  # QQQ très haussier
            elif qqq['change_pct'] > 0:
                score += 15  # QQQ légèrement positif
            elif qqq['change_pct'] < -0.5:
                score -= 20  # QQQ très négatif
            
            # ---- Contribution du VIX (-25 à 0 points) ----
            # Plus le VIX est bas, mieux c'est
            if vix['level'] < 15:
                score += 0   # Très calme, pas de pénalité
            elif vix['level'] < 20:
                score -= 5   # Calme, petite pénalité
            elif vix['level'] < 25:
                score -= 10  # Normal, pénalité modérée
            elif vix['level'] < 30:
                score -= 15  # Nerveux, pénalité importante
            else:
                score -= 25  # Panique, grosse pénalité
            
            # Limiter le score entre 0 et 100
            # max(0, ...) = au minimum 0
            # min(100, ...) = au maximum 100
            score = max(0, min(100, score))
            
            return score
            
        except Exception as e:
            print(f"❌ Erreur calcul score marché: {e}")
            return 50  # Score neutre si erreur


# ============================================================
# CODE DE TEST
# ============================================================

if __name__ == '__main__':
    # Afficher en-tête
    print("\n" + "="*60)
    print("TEST MARKET INDICES ANALYZER")
    print("="*60 + "\n")
    
    # Importer le provider
    from stock_data import StockDataProvider
    
    # Créer les instances
    provider = StockDataProvider()
    analyzer = MarketIndicesAnalyzer(provider)
    
    try:
        # Se connecter à IBKR
        provider.connect()
        
        # ---- Analyse SPY ----
        print("📊 SPY:")
        spy = analyzer.get_spy_status()
        if spy:
            print(f"   Prix: ${spy['price']:.2f}")
            print(f"   Variation: {spy['change_pct']:+.2f}%")
            print(f"   Tendance: {spy['trend']}")
            print(f"   Signal: {'✅ Haussier' if spy['is_bullish'] else '❌ Non haussier'}")
        
        # ---- Analyse QQQ ----
        print(f"\n📊 QQQ:")
        qqq = analyzer.get_qqq_status()
        if qqq:
            print(f"   Prix: ${qqq['price']:.2f}")
            print(f"   Variation: {qqq['change_pct']:+.2f}%")
            print(f"   Tendance: {qqq['trend']}")
            print(f"   Signal: {'✅ Haussier' if qqq['is_bullish'] else '❌ Non haussier'}")
        
        # ---- Analyse VIX ----
        print(f"\n📊 VIX:")
        vix = analyzer.get_vix_level()
        if vix:
            print(f"   Niveau: {vix['level']:.2f}")
            print(f"   Humeur: {vix['color']} {vix['mood']}")
            print(f"   Favorable: {'✅ Oui' if vix['is_favorable'] else '❌ Non'}")
        
        # ---- Validation globale ----
        print(f"\n🎯 Validation marché:")
        is_bullish, details = analyzer.is_market_bullish()
        score = analyzer.get_market_score()
        
        print(f"   Marché haussier: {'✅ OUI' if is_bullish else '❌ NON'}")
        print(f"   Score: {score}/100")
        
        # Afficher le détail des conditions
        if 'conditions' in details:
            print(f"\n   Conditions:")
            for cond, status in details['conditions'].items():
                emoji = "✅" if status else "❌"
                print(f"      {emoji} {cond}")
        
    finally:
        # Toujours se déconnecter
        provider.disconnect()
