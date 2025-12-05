"""
Filtres Horaires - Vérification des Heures de Trading
=====================================================
Ce fichier gère les filtres basés sur le temps:

1. Heures de marché US: 09:30 - 16:00 (heure de New York)
2. Jours ouvrables: Lundi à Vendredi (pas de weekend)
3. Période exclue: 09:30 - 10:15 (trop volatile à l'ouverture)

Le bot n'achète que pendant les heures favorables !
"""

# ============================================================
# IMPORTS
# ============================================================

from datetime import datetime, time  # Pour manipuler dates et heures
import pytz  # Pour gérer les fuseaux horaires

# Nos paramètres depuis la configuration
from config import TIMEZONE, MARKET_OPEN, MARKET_CLOSE, EXCLUDED_START, EXCLUDED_END


# ============================================================
# CLASSE PRINCIPALE - TimeFilters
# ============================================================

class TimeFilters:
    """
    Filtres basés sur l'horaire
    
    Permet de:
    - Vérifier si on est dans les heures de marché
    - Éviter la période volatile de l'ouverture
    - Calculer le temps restant avant ouverture
    """
    
    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    
    def __init__(self):
        """
        Constructeur - Initialise les heures de référence
        """
        # Créer l'objet timezone pour New York
        self.tz = pytz.timezone(TIMEZONE)
        
        # Convertir les strings en objets time
        # strptime = string parse time (convertit string → datetime)
        # .time() extrait juste l'heure (sans la date)
        self.market_open = datetime.strptime(MARKET_OPEN, '%H:%M').time()    # 09:30
        self.market_close = datetime.strptime(MARKET_CLOSE, '%H:%M').time()  # 16:00
        self.excluded_start = datetime.strptime(EXCLUDED_START, '%H:%M').time()  # 09:30
        self.excluded_end = datetime.strptime(EXCLUDED_END, '%H:%M').time()      # 10:15
    
    # --------------------------------------------------------
    # HEURE ACTUELLE
    # --------------------------------------------------------
    
    def get_current_time_et(self) -> datetime:
        """
        Retourne l'heure actuelle en Eastern Time (New York)
        
        Le marché US fonctionne sur le fuseau horaire de New York.
        Il faut toujours utiliser cette heure pour les comparaisons.
        
        Returns:
            datetime avec le fuseau horaire de New York
        """
        return datetime.now(self.tz)
    
    # --------------------------------------------------------
    # VÉRIFICATION DES HEURES DE MARCHÉ
    # --------------------------------------------------------
    
    def is_trading_hours(self) -> tuple[bool, str]:
        """
        Vérifie si on est dans les heures de marché
        
        Conditions:
        - Jour de semaine (Lundi à Vendredi)
        - Après 09:30 ET
        - Avant 16:00 ET
        
        Returns:
            Tuple (is_trading, reason)
        """
        # Obtenir l'heure actuelle à New York
        now = self.get_current_time_et()
        current_time = now.time()  # Extraire juste l'heure
        
        # Vérifier le jour de la semaine
        # weekday() retourne: 0=Lundi, 1=Mardi, ..., 4=Vendredi, 5=Samedi, 6=Dimanche
        if now.weekday() > 4:  # Si samedi (5) ou dimanche (6)
            return False, f"Weekend (jour {now.weekday()})"
        
        # Vérifier si avant l'ouverture
        if current_time < self.market_open:
            return False, f"Marché pas encore ouvert (ouverture {MARKET_OPEN})"
        
        # Vérifier si après la fermeture
        if current_time >= self.market_close:
            return False, f"Marché fermé (fermeture {MARKET_CLOSE})"
        
        return True, "OK"
    
    # --------------------------------------------------------
    # VÉRIFICATION DE LA PÉRIODE EXCLUE
    # --------------------------------------------------------
    
    def is_excluded_time(self) -> tuple[bool, str]:
        """
        Vérifie si on est dans la période exclue (09:30-10:15)
        
        Pourquoi exclure cette période ?
        - Les premières 45 minutes après l'ouverture sont très volatiles
        - Les ordres overnight sont exécutés
        - Les institutionnels passent leurs gros ordres
        - Beaucoup de faux signaux pendant cette période
        
        Returns:
            Tuple (is_excluded, reason)
        """
        now = self.get_current_time_et()
        current_time = now.time()
        
        # Vérifier si entre 09:30 et 10:15
        if self.excluded_start <= current_time < self.excluded_end:
            return True, f"Période volatile exclue ({EXCLUDED_START}-{EXCLUDED_END})"
        
        return False, "OK"
    
    # --------------------------------------------------------
    # VALIDATION COMPLÈTE
    # --------------------------------------------------------
    
    def can_trade_now(self) -> tuple[bool, str]:
        """
        Validation complète: peut-on trader maintenant ?
        
        Vérifie:
        1. On est dans les heures de marché
        2. On n'est PAS dans la période exclue
        
        Returns:
            Tuple (can_trade, reason)
        """
        # Étape 1: Vérifier les heures de marché
        is_trading, reason = self.is_trading_hours()
        if not is_trading:
            return False, reason
        
        # Étape 2: Vérifier qu'on n'est pas dans la période exclue
        is_excluded, reason = self.is_excluded_time()
        if is_excluded:
            return False, reason
        
        return True, "OK"
    
    # --------------------------------------------------------
    # CALCULS DE TEMPS
    # --------------------------------------------------------
    
    def get_time_until_open(self) -> int:
        """
        Calcule le nombre de minutes jusqu'à l'ouverture du marché
        
        Utile pour savoir quand le bot pourra commencer à trader.
        
        Returns:
            Nombre de minutes jusqu'à l'ouverture
        """
        now = self.get_current_time_et()
        current_time = now.time()
        
        # Si on est avant l'ouverture aujourd'hui
        if current_time < self.market_open:
            # Créer un datetime pour l'ouverture d'aujourd'hui
            open_today = now.replace(
                hour=self.market_open.hour,
                minute=self.market_open.minute,
                second=0
            )
            # Calculer la différence
            delta = open_today - now
            return int(delta.total_seconds() / 60)  # Convertir secondes en minutes
        else:
            # Le marché est fermé ou c'est le weekend
            # Calculer le nombre de jours jusqu'au prochain jour ouvré
            days_ahead = 1
            if now.weekday() == 4:  # Vendredi → prochain = Lundi (3 jours)
                days_ahead = 3
            elif now.weekday() == 5:  # Samedi → prochain = Lundi (2 jours)
                days_ahead = 2
            
            # Estimation approximative en minutes
            return days_ahead * 24 * 60
    
    def get_time_until_excluded_end(self) -> int:
        """
        Calcule le nombre de minutes jusqu'à la fin de la période exclue
        
        Utile pour savoir quand le bot pourra commencer à acheter
        après l'ouverture du marché.
        
        Returns:
            Nombre de minutes jusqu'à 10:15
        """
        now = self.get_current_time_et()
        current_time = now.time()
        
        # Seulement si on est dans la période exclue
        if self.excluded_start <= current_time < self.excluded_end:
            # Créer un datetime pour la fin de la période exclue
            end_excluded = now.replace(
                hour=self.excluded_end.hour,
                minute=self.excluded_end.minute,
                second=0
            )
            # Calculer la différence
            delta = end_excluded - now
            return int(delta.total_seconds() / 60)
        
        return 0  # Pas dans la période exclue


# ============================================================
# INSTANCE GLOBALE
# ============================================================

# Créer une instance globale
# Usage: from filters_time import time_filters
time_filters = TimeFilters()


# ============================================================
# CODE DE TEST
# ============================================================

if __name__ == '__main__':
    # Afficher en-tête
    print("\n" + "="*60)
    print("TEST TIME FILTERS")
    print("="*60 + "\n")
    
    # Créer un objet TimeFilters pour les tests
    filters = TimeFilters()
    
    # Afficher l'heure actuelle à New York
    now = filters.get_current_time_et()
    print(f"🕐 Heure actuelle (ET): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Jour semaine: {now.strftime('%A')}")  # Nom du jour en anglais
    print()
    
    # Test 1: Heures de trading
    is_trading, reason = filters.is_trading_hours()
    emoji = "✅" if is_trading else "❌"
    print(f"{emoji} Heures de trading: {reason}")
    
    # Test 2: Période exclue
    is_excluded, reason = filters.is_excluded_time()
    emoji = "✅" if not is_excluded else "❌"  # Note: ✅ si PAS exclu
    print(f"{emoji} Période autorisée: {reason}")
    
    # Test 3: Validation complète
    can_trade, reason = filters.can_trade_now()
    emoji = "✅" if can_trade else "❌"
    print(f"\n{emoji} PEUT TRADER: {reason}")
    
    # Si on ne peut pas trader, afficher quand on pourra
    if not can_trade:
        if not is_trading:
            minutes = filters.get_time_until_open()
            hours = minutes // 60  # Division entière
            mins = minutes % 60    # Reste (modulo)
            print(f"   ⏰ Ouverture dans: {hours}h {mins}min")
        elif is_excluded:
            minutes = filters.get_time_until_excluded_end()
            print(f"   ⏰ Fin période exclue dans: {minutes} min")
