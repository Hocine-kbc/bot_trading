"""
Filtres horaires - Vérification heures de trading
"""
from datetime import datetime, time
import pytz
from config import TIMEZONE, MARKET_OPEN, MARKET_CLOSE, EXCLUDED_START, EXCLUDED_END


class TimeFilters:
    """Filtres basés sur l'horaire"""
    
    def __init__(self):
        self.tz = pytz.timezone(TIMEZONE)
        self.market_open = datetime.strptime(MARKET_OPEN, '%H:%M').time()
        self.market_close = datetime.strptime(MARKET_CLOSE, '%H:%M').time()
        self.excluded_start = datetime.strptime(EXCLUDED_START, '%H:%M').time()
        self.excluded_end = datetime.strptime(EXCLUDED_END, '%H:%M').time()
    
    def get_current_time_et(self) -> datetime:
        """Retourne heure actuelle en ET"""
        return datetime.now(self.tz)
    
    def is_trading_hours(self) -> tuple[bool, str]:
        """
        Vérifie si on est dans les heures de marché
        
        Returns: (is_trading, reason)
        """
        now = self.get_current_time_et()
        current_time = now.time()
        
        # Vérifier jour de la semaine (Lun-Ven = 0-4)
        if now.weekday() > 4:
            return False, f"Weekend (jour {now.weekday()})"
        
        # Vérifier heures
        if current_time < self.market_open:
            return False, f"Marché pas encore ouvert (ouverture {MARKET_OPEN})"
        
        if current_time >= self.market_close:
            return False, f"Marché fermé (fermeture {MARKET_CLOSE})"
        
        return True, "OK"
    
    def is_excluded_time(self) -> tuple[bool, str]:
        """
        Vérifie si on est dans la période exclue (09:30-10:15)
        
        Returns: (is_excluded, reason)
        """
        now = self.get_current_time_et()
        current_time = now.time()
        
        if self.excluded_start <= current_time < self.excluded_end:
            return True, f"Période volatile exclue ({EXCLUDED_START}-{EXCLUDED_END})"
        
        return False, "OK"
    
    def can_trade_now(self) -> tuple[bool, str]:
        """
        Validation complète horaire
        
        Returns: (can_trade, reason)
        """
        # Vérifier heures de trading
        is_trading, reason = self.is_trading_hours()
        if not is_trading:
            return False, reason
        
        # Vérifier période exclue
        is_excluded, reason = self.is_excluded_time()
        if is_excluded:
            return False, reason
        
        return True, "OK"
    
    def get_time_until_open(self) -> int:
        """Retourne minutes jusqu'à l'ouverture"""
        now = self.get_current_time_et()
        current_time = now.time()
        
        if current_time < self.market_open:
            # Aujourd'hui
            open_today = now.replace(
                hour=self.market_open.hour,
                minute=self.market_open.minute,
                second=0
            )
            delta = open_today - now
            return int(delta.total_seconds() / 60)
        else:
            # Demain (ou prochain jour de semaine)
            days_ahead = 1
            if now.weekday() == 4:  # Vendredi
                days_ahead = 3
            elif now.weekday() == 5:  # Samedi
                days_ahead = 2
            
            # Estimation approximative
            return days_ahead * 24 * 60
    
    def get_time_until_excluded_end(self) -> int:
        """Retourne minutes jusqu'à la fin de la période exclue"""
        now = self.get_current_time_et()
        current_time = now.time()
        
        if self.excluded_start <= current_time < self.excluded_end:
            end_excluded = now.replace(
                hour=self.excluded_end.hour,
                minute=self.excluded_end.minute,
                second=0
            )
            delta = end_excluded - now
            return int(delta.total_seconds() / 60)
        
        return 0


# Instance globale
time_filters = TimeFilters()


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST TIME FILTERS")
    print("="*60 + "\n")
    
    filters = TimeFilters()
    
    now = filters.get_current_time_et()
    print(f"🕐 Heure actuelle (ET): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Jour semaine: {now.strftime('%A')}")
    print()
    
    # Test heures de trading
    is_trading, reason = filters.is_trading_hours()
    emoji = "✅" if is_trading else "❌"
    print(f"{emoji} Heures de trading: {reason}")
    
    # Test période exclue
    is_excluded, reason = filters.is_excluded_time()
    emoji = "✅" if not is_excluded else "❌"
    print(f"{emoji} Période autorisée: {reason}")
    
    # Test validation complète
    can_trade, reason = filters.can_trade_now()
    emoji = "✅" if can_trade else "❌"
    print(f"\n{emoji} PEUT TRADER: {reason}")
    
    if not can_trade:
        if not is_trading:
            minutes = filters.get_time_until_open()
            hours = minutes // 60
            mins = minutes % 60
            print(f"   ⏰ Ouverture dans: {hours}h {mins}min")
        elif is_excluded:
            minutes = filters.get_time_until_excluded_end()
            print(f"   ⏰ Fin période exclue dans: {minutes} min")

