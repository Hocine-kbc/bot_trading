"""
Filtres de Trading - Validation Complète
========================================
Ce fichier regroupe TOUS les filtres utilisés par le bot pour
décider si on peut acheter une action ou non.

Filtres disponibles:
1. Watchlist: L'action est-elle dans notre liste ?
2. Time: Sommes-nous dans les heures de trading ?
3. Earnings: Y a-t-il des résultats à venir ?
4. Market: Le marché global est-il favorable ?
5. Sector: Le secteur de l'action est-il en hausse ?
6. Stock: L'action elle-même montre-t-elle des signaux positifs ?
7. News: Y a-t-il des news négatives ?
8. Downgrade: Y a-t-il eu un downgrade récent ?
9. Spread: Le spread bid-ask est-il acceptable ?

Pour qu'un achat soit validé, TOUS les filtres doivent passer !
"""

# ============================================================
# IMPORTS
# ============================================================

from typing import Dict, Optional  # Pour typer les variables
import pandas as pd  # Pour manipuler les données

# Nos modules
from filters_time import TimeFilters  # Filtres horaires
from news_monitor import NewsMonitor  # Surveillance des news
from market_indices import MarketIndicesAnalyzer  # Analyse indices
from market_sectors import MarketSectorsAnalyzer  # Analyse secteurs
from stock_data import StockDataProvider  # Données boursières
from watchlist_manager import WatchlistManager  # Gestion watchlist

# Nos paramètres
from config import (
    DOJI_BODY_PCT,        # Seuil pour détecter un doji (20%)
    HIGH_WICK_PCT,        # Seuil mèche haute (50%)
    MIN_VOLUME_MULTIPLIER,  # Volume minimum (1.2x)
    SPREAD_MAX_PCT        # Spread maximum (0.5%)
)


# ============================================================
# CLASSE PRINCIPALE - TradingFilters
# ============================================================

class TradingFilters:
    """
    Ensemble complet des filtres de trading
    
    Cette classe centralise tous les filtres et permet de
    valider rapidement si une action est bonne à acheter.
    """
    
    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    
    def __init__(
        self,
        data_provider: StockDataProvider,
        watchlist_manager: WatchlistManager,
        news_monitor: NewsMonitor,
        market_analyzer: MarketIndicesAnalyzer,
        sector_analyzer: MarketSectorsAnalyzer
    ):
        """
        Constructeur - Reçoit toutes les dépendances nécessaires
        
        Args:
            data_provider: Pour récupérer les données boursières
            watchlist_manager: Pour vérifier la watchlist
            news_monitor: Pour vérifier les news
            market_analyzer: Pour analyser le marché global
            sector_analyzer: Pour analyser les secteurs
        """
        self.data_provider = data_provider
        self.watchlist_manager = watchlist_manager
        self.news_monitor = news_monitor
        self.market_analyzer = market_analyzer
        self.sector_analyzer = sector_analyzer
        self.time_filters = TimeFilters()  # Créer un objet pour les filtres horaires
    
    # --------------------------------------------------------
    # FILTRE 1: WATCHLIST
    # --------------------------------------------------------
    
    def filter_watchlist(self, ticker: str) -> tuple[bool, str]:
        """
        Filtre: L'action est-elle dans la watchlist et non blacklistée ?
        
        On ne trade que les actions de notre watchlist.
        Les actions blacklistées sont automatiquement refusées.
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Tuple (passed, reason)
        """
        return self.watchlist_manager.can_trade(ticker)
    
    # --------------------------------------------------------
    # FILTRE 2: HORAIRES
    # --------------------------------------------------------
    
    def filter_time(self) -> tuple[bool, str]:
        """
        Filtre: Sommes-nous dans les horaires de trading valides ?
        
        On ne trade que:
        - Du lundi au vendredi
        - Entre 10:15 et 16:00 (ET)
        - Pas pendant les premières 45 minutes
        
        Returns:
            Tuple (passed, reason)
        """
        return self.time_filters.can_trade_now()
    
    # --------------------------------------------------------
    # FILTRE 3: EARNINGS
    # --------------------------------------------------------
    
    def filter_earnings(self, ticker: str, hours: int = 48) -> tuple[bool, str]:
        """
        Filtre: L'action a-t-elle des earnings dans les prochaines X heures ?
        
        On évite d'acheter avant les résultats trimestriels car
        le cours peut bouger de +/- 10-20% après l'annonce.
        
        Args:
            ticker: Le symbole de l'action
            hours: Nombre d'heures à vérifier (défaut: 48h)
        
        Returns:
            Tuple (passed, reason)
        """
        # Vérifier si earnings dans la période
        has_earnings, info = self.news_monitor.has_earnings_soon(ticker, hours)
        
        if has_earnings:
            return False, f"Earnings dans {info['hours_until']:.1f}h"
        
        return True, "OK"
    
    # --------------------------------------------------------
    # FILTRE 4: ÉMOTION DU MARCHÉ
    # --------------------------------------------------------
    
    def filter_market_emotion(self) -> tuple[bool, str]:
        """
        Filtre: Le marché global est-il favorable ?
        
        Conditions pour un marché favorable:
        - SPY en hausse (>= 0.3%)
        - QQQ en hausse (>= 0.3%)
        - VIX bas (< 25)
        
        Si le marché est baissier, on n'achète rien !
        
        Returns:
            Tuple (passed, reason)
        """
        # Vérifier si le marché est haussier
        is_bullish, details = self.market_analyzer.is_market_bullish()
        
        if not is_bullish:
            # Identifier la cause du problème
            if 'error' in details:
                return False, f"Erreur données marché: {details['error']}"
            
            # Lister les conditions qui ont échoué
            conditions = details.get('conditions', {})
            failed = [k for k, v in conditions.items() if not v]
            return False, f"Marché non favorable: {', '.join(failed)}"
        
        return True, "OK"
    
    # --------------------------------------------------------
    # FILTRE 5: ÉMOTION DU SECTEUR
    # --------------------------------------------------------
    
    def filter_sector_emotion(self, ticker: str) -> tuple[bool, str]:
        """
        Filtre: Le secteur de l'action est-il haussier ?
        
        Conditions:
        - ETF du secteur en hausse (> 0.5%)
        - Volume de l'ETF > moyenne
        
        Une action a plus de chances de monter si son secteur est fort.
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Tuple (passed, reason)
        """
        # Vérifier si le secteur est favorable
        is_favorable, sector = self.sector_analyzer.is_stock_sector_favorable(ticker)
        
        if not is_favorable:
            return False, f"Secteur {sector} non haussier"
        
        return True, f"Secteur {sector} favorable"
    
    # --------------------------------------------------------
    # FILTRE 6: ÉMOTION DE L'ACTION
    # --------------------------------------------------------
    
    def filter_stock_emotion(self, ticker: str) -> tuple[bool, str]:
        """
        Filtre: L'action montre-t-elle des signaux positifs ?
        
        On REFUSE si:
        - Doji détecté (corps < 20% du range) → indécision
        - Mèche haute excessive (> 50% du range) → pression vendeuse
        - Volume très faible (< 50% de la moyenne) → pas d'intérêt
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Tuple (passed, reason)
        """
        try:
            # Récupérer les données OHLCV
            df = self.data_provider.get_ohlcv(ticker, '5 mins', '1 D')
            if df is None or df.empty:
                return False, "Pas de données"
            
            # Récupérer la dernière bougie
            last = df.iloc[-1]
            
            # ---- Vérifier si c'est un Doji ----
            # Un doji = corps très petit = indécision du marché
            body = abs(last['close'] - last['open'])  # Taille du corps
            total_range = last['high'] - last['low']  # Range total
            
            if total_range == 0:
                return False, "Range nulle (suspect)"
            
            body_pct = body / total_range  # % du corps par rapport au range
            
            if body_pct < DOJI_BODY_PCT:  # Si corps < 20% → doji
                return False, f"Doji détecté (body {body_pct*100:.1f}%)"
            
            # ---- Vérifier la mèche haute ----
            # Une grande mèche haute = pression vendeuse
            upper_shadow = last['high'] - max(last['open'], last['close'])
            upper_shadow_pct = upper_shadow / total_range
            
            if upper_shadow_pct > HIGH_WICK_PCT:  # Si mèche > 50% → dangereux
                return False, f"Mèche haute excessive ({upper_shadow_pct*100:.1f}%)"
            
            # ---- Vérifier le volume ----
            # Un volume faible = pas d'intérêt des traders
            recent = df.tail(20)
            avg_volume = recent['volume'].iloc[:-1].mean()  # Volume moyen
            
            if last['volume'] < avg_volume * 0.5:  # Si volume < 50% moyenne
                return False, f"Volume faible ({last['volume']/avg_volume*100:.0f}% moy)"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    # --------------------------------------------------------
    # FILTRE 7: NEWS NÉGATIVES
    # --------------------------------------------------------
    
    def filter_negative_news(self, ticker: str, minutes: int = 30) -> tuple[bool, str]:
        """
        Filtre: Y a-t-il des news négatives récentes ?
        
        On refuse d'acheter si des news négatives sont apparues
        dans les dernières X minutes (procès, fraude, etc.)
        
        Args:
            ticker: Le symbole de l'action
            minutes: Période à vérifier (défaut: 30 min)
        
        Returns:
            Tuple (passed, reason)
        """
        # Vérifier les news négatives
        has_negative, news_list = self.news_monitor.has_negative_news(ticker, minutes)
        
        if has_negative:
            return False, f"{len(news_list)} news négative(s) récente(s)"
        
        return True, "OK"
    
    # --------------------------------------------------------
    # FILTRE 8: DOWNGRADE
    # --------------------------------------------------------
    
    def filter_downgrade(self, ticker: str, days: int = 1) -> tuple[bool, str]:
        """
        Filtre: Y a-t-il eu un downgrade récent ?
        
        Un downgrade = un analyste dégrade sa note sur l'action.
        C'est un signal négatif, on évite d'acheter.
        
        Args:
            ticker: Le symbole de l'action
            days: Période à vérifier (défaut: 1 jour)
        
        Returns:
            Tuple (passed, reason)
        """
        # Vérifier les downgrades
        has_downgrade, downgrades = self.news_monitor.has_recent_downgrade(ticker, days)
        
        if has_downgrade:
            return False, f"{len(downgrades)} downgrade(s) récent(s)"
        
        return True, "OK"
    
    # --------------------------------------------------------
    # FILTRE 9: SPREAD
    # --------------------------------------------------------
    
    def filter_spread(self, ticker: str) -> tuple[bool, str]:
        """
        Filtre: Le spread bid-ask est-il acceptable ?
        
        Le spread = écart entre prix d'achat (ask) et prix de vente (bid).
        Un spread élevé = coût de transaction élevé = mauvais pour nous.
        
        On refuse si spread > 0.5%
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Tuple (passed, reason)
        """
        try:
            # Récupérer l'orderflow
            orderflow = self.data_provider.get_orderflow(ticker)
            if not orderflow:
                return False, "Pas de données orderflow"
            
            # Vérifier le spread
            spread_pct = orderflow['spread_pct']
            
            if spread_pct > SPREAD_MAX_PCT * 100:  # Si spread > 0.5%
                return False, f"Spread trop large ({spread_pct:.2f}%)"
            
            return True, f"Spread OK ({spread_pct:.2f}%)"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    # --------------------------------------------------------
    # VALIDATION COMPLÈTE
    # --------------------------------------------------------
    
    def validate_all_filters(self, ticker: str) -> tuple[bool, Dict]:
        """
        Validation COMPLÈTE de tous les filtres
        
        Exécute tous les filtres et retourne le résultat global.
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Tuple (all_passed, results_dict):
            - all_passed: True si TOUS les filtres sont passés
            - results_dict: Détail de chaque filtre
        """
        results = {}
        
        # Filtre 1: Watchlist & Blacklist
        passed, reason = self.filter_watchlist(ticker)
        results['watchlist'] = {'passed': passed, 'reason': reason}
        
        # Filtre 2: Horaires
        passed, reason = self.filter_time()
        results['time'] = {'passed': passed, 'reason': reason}
        
        # Filtre 3: Earnings
        passed, reason = self.filter_earnings(ticker)
        results['earnings'] = {'passed': passed, 'reason': reason}
        
        # Filtre 4: Marché
        passed, reason = self.filter_market_emotion()
        results['market'] = {'passed': passed, 'reason': reason}
        
        # Filtre 5: Secteur
        passed, reason = self.filter_sector_emotion(ticker)
        results['sector'] = {'passed': passed, 'reason': reason}
        
        # Filtre 6: Action
        passed, reason = self.filter_stock_emotion(ticker)
        results['stock'] = {'passed': passed, 'reason': reason}
        
        # Filtre 7: News négatives
        passed, reason = self.filter_negative_news(ticker)
        results['negative_news'] = {'passed': passed, 'reason': reason}
        
        # Filtre 8: Downgrade
        passed, reason = self.filter_downgrade(ticker)
        results['downgrade'] = {'passed': passed, 'reason': reason}
        
        # Filtre 9: Spread
        passed, reason = self.filter_spread(ticker)
        results['spread'] = {'passed': passed, 'reason': reason}
        
        # Vérifier si TOUS les filtres sont passés
        # all() retourne True si toutes les valeurs sont True
        all_passed = all(r['passed'] for r in results.values())
        
        return all_passed, results
    
    def get_failed_filters(self, results: Dict) -> list:
        """
        Retourne la liste des filtres qui ont échoué
        
        Utile pour comprendre pourquoi une action a été refusée.
        
        Args:
            results: Le dictionnaire retourné par validate_all_filters()
        
        Returns:
            Liste des raisons d'échec
        """
        failed = [
            f"{name}: {data['reason']}"
            for name, data in results.items()
            if not data['passed']  # Garder seulement les échecs
        ]
        return failed


# ============================================================
# CODE DE TEST
# ============================================================

if __name__ == '__main__':
    # Afficher en-tête
    print("\n" + "="*60)
    print("TEST TRADING FILTERS")
    print("="*60 + "\n")
    
    # Importer les dépendances
    from stock_data import StockDataProvider
    from watchlist_manager import WatchlistManager
    from news_monitor import NewsMonitor
    from market_indices import MarketIndicesAnalyzer
    from market_sectors import MarketSectorsAnalyzer
    
    # Créer les instances
    provider = StockDataProvider()
    watchlist_mgr = WatchlistManager()
    news_mon = NewsMonitor()
    market_analyzer = MarketIndicesAnalyzer(provider)
    sector_analyzer = MarketSectorsAnalyzer(provider)
    
    # Créer l'objet TradingFilters
    filters = TradingFilters(
        provider,
        watchlist_mgr,
        news_mon,
        market_analyzer,
        sector_analyzer
    )
    
    # Ticker à tester
    test_ticker = 'AAPL'
    
    try:
        # Se connecter à IBKR
        provider.connect()
        
        print(f"🔍 Validation filtres pour {test_ticker}:\n")
        
        # Exécuter tous les filtres
        all_passed, results = filters.validate_all_filters(test_ticker)
        
        # Afficher le résultat de chaque filtre
        for filter_name, data in results.items():
            emoji = "✅" if data['passed'] else "❌"
            # :<20 = aligné à gauche sur 20 caractères
            print(f"{emoji} {filter_name:<20} {data['reason']}")
        
        # Afficher le résumé
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
        # Toujours se déconnecter
        provider.disconnect()
