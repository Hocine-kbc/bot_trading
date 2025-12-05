"""
Gestion des Watchlists
======================
Ce fichier gère les listes d'actions à surveiller:

1. WATCHLIST CORE: Les leaders sectoriels (grandes entreprises stables)
   → Apple, Microsoft, Google, Amazon, etc.

2. WATCHLIST SECONDARY: Les opportunités momentum
   → Actions plus petites avec potentiel de mouvement

3. BLACKLIST: Les actions à éviter
   → Secteurs exclus, actions problématiques
"""

# ============================================================
# IMPORTS
# ============================================================

import json  # Pour lire/écrire les fichiers JSON
from pathlib import Path  # Pour gérer les chemins de fichiers
from typing import List, Dict, Optional  # Pour typer les variables

# Chemins des fichiers depuis la configuration
from config import (
    WATCHLIST_CORE_FILE,      # Chemin vers watchlist_core.json
    WATCHLIST_SECONDARY_FILE,  # Chemin vers watchlist_secondary.json
    BLACKLIST_FILE            # Chemin vers blacklist_sectors.json
)


# ============================================================
# CLASSE PRINCIPALE - WatchlistManager
# ============================================================

class WatchlistManager:
    """
    Gestionnaire des watchlists et de la blacklist
    
    Permet de:
    - Charger les listes depuis les fichiers JSON
    - Vérifier si une action est dans la watchlist
    - Vérifier si une action est blacklistée
    - Ajouter/Retirer des actions de la watchlist secondary
    """
    
    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    
    def __init__(self):
        """
        Constructeur - Initialise les listes vides puis charge les données
        """
        self.core_watchlist = []      # Liste des tickers core
        self.secondary_watchlist = []  # Liste des tickers secondary
        self.blacklist = []           # Liste des tickers à éviter
        self.load_all()               # Charger toutes les listes
    
    # --------------------------------------------------------
    # CHARGEMENT DES DONNÉES
    # --------------------------------------------------------
    
    def load_all(self):
        """
        Charge toutes les listes depuis les fichiers JSON
        Puis filtre les tickers blacklistés des watchlists
        """
        self.load_watchlist_core()       # Charger watchlist principale
        self.load_watchlist_secondary()   # Charger watchlist secondaire
        self.load_blacklist()            # Charger blacklist
        self._filter_blacklisted()       # Retirer les blacklistés des watchlists
    
    def load_watchlist_core(self):
        """
        Charge la watchlist principale (leaders sectoriels)
        
        Le fichier JSON est organisé par secteurs:
        {
            "sectors": {
                "technology": { "stocks": ["AAPL", "MSFT", ...] },
                "healthcare": { "stocks": ["JNJ", "PFE", ...] },
                ...
            }
        }
        """
        try:
            # Ouvrir et lire le fichier JSON
            with open(WATCHLIST_CORE_FILE, 'r') as f:
                data = json.load(f)
            
            self.core_watchlist = []  # Réinitialiser la liste
            sectors = data.get('sectors', {})  # Récupérer les secteurs
            
            # Parcourir chaque secteur et ajouter ses actions
            for sector_name, sector_data in sectors.items():
                stocks = sector_data.get('stocks', [])
                self.core_watchlist.extend(stocks)  # extend = ajouter plusieurs éléments
            
            # Dédupliquer (retirer les doublons)
            # set() crée un ensemble (pas de doublons), puis list() reconvertit en liste
            self.core_watchlist = list(set(self.core_watchlist))
            print(f"✅ Watchlist core chargée: {len(self.core_watchlist)} actions")
            
        except Exception as e:
            print(f"❌ Erreur chargement watchlist core: {e}")
            self.core_watchlist = []
    
    def load_watchlist_secondary(self):
        """
        Charge la watchlist secondaire (opportunités momentum)
        
        Structure similaire mais organisée par catégories:
        {
            "categories": {
                "momentum_leaders": { "stocks": [...] },
                "earnings_plays": { "stocks": [...] },
                ...
            }
        }
        """
        try:
            with open(WATCHLIST_SECONDARY_FILE, 'r') as f:
                data = json.load(f)
            
            self.secondary_watchlist = []
            categories = data.get('categories', {})
            
            # Parcourir chaque catégorie
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
        """
        Charge la blacklist (secteurs et tickers à éviter)
        
        Structure:
        {
            "excluded_tickers": ["BAD1", "BAD2", ...]
        }
        """
        try:
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
            
            # Récupérer la liste des tickers exclus
            self.blacklist = data.get('excluded_tickers', [])
            print(f"✅ Blacklist chargée: {len(self.blacklist)} tickers exclus")
            
        except Exception as e:
            print(f"❌ Erreur chargement blacklist: {e}")
            self.blacklist = []
    
    def _filter_blacklisted(self):
        """
        Retire les tickers blacklistés des watchlists
        
        Cette méthode est appelée après le chargement pour s'assurer
        qu'aucun ticker blacklisté ne reste dans les watchlists
        """
        # Sauvegarder les compteurs avant filtrage
        before_core = len(self.core_watchlist)
        before_secondary = len(self.secondary_watchlist)
        
        # Filtrer: garder seulement les tickers qui ne sont PAS dans la blacklist
        # List comprehension: [x for x in liste if condition]
        self.core_watchlist = [t for t in self.core_watchlist if t not in self.blacklist]
        self.secondary_watchlist = [t for t in self.secondary_watchlist if t not in self.blacklist]
        
        # Calculer combien ont été retirés
        removed_core = before_core - len(self.core_watchlist)
        removed_secondary = before_secondary - len(self.secondary_watchlist)
        
        # Afficher un avertissement si des tickers ont été retirés
        if removed_core > 0:
            print(f"⚠️  {removed_core} tickers retirés de watchlist core (blacklistés)")
        if removed_secondary > 0:
            print(f"⚠️  {removed_secondary} tickers retirés de watchlist secondary (blacklistés)")
    
    # --------------------------------------------------------
    # MÉTHODES DE LECTURE
    # --------------------------------------------------------
    
    def get_all_tickers(self) -> List[str]:
        """
        Retourne tous les tickers (core + secondary), sans doublons
        
        Returns:
            Liste triée de tous les tickers à surveiller
        """
        # Fusionner les deux listes et dédupliquer
        all_tickers = list(set(self.core_watchlist + self.secondary_watchlist))
        return sorted(all_tickers)  # Trier par ordre alphabétique
    
    def is_in_watchlist(self, ticker: str) -> bool:
        """
        Vérifie si un ticker est dans une des watchlists
        
        Args:
            ticker: Le symbole de l'action (ex: 'AAPL')
        
        Returns:
            True si le ticker est dans core OU secondary
        """
        ticker = ticker.upper()  # Convertir en majuscules pour comparaison
        return ticker in self.core_watchlist or ticker in self.secondary_watchlist
    
    def is_blacklisted(self, ticker: str) -> bool:
        """
        Vérifie si un ticker est dans la blacklist
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            True si le ticker est blacklisté (à éviter)
        """
        ticker = ticker.upper()
        return ticker in self.blacklist
    
    def can_trade(self, ticker: str) -> tuple[bool, str]:
        """
        Vérifie si on peut trader ce ticker
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Tuple (bool, str):
            - bool: True si on peut trader, False sinon
            - str: Raison (utile pour le debug)
        """
        ticker = ticker.upper()
        
        # Vérifier d'abord si blacklisté
        if self.is_blacklisted(ticker):
            return False, f"{ticker} est blacklisté"
        
        # Vérifier si dans une watchlist
        if not self.is_in_watchlist(ticker):
            return False, f"{ticker} n'est pas dans la watchlist"
        
        return True, "OK"
    
    # --------------------------------------------------------
    # MÉTHODES DE MODIFICATION
    # --------------------------------------------------------
    
    def add_to_secondary(self, ticker: str, category: str = 'momentum_leaders'):
        """
        Ajoute un ticker à la watchlist secondary
        
        Args:
            ticker: Le symbole de l'action
            category: La catégorie où l'ajouter (défaut: momentum_leaders)
        
        Returns:
            True si ajouté avec succès, False sinon
        """
        ticker = ticker.upper()
        
        # Vérifier qu'il n'est pas blacklisté
        if self.is_blacklisted(ticker):
            print(f"❌ Impossible d'ajouter {ticker}: blacklisté")
            return False
        
        # Vérifier qu'il n'est pas déjà présent
        if ticker in self.secondary_watchlist:
            print(f"⚠️  {ticker} déjà dans watchlist secondary")
            return False
        
        try:
            # Lire le fichier JSON actuel
            with open(WATCHLIST_SECONDARY_FILE, 'r') as f:
                data = json.load(f)
            
            # Vérifier que la catégorie existe, sinon utiliser la défaut
            if category not in data['categories']:
                category = 'momentum_leaders'
            
            # Ajouter le ticker à la catégorie
            data['categories'][category]['stocks'].append(ticker)
            
            # Mettre à jour le compteur total
            data['total_stocks'] = len(self.get_all_tickers()) + 1
            
            # Sauvegarder le fichier
            with open(WATCHLIST_SECONDARY_FILE, 'w') as f:
                json.dump(data, f, indent=2)  # indent=2 pour un JSON lisible
            
            # Mettre à jour la liste en mémoire
            self.secondary_watchlist.append(ticker)
            print(f"✅ {ticker} ajouté à watchlist secondary ({category})")
            return True
            
        except Exception as e:
            print(f"❌ Erreur ajout {ticker}: {e}")
            return False
    
    def remove_from_secondary(self, ticker: str):
        """
        Retire un ticker de la watchlist secondary
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            True si retiré avec succès, False sinon
        """
        ticker = ticker.upper()
        
        # Vérifier qu'il est présent
        if ticker not in self.secondary_watchlist:
            print(f"⚠️  {ticker} n'est pas dans watchlist secondary")
            return False
        
        try:
            # Lire le fichier JSON
            with open(WATCHLIST_SECONDARY_FILE, 'r') as f:
                data = json.load(f)
            
            # Retirer de toutes les catégories (au cas où il serait dans plusieurs)
            for category_name, category_data in data['categories'].items():
                stocks = category_data.get('stocks', [])
                if ticker in stocks:
                    stocks.remove(ticker)
                    category_data['stocks'] = stocks
            
            # Mettre à jour le compteur
            data['total_stocks'] = len(self.get_all_tickers()) - 1
            
            # Sauvegarder
            with open(WATCHLIST_SECONDARY_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Mettre à jour la liste en mémoire
            self.secondary_watchlist.remove(ticker)
            print(f"✅ {ticker} retiré de watchlist secondary")
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression {ticker}: {e}")
            return False
    
    # --------------------------------------------------------
    # STATISTIQUES
    # --------------------------------------------------------
    
    def get_stats(self) -> Dict:
        """
        Retourne les statistiques des watchlists
        
        Returns:
            Dictionnaire avec les compteurs
        """
        return {
            'core_count': len(self.core_watchlist),        # Nombre dans core
            'secondary_count': len(self.secondary_watchlist),  # Nombre dans secondary
            'total_count': len(self.get_all_tickers()),    # Total unique
            'blacklist_count': len(self.blacklist)         # Nombre blacklistés
        }


# ============================================================
# INSTANCE GLOBALE
# ============================================================

# Créer une instance globale
# Usage: from watchlist_manager import watchlist_manager
watchlist_manager = WatchlistManager()


# ============================================================
# CODE DE TEST
# ============================================================

if __name__ == '__main__':
    # Afficher en-tête
    print("\n" + "="*60)
    print("TEST WATCHLIST MANAGER")
    print("="*60 + "\n")
    
    # Créer un manager pour les tests
    manager = WatchlistManager()
    
    # Afficher les statistiques
    stats = manager.get_stats()
    print(f"📊 Statistiques:")
    print(f"   - Core: {stats['core_count']}")
    print(f"   - Secondary: {stats['secondary_count']}")
    print(f"   - Total: {stats['total_count']}")
    print(f"   - Blacklist: {stats['blacklist_count']}")
    
    # Tester quelques tickers
    print(f"\n🔍 Tests:")
    test_tickers = ['AAPL', 'TSLA', 'JPM', 'UNKNOWN']
    
    for ticker in test_tickers:
        can_trade, reason = manager.can_trade(ticker)
        status = "✅" if can_trade else "❌"
        print(f"   {status} {ticker}: {reason}")
