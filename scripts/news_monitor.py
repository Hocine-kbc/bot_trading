"""
Surveillance news via Benzinga Pro API
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz
from config import BENZINGA_API_KEY, TIMEZONE, NEGATIVE_KEYWORDS


class NewsMonitor:
    """Surveillance des news via Benzinga"""
    
    def __init__(self):
        self.api_key = BENZINGA_API_KEY
        self.base_url = "https://api.benzinga.com/api/v2.1"
        self.tz = pytz.timezone(TIMEZONE)
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Requête API Benzinga"""
        try:
            params['token'] = self.api_key
            url = f"{self.base_url}/{endpoint}"
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erreur API Benzinga: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur requête Benzinga: {e}")
            return None
    
    def get_earnings_calendar(self, days_ahead: int = 2) -> List[Dict]:
        """
        Récupère calendrier earnings
        
        Args:
            days_ahead: Nombre de jours à l'avance (défaut 2 = 48h)
        """
        try:
            today = datetime.now(self.tz)
            end_date = today + timedelta(days=days_ahead)
            
            params = {
                'parameters[date_from]': today.strftime('%Y-%m-%d'),
                'parameters[date_to]': end_date.strftime('%Y-%m-%d')
            }
            
            data = self._make_request('calendar/earnings', params)
            
            if data and 'earnings' in data:
                return data['earnings']
            
            return []
            
        except Exception as e:
            print(f"❌ Erreur earnings calendar: {e}")
            return []
    
    def has_earnings_soon(self, ticker: str, hours: int = 48) -> tuple[bool, Optional[Dict]]:
        """
        Vérifie si action a earnings dans les X heures
        
        Returns: (has_earnings, earnings_info)
        """
        try:
            earnings = self.get_earnings_calendar(days_ahead=int(hours/24) + 1)
            
            ticker = ticker.upper()
            
            for earning in earnings:
                if earning.get('ticker', '').upper() == ticker:
                    # Vérifier timing
                    date_str = earning.get('date')
                    time_str = earning.get('time', 'amc')  # amc=after market close
                    
                    if date_str:
                        # Calcul heures restantes
                        earning_date = datetime.strptime(date_str, '%Y-%m-%d')
                        earning_date = self.tz.localize(earning_date)
                        
                        if time_str == 'bmo':  # before market open
                            earning_date = earning_date.replace(hour=9, minute=30)
                        else:  # amc
                            earning_date = earning_date.replace(hour=16, minute=0)
                        
                        now = datetime.now(self.tz)
                        hours_until = (earning_date - now).total_seconds() / 3600
                        
                        if 0 <= hours_until <= hours:
                            return True, {
                                'ticker': ticker,
                                'date': date_str,
                                'time': time_str,
                                'hours_until': hours_until,
                                'eps_estimate': earning.get('eps_est'),
                                'revenue_estimate': earning.get('revenue_est')
                            }
            
            return False, None
            
        except Exception as e:
            print(f"❌ Erreur vérification earnings {ticker}: {e}")
            return False, None
    
    def get_breaking_news(self, ticker: Optional[str] = None, minutes: int = 30) -> List[Dict]:
        """
        Récupère news récentes
        
        Args:
            ticker: Ticker spécifique (None = toutes les news)
            minutes: Minutes en arrière
        """
        try:
            now = datetime.now(self.tz)
            from_time = now - timedelta(minutes=minutes)
            
            params = {
                'pageSize': 50,
                'displayOutput': 'full',
                'dateFrom': from_time.strftime('%Y-%m-%d'),
                'dateTo': now.strftime('%Y-%m-%d')
            }
            
            if ticker:
                params['tickers'] = ticker.upper()
            
            data = self._make_request('news', params)
            
            if data and isinstance(data, list):
                # Filtrer par timing
                recent_news = []
                for news in data:
                    created = news.get('created')
                    if created:
                        news_time = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        if news_time >= from_time.replace(tzinfo=pytz.UTC):
                            recent_news.append(news)
                
                return recent_news
            
            return []
            
        except Exception as e:
            print(f"❌ Erreur breaking news: {e}")
            return []
    
    def is_negative_news(self, news: Dict) -> bool:
        """Détecte si news est négative"""
        try:
            title = news.get('title', '').lower()
            body = news.get('body', '').lower()
            
            text = f"{title} {body}"
            
            # Chercher mots-clés négatifs
            for keyword in NEGATIVE_KEYWORDS:
                if keyword in text:
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur analyse news: {e}")
            return False
    
    def has_negative_news(self, ticker: str, minutes: int = 30) -> tuple[bool, List[Dict]]:
        """
        Vérifie si action a news négatives récentes
        
        Returns: (has_negative, negative_news_list)
        """
        try:
            news_list = self.get_breaking_news(ticker, minutes)
            
            negative_news = [
                news for news in news_list
                if self.is_negative_news(news)
            ]
            
            has_negative = len(negative_news) > 0
            
            return has_negative, negative_news
            
        except Exception as e:
            print(f"❌ Erreur vérification news négatives {ticker}: {e}")
            return False, []
    
    def get_ratings_changes(self, ticker: str, days: int = 1) -> List[Dict]:
        """Récupère changements de ratings (upgrades/downgrades)"""
        try:
            today = datetime.now(self.tz)
            from_date = today - timedelta(days=days)
            
            params = {
                'parameters[date_from]': from_date.strftime('%Y-%m-%d'),
                'parameters[date_to]': today.strftime('%Y-%m-%d'),
                'parameters[tickers]': ticker.upper()
            }
            
            data = self._make_request('calendar/ratings', params)
            
            if data and 'ratings' in data:
                return data['ratings']
            
            return []
            
        except Exception as e:
            print(f"❌ Erreur ratings {ticker}: {e}")
            return []
    
    def has_recent_downgrade(self, ticker: str, days: int = 1) -> tuple[bool, List[Dict]]:
        """Vérifie si action a eu downgrade récent"""
        try:
            ratings = self.get_ratings_changes(ticker, days)
            
            downgrades = [
                rating for rating in ratings
                if 'downgrade' in rating.get('action', '').lower()
            ]
            
            has_downgrade = len(downgrades) > 0
            
            return has_downgrade, downgrades
            
        except Exception as e:
            print(f"❌ Erreur vérification downgrade {ticker}: {e}")
            return False, []


# Instance globale
news_monitor = NewsMonitor()


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST NEWS MONITOR")
    print("="*60 + "\n")
    
    monitor = NewsMonitor()
    
    if not BENZINGA_API_KEY:
        print("⚠️  Pas de clé API Benzinga configurée")
        print("Ajoutez BENZINGA_API_KEY dans votre fichier .env")
        exit(1)
    
    # Test earnings calendar
    print("📅 Earnings calendar (2 prochains jours):\n")
    earnings = monitor.get_earnings_calendar(days_ahead=2)
    
    if earnings:
        for i, earning in enumerate(earnings[:10]):  # Top 10
            ticker = earning.get('ticker', 'N/A')
            date = earning.get('date', 'N/A')
            time = earning.get('time', 'N/A')
            print(f"{i+1}. {ticker} - {date} {time}")
    else:
        print("Aucun earning trouvé")
    
    # Test action spécifique
    test_ticker = 'AAPL'
    print(f"\n🔍 Vérifications {test_ticker}:\n")
    
    # Earnings
    has_earnings, earnings_info = monitor.has_earnings_soon(test_ticker, hours=48)
    if has_earnings:
        print(f"⚠️  Earnings dans {earnings_info['hours_until']:.1f}h")
        print(f"   Date: {earnings_info['date']} {earnings_info['time']}")
    else:
        print("✅ Pas d'earnings dans les 48h")
    
    # News récentes
    print(f"\n📰 News récentes (30 min):")
    news = monitor.get_breaking_news(test_ticker, minutes=30)
    if news:
        for i, article in enumerate(news[:5]):
            title = article.get('title', 'N/A')
            created = article.get('created', 'N/A')
            is_neg = monitor.is_negative_news(article)
            emoji = "🔴" if is_neg else "🟢"
            print(f"   {emoji} [{created}] {title}")
    else:
        print("   Aucune news récente")
    
    # News négatives
    has_neg, neg_news = monitor.has_negative_news(test_ticker, minutes=30)
    if has_neg:
        print(f"\n🔴 {len(neg_news)} news négative(s) détectée(s)")
    else:
        print(f"\n✅ Pas de news négative récente")
    
    # Downgrades
    has_down, downgrades = monitor.has_recent_downgrade(test_ticker, days=1)
    if has_down:
        print(f"\n🔻 {len(downgrades)} downgrade(s) récent(s)")
        for downgrade in downgrades:
            analyst = downgrade.get('analyst', 'N/A')
            action = downgrade.get('action', 'N/A')
            print(f"   - {analyst}: {action}")
    else:
        print(f"\n✅ Pas de downgrade récent")

