"""
Gestion des watchlists (core + secondary)
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from config import (
    WATCHLIST_CORE_FILE,
    WATCHLIST_SECONDARY_FILE,
    BLACKLIST_FILE
)


class WatchlistManager:
    """Gestionnaire des watchlists et blacklist"""
    
    def __init__(self):
        self.core_watchlist = []
        self.secondary_watchlist = []
        self.blacklist = []
        self.load_all()
    
    def load_all(self):
        """Charge toutes les listes"""
        self.load_watchlist_core()
        self.load_watchlist_secondary()
        self.load_blacklist()
        self._filter_blacklisted()
    
    def load_watchlist_core(self):
        """Charge watchlist principale (leaders sectoriels)"""
        try:
            with open(WATCHLIST_CORE_FILE, 'r') as f:
                data = json.load(f)
            
            self.core_watchlist = []
            sectors = data.get('sectors', {})
            
            for sector_name, sector_data in sectors.items():
                stocks = sector_data.get('stocks', [])
                self.core_watchlist.extend(stocks)
            
            # Dédupliquer
            self.core_watchlist = list(set(self.core_watchlist))
            print(f"✅ Watchlist core chargée: {len(self.core_watchlist)} actions")
            
        except Exception as e:
            print(f"❌ Erreur chargement watchlist core: {e}")
            self.core_watchlist = []
    
    def load_watchlist_secondary(self):
        """Charge watchlist opportunités"""
        try:
            with open(WATCHLIST_SECONDARY_FILE, 'r') as f:
                data = json.load(f)
            
            self.secondary_watchlist = []
            categories = data.get('categories', {})
            
            for category_name, category_data in categories.items():
                stocks = category_data.get('stocks', [])
                self.secondary_watchlist.extend(stocks)
            
            # Dédupliquer
            self.secondary_watchlist = list(set(self.secondary_watchlist))
            print(f"✅ Watchlist secondary chargée: {len(self.secondary_watchlist)} actions")
            
        except Exception as e:
            print(f"❌ Erreur chargement watchlist secondary: {e}")
            self.secondary_watchlist = []
    
    def load_blacklist(self):
        """Charge la blacklist sectorielle"""
        try:
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
            
            self.blacklist = data.get('excluded_tickers', [])
            print(f"✅ Blacklist chargée: {len(self.blacklist)} tickers exclus")
            
        except Exception as e:
            print(f"❌ Erreur chargement blacklist: {e}")
            self.blacklist = []
    
    def _filter_blacklisted(self):
        """Retire les tickers blacklistés des watchlists"""
        before_core = len(self.core_watchlist)
        before_secondary = len(self.secondary_watchlist)
        
        self.core_watchlist = [t for t in self.core_watchlist if t not in self.blacklist]
        self.secondary_watchlist = [t for t in self.secondary_watchlist if t not in self.blacklist]
        
        removed_core = before_core - len(self.core_watchlist)
        removed_secondary = before_secondary - len(self.secondary_watchlist)
        
        if removed_core > 0:
            print(f"⚠️  {removed_core} tickers retirés de watchlist core (blacklistés)")
        if removed_secondary > 0:
            print(f"⚠️  {removed_secondary} tickers retirés de watchlist secondary (blacklistés)")
    
    def get_all_tickers(self) -> List[str]:
        """Retourne tous les tickers (core + secondary, sans blacklistés)"""
        all_tickers = list(set(self.core_watchlist + self.secondary_watchlist))
        return sorted(all_tickers)
    
    def is_in_watchlist(self, ticker: str) -> bool:
        """Vérifie si ticker est dans watchlist (core ou secondary)"""
        ticker = ticker.upper()
        return ticker in self.core_watchlist or ticker in self.secondary_watchlist
    
    def is_blacklisted(self, ticker: str) -> bool:
        """Vérifie si ticker est blacklisté"""
        ticker = ticker.upper()
        return ticker in self.blacklist
    
    def can_trade(self, ticker: str) -> tuple[bool, str]:
        """
        Vérifie si on peut trader ce ticker
        Returns: (bool, reason)
        """
        ticker = ticker.upper()
        
        if self.is_blacklisted(ticker):
            return False, f"{ticker} est blacklisté"
        
        if not self.is_in_watchlist(ticker):
            return False, f"{ticker} n'est pas dans la watchlist"
        
        return True, "OK"
    
    def add_to_secondary(self, ticker: str, category: str = 'momentum_leaders'):
        """Ajoute un ticker à la watchlist secondary"""
        ticker = ticker.upper()
        
        if self.is_blacklisted(ticker):
            print(f"❌ Impossible d'ajouter {ticker}: blacklisté")
            return False
        
        if ticker in self.secondary_watchlist:
            print(f"⚠️  {ticker} déjà dans watchlist secondary")
            return False
        
        try:
            with open(WATCHLIST_SECONDARY_FILE, 'r') as f:
                data = json.load(f)
            
            if category not in data['categories']:
                category = 'momentum_leaders'
            
            data['categories'][category]['stocks'].append(ticker)
            data['total_stocks'] = len(self.get_all_tickers()) + 1
            
            with open(WATCHLIST_SECONDARY_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.secondary_watchlist.append(ticker)
            print(f"✅ {ticker} ajouté à watchlist secondary ({category})")
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout {ticker}: {e}")
            return False
    
    def remove_from_secondary(self, ticker: str):
        """Retire un ticker de la watchlist secondary"""
        ticker = ticker.upper()
        
        if ticker not in self.secondary_watchlist:
            print(f"⚠️  {ticker} n'est pas dans watchlist secondary")
            return False
        
        try:
            with open(WATCHLIST_SECONDARY_FILE, 'r') as f:
                data = json.load(f)
            
            # Retirer de toutes les catégories
            for category_name, category_data in data['categories'].items():
                stocks = category_data.get('stocks', [])
                if ticker in stocks:
                    stocks.remove(ticker)
                    category_data['stocks'] = stocks
            
            data['total_stocks'] = len(self.get_all_tickers()) - 1
            
            with open(WATCHLIST_SECONDARY_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.secondary_watchlist.remove(ticker)
            print(f"✅ {ticker} retiré de watchlist secondary")
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression {ticker}: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Retourne statistiques watchlists"""
        return {
            'core_count': len(self.core_watchlist),
            'secondary_count': len(self.secondary_watchlist),
            'total_count': len(self.get_all_tickers()),
            'blacklist_count': len(self.blacklist)
        }


# Instance globale
watchlist_manager = WatchlistManager()


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST WATCHLIST MANAGER")
    print("="*60 + "\n")
    
    manager = WatchlistManager()
    
    stats = manager.get_stats()
    print(f"📊 Statistiques:")
    print(f"   - Core: {stats['core_count']}")
    print(f"   - Secondary: {stats['secondary_count']}")
    print(f"   - Total: {stats['total_count']}")
    print(f"   - Blacklist: {stats['blacklist_count']}")
    
    print(f"\n🔍 Tests:")
    test_tickers = ['AAPL', 'TSLA', 'JPM', 'UNKNOWN']
    
    for ticker in test_tickers:
        can_trade, reason = manager.can_trade(ticker)
        status = "✅" if can_trade else "❌"
        print(f"   {status} {ticker}: {reason}")

