"""
Surveillance des Secteurs de Marché via ETFs
============================================
Ce fichier analyse la performance de chaque secteur du S&P 500.

Le marché boursier US est divisé en 11 secteurs:
1. Technology (XLK) - Apple, Microsoft, Nvidia
2. Healthcare (XLV) - Johnson & Johnson, Pfizer
3. Financials (XLF) - JPMorgan, Bank of America
4. Consumer Discretionary (XLY) - Amazon, Tesla
5. Consumer Staples (XLP) - Procter & Gamble, Coca-Cola
6. Energy (XLE) - Exxon, Chevron
7. Industrials (XLI) - Boeing, Caterpillar
8. Materials (XLB) - Dow, DuPont
9. Real Estate (XLRE) - REITs
10. Utilities (XLU) - Electric, Gas companies
11. Communication (XLC) - Google, Meta

On utilise les ETFs sectoriels pour analyser chaque secteur.
Le bot préfère acheter des actions dans des secteurs en hausse !
"""

# ============================================================
# IMPORTS
# ============================================================

from typing import Dict, List, Optional  # Pour typer les variables
import pandas as pd  # Pour manipuler les données

# Nos modules
from stock_data import StockDataProvider  # Pour récupérer les données
from config import SECTOR_ETFS, SECTOR_MIN_CHANGE, MIN_VOLUME_MULTIPLIER  # Nos seuils


# ============================================================
# CLASSE PRINCIPALE - MarketSectorsAnalyzer
# ============================================================

class MarketSectorsAnalyzer:
    """
    Analyseur des secteurs de marché
    
    Permet de:
    - Analyser la performance de chaque secteur
    - Identifier les secteurs haussiers
    - Vérifier si le secteur d'une action est favorable
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
    # ANALYSE D'UN SECTEUR
    # --------------------------------------------------------
    
    def get_sector_status(self, etf_symbol: str, sector_name: str = '') -> Optional[Dict]:
        """
        Analyse un secteur via son ETF
        
        Chaque secteur a un ETF qui le représente.
        Par exemple, XLK représente le secteur technologique.
        
        Args:
            etf_symbol: Le symbole de l'ETF (ex: 'XLK')
            sector_name: Le nom du secteur (ex: 'technology')
        
        Returns:
            Dictionnaire avec:
            - sector/etf: identification
            - price: prix actuel
            - change_pct: variation en %
            - volume_ratio: volume actuel vs moyenne
            - trend: 'bullish' ou 'bearish'
            - is_bullish: True si conditions haussières remplies
        """
        try:
            # Récupérer les données OHLCV
            df = self.data_provider.get_ohlcv(etf_symbol, interval='5 mins', duration='1 D')
            if df is None or df.empty:
                return None
            
            # Dernière bougie et précédente
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            
            # Calculer la variation en %
            change_pct = ((last['close'] - prev['close']) / prev['close']) * 100
            
            # Analyser le volume
            recent = df.tail(20)
            avg_volume = recent['volume'].mean()  # Volume moyen
            # Ratio = volume actuel / volume moyen
            volume_ratio = last['volume'] / avg_volume if avg_volume > 0 else 0
            
            # Calculer la tendance
            sma_20 = recent['close'].mean()  # Moyenne mobile 20 périodes
            trend = 'bullish' if last['close'] > sma_20 else 'bearish'
            
            # Un secteur est haussier si:
            # 1. La variation est >= au seuil (0.5% par défaut)
            # 2. Le volume est >= à 1.2x la moyenne
            is_bullish = (
                change_pct >= SECTOR_MIN_CHANGE * 100 and
                volume_ratio >= MIN_VOLUME_MULTIPLIER
            )
            
            return {
                'sector': sector_name or etf_symbol,  # Nom du secteur
                'etf': etf_symbol,                    # Symbole de l'ETF
                'price': last['close'],               # Prix actuel
                'change_pct': change_pct,             # Variation en %
                'volume': last['volume'],             # Volume actuel
                'avg_volume': avg_volume,             # Volume moyen
                'volume_ratio': volume_ratio,         # Ratio de volume
                'sma_20': sma_20,                     # SMA 20
                'trend': trend,                       # Tendance
                'is_bullish': is_bullish              # Signal haussier
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse secteur {etf_symbol}: {e}")
            return None
    
    # --------------------------------------------------------
    # ANALYSE DE TOUS LES SECTEURS
    # --------------------------------------------------------
    
    def get_all_sectors_status(self) -> Dict[str, Dict]:
        """
        Analyse tous les secteurs
        
        Parcourt la liste des ETFs sectoriels définie dans config.py
        et analyse chaque secteur.
        
        Returns:
            Dictionnaire {nom_secteur: données_secteur}
        """
        results = {}
        
        # Parcourir chaque secteur défini dans SECTOR_ETFS
        for sector_name, etf_symbol in SECTOR_ETFS.items():
            status = self.get_sector_status(etf_symbol, sector_name)
            if status:
                results[sector_name] = status
        
        return results
    
    def get_bullish_sectors(self) -> List[Dict]:
        """
        Retourne la liste des secteurs haussiers
        
        Les secteurs sont triés par force (variation la plus élevée en premier).
        
        Returns:
            Liste des secteurs haussiers triés par variation décroissante
        """
        # Récupérer tous les secteurs
        all_sectors = self.get_all_sectors_status()
        
        # Filtrer pour garder seulement les haussiers
        bullish = [
            sector_data for sector_data in all_sectors.values()
            if sector_data['is_bullish']
        ]
        
        # Trier par variation décroissante (le plus fort en premier)
        bullish.sort(key=lambda x: x['change_pct'], reverse=True)
        
        return bullish
    
    # --------------------------------------------------------
    # VÉRIFICATION D'UN SECTEUR SPÉCIFIQUE
    # --------------------------------------------------------
    
    def is_sector_bullish(self, etf_symbol: str) -> bool:
        """
        Vérifie si un secteur spécifique est haussier
        
        Args:
            etf_symbol: Le symbole de l'ETF du secteur
        
        Returns:
            True si le secteur est haussier
        """
        status = self.get_sector_status(etf_symbol)
        if not status:
            return False
        return status['is_bullish']
    
    # --------------------------------------------------------
    # IDENTIFICATION DU SECTEUR D'UNE ACTION
    # --------------------------------------------------------
    
    def get_sector_for_stock(self, ticker: str) -> Optional[str]:
        """
        Identifie le secteur d'une action
        
        ATTENTION: Cette méthode utilise un mapping manuel simplifié.
        Pour une identification précise, il faudrait utiliser une API
        de données fondamentales (comme Benzinga ou Yahoo Finance).
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Le nom du secteur ou None si inconnu
        """
        # Mapping manuel de quelques actions populaires
        # À améliorer avec une API de données fondamentales
        tech_stocks = ['AAPL', 'MSFT', 'NVDA', 'AMD', 'META', 'GOOGL', 'AVGO', 'ADBE']
        consumer_stocks = ['AMZN', 'TSLA', 'HD', 'NKE', 'SBUX', 'MCD', 'LOW']
        healthcare_stocks = ['UNH', 'JNJ', 'LLY', 'ABBV', 'TMO']
        energy_stocks = ['XOM', 'CVX', 'COP', 'SLB']
        
        ticker = ticker.upper()
        
        # Chercher dans chaque liste
        if ticker in tech_stocks:
            return 'technology'
        elif ticker in consumer_stocks:
            return 'consumer_discretionary'
        elif ticker in healthcare_stocks:
            return 'healthcare'
        elif ticker in energy_stocks:
            return 'energy'
        else:
            return None  # Secteur inconnu
    
    def is_stock_sector_favorable(self, ticker: str) -> tuple[bool, str]:
        """
        Vérifie si le secteur de l'action est favorable
        
        Une action a plus de chances de monter si son secteur
        est globalement en hausse.
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Tuple (is_favorable, sector_name):
            - is_favorable: True si le secteur est haussier
            - sector_name: Nom du secteur
        """
        # Trouver le secteur de l'action
        sector = self.get_sector_for_stock(ticker)
        
        if not sector:
            # Si secteur inconnu, on ne bloque pas
            # (on donne le bénéfice du doute)
            return True, 'unknown'
        
        # Récupérer l'ETF correspondant au secteur
        etf = SECTOR_ETFS.get(sector)
        if not etf:
            return True, sector
        
        # Vérifier si le secteur est haussier
        is_favorable = self.is_sector_bullish(etf)
        
        return is_favorable, sector
    
    # --------------------------------------------------------
    # SCORE GLOBAL DES SECTEURS
    # --------------------------------------------------------
    
    def get_sector_strength_score(self) -> int:
        """
        Calcule un score global de force des secteurs (0-100)
        
        Basé sur le pourcentage de secteurs qui sont haussiers.
        
        Exemple:
        - 11/11 secteurs haussiers = 100
        - 6/11 secteurs haussiers = 55
        - 0/11 secteurs haussiers = 0
        
        Returns:
            Score de 0 à 100
        """
        # Récupérer tous les secteurs
        all_sectors = self.get_all_sectors_status()
        
        if not all_sectors:
            return 50  # Score neutre si pas de données
        
        # Compter les secteurs haussiers
        bullish_count = sum(1 for s in all_sectors.values() if s['is_bullish'])
        total_count = len(all_sectors)
        
        # Calculer le pourcentage
        score = int((bullish_count / total_count) * 100)
        
        return score


# ============================================================
# CODE DE TEST
# ============================================================

if __name__ == '__main__':
    # Afficher en-tête
    print("\n" + "="*60)
    print("TEST MARKET SECTORS ANALYZER")
    print("="*60 + "\n")
    
    # Importer le provider
    from stock_data import StockDataProvider
    
    # Créer les instances
    provider = StockDataProvider()
    analyzer = MarketSectorsAnalyzer(provider)
    
    try:
        # Se connecter à IBKR
        provider.connect()
        
        # ---- Analyse de tous les secteurs ----
        print("📊 Analyse secteurs:\n")
        all_sectors = analyzer.get_all_sectors_status()
        
        for sector_name, data in all_sectors.items():
            # Emoji selon si haussier ou non
            emoji = "✅" if data['is_bullish'] else "❌"
            # Afficher le nom du secteur (aligné à gauche sur 25 caractères)
            print(f"{emoji} {sector_name.upper():<25} ({data['etf']})")
            print(f"   Prix: ${data['price']:.2f} | Var: {data['change_pct']:+.2f}%")
            print(f"   Volume ratio: {data['volume_ratio']:.2f}x | Tendance: {data['trend']}")
            print()
        
        # ---- Liste des secteurs haussiers ----
        bullish = analyzer.get_bullish_sectors()
        print(f"\n🚀 Secteurs haussiers ({len(bullish)}):")
        for sector in bullish:
            print(f"   • {sector['sector'].upper()} ({sector['etf']}): {sector['change_pct']:+.2f}%")
        
        # ---- Score global ----
        score = analyzer.get_sector_strength_score()
        print(f"\n🎯 Score force secteurs: {score}/100")
        
        # ---- Test sur une action spécifique ----
        test_ticker = 'AAPL'
        is_favorable, sector = analyzer.is_stock_sector_favorable(test_ticker)
        print(f"\n🔍 {test_ticker}:")
        print(f"   Secteur: {sector}")
        print(f"   Favorable: {'✅ Oui' if is_favorable else '❌ Non'}")
        
    finally:
        # Toujours se déconnecter
        provider.disconnect()
