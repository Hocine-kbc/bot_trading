"""
Surveillance des News via Benzinga Pro API
==========================================
Ce fichier surveille les actualités financières pour:
- Détecter les earnings (résultats trimestriels) à venir
- Repérer les news négatives (procès, downgrades, etc.)
- Éviter d'acheter avant des annonces importantes

API utilisée: Benzinga Pro (https://www.benzinga.com/apis)
Nécessite une clé API dans le fichier .env
"""

# ============================================================
# IMPORTS
# ============================================================

import requests  # Pour faire des requêtes HTTP à l'API
from datetime import datetime, timedelta  # Pour manipuler les dates
from typing import List, Dict, Optional  # Pour typer les variables
import pytz  # Pour gérer les fuseaux horaires

# Nos paramètres depuis la configuration
from config import BENZINGA_API_KEY, TIMEZONE, NEGATIVE_KEYWORDS


# ============================================================
# CLASSE PRINCIPALE - NewsMonitor
# ============================================================

class NewsMonitor:
    """
    Surveillance des news financières via l'API Benzinga
    
    Fonctionnalités:
    - Calendrier des earnings (résultats trimestriels)
    - News récentes sur une action
    - Détection de news négatives
    - Suivi des changements de ratings (upgrades/downgrades)
    """
    
    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    
    def __init__(self):
        """
        Constructeur - Configure l'accès à l'API Benzinga
        """
        self.api_key = BENZINGA_API_KEY  # Clé API (depuis .env)
        self.base_url = "https://api.benzinga.com/api/v2.1"  # URL de base de l'API
        self.tz = pytz.timezone(TIMEZONE)  # Fuseau horaire (New York)
    
    # --------------------------------------------------------
    # REQUÊTE API
    # --------------------------------------------------------
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Fait une requête à l'API Benzinga
        
        Args:
            endpoint: Le point d'accès API (ex: 'news', 'calendar/earnings')
            params: Les paramètres de la requête
        
        Returns:
            Les données JSON de la réponse, ou None si erreur
        """
        try:
            # Ajouter le token d'authentification aux paramètres
            params['token'] = self.api_key
            
            # Construire l'URL complète
            url = f"{self.base_url}/{endpoint}"
            
            # Faire la requête GET avec timeout de 10 secondes
            response = requests.get(url, params=params, timeout=10)
            
            # Vérifier le code de statut HTTP
            if response.status_code == 200:  # 200 = succès
                return response.json()  # Convertir la réponse en dictionnaire Python
            else:
                print(f"❌ Erreur API Benzinga: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur requête Benzinga: {e}")
            return None
    
    # --------------------------------------------------------
    # CALENDRIER DES EARNINGS
    # --------------------------------------------------------
    
    def get_earnings_calendar(self, days_ahead: int = 2) -> List[Dict]:
        """
        Récupère le calendrier des earnings (résultats trimestriels)
        
        Les earnings sont des annonces très importantes qui peuvent
        faire bouger une action de +/- 10-20% en quelques minutes.
        On évite d'acheter juste avant ces annonces.
        
        Args:
            days_ahead: Nombre de jours à l'avance (défaut: 2 = 48h)
        
        Returns:
            Liste des earnings prévus avec ticker, date, estimations
        """
        try:
            # Calculer la plage de dates
            today = datetime.now(self.tz)
            end_date = today + timedelta(days=days_ahead)
            
            # Paramètres de la requête
            params = {
                'parameters[date_from]': today.strftime('%Y-%m-%d'),  # Date début
                'parameters[date_to]': end_date.strftime('%Y-%m-%d')   # Date fin
            }
            
            # Appeler l'API
            data = self._make_request('calendar/earnings', params)
            
            # Extraire la liste des earnings
            if data and 'earnings' in data:
                return data['earnings']
            
            return []
            
        except Exception as e:
            print(f"❌ Erreur earnings calendar: {e}")
            return []
    
    def has_earnings_soon(self, ticker: str, hours: int = 48) -> tuple[bool, Optional[Dict]]:
        """
        Vérifie si une action a des earnings dans les prochaines X heures
        
        IMPORTANT: Ne pas acheter une action qui a des earnings imminents !
        Le risque est trop élevé (gap up ou gap down imprévisible).
        
        Args:
            ticker: Le symbole de l'action
            hours: Nombre d'heures à vérifier (défaut: 48h)
        
        Returns:
            Tuple (has_earnings, earnings_info):
            - has_earnings: True si earnings dans la période
            - earnings_info: Détails des earnings (date, estimations)
        """
        try:
            # Récupérer le calendrier
            earnings = self.get_earnings_calendar(days_ahead=int(hours/24) + 1)
            
            ticker = ticker.upper()
            
            # Chercher le ticker dans la liste
            for earning in earnings:
                if earning.get('ticker', '').upper() == ticker:
                    # Récupérer la date et l'heure
                    date_str = earning.get('date')
                    time_str = earning.get('time', 'amc')  # amc = after market close (par défaut)
                    
                    if date_str:
                        # Convertir la date string en objet datetime
                        earning_date = datetime.strptime(date_str, '%Y-%m-%d')
                        earning_date = self.tz.localize(earning_date)
                        
                        # Ajuster l'heure selon le type d'annonce
                        if time_str == 'bmo':  # before market open = avant ouverture
                            earning_date = earning_date.replace(hour=9, minute=30)
                        else:  # amc = after market close = après fermeture
                            earning_date = earning_date.replace(hour=16, minute=0)
                        
                        # Calculer le temps restant
                        now = datetime.now(self.tz)
                        hours_until = (earning_date - now).total_seconds() / 3600
                        
                        # Si dans la plage demandée
                        if 0 <= hours_until <= hours:
                            return True, {
                                'ticker': ticker,
                                'date': date_str,
                                'time': time_str,  # bmo ou amc
                                'hours_until': hours_until,
                                'eps_estimate': earning.get('eps_est'),  # Estimation EPS
                                'revenue_estimate': earning.get('revenue_est')  # Estimation revenus
                            }
            
            return False, None  # Pas d'earnings trouvés
            
        except Exception as e:
            print(f"❌ Erreur vérification earnings {ticker}: {e}")
            return False, None
    
    # --------------------------------------------------------
    # NEWS RÉCENTES
    # --------------------------------------------------------
    
    def get_breaking_news(self, ticker: Optional[str] = None, minutes: int = 30) -> List[Dict]:
        """
        Récupère les news récentes
        
        Args:
            ticker: Symbole spécifique (None = toutes les news)
            minutes: Nombre de minutes en arrière
        
        Returns:
            Liste des articles de news récents
        """
        try:
            # Calculer la plage de temps
            now = datetime.now(self.tz)
            from_time = now - timedelta(minutes=minutes)
            
            # Paramètres de la requête
            params = {
                'pageSize': 50,  # Max 50 articles
                'displayOutput': 'full',  # Contenu complet
                'dateFrom': from_time.strftime('%Y-%m-%d'),
                'dateTo': now.strftime('%Y-%m-%d')
            }
            
            # Filtrer par ticker si spécifié
            if ticker:
                params['tickers'] = ticker.upper()
            
            # Appeler l'API
            data = self._make_request('news', params)
            
            if data and isinstance(data, list):
                # Filtrer pour ne garder que les news vraiment récentes
                recent_news = []
                for news in data:
                    created = news.get('created')  # Date de création
                    if created:
                        # Convertir en datetime
                        news_time = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        # Vérifier si dans la plage
                        if news_time >= from_time.replace(tzinfo=pytz.UTC):
                            recent_news.append(news)
                
                return recent_news
            
            return []
            
        except Exception as e:
            print(f"❌ Erreur breaking news: {e}")
            return []
    
    # --------------------------------------------------------
    # DÉTECTION DE NEWS NÉGATIVES
    # --------------------------------------------------------
    
    def is_negative_news(self, news: Dict) -> bool:
        """
        Détecte si une news est négative
        
        Cherche les mots-clés négatifs dans le titre et le corps.
        Liste des mots-clés définie dans config.py (NEGATIVE_KEYWORDS)
        
        Args:
            news: Dictionnaire représentant un article
        
        Returns:
            True si la news contient des mots-clés négatifs
        """
        try:
            # Récupérer titre et corps en minuscules
            title = news.get('title', '').lower()
            body = news.get('body', '').lower()
            
            # Combiner pour recherche
            text = f"{title} {body}"
            
            # Chercher chaque mot-clé négatif
            for keyword in NEGATIVE_KEYWORDS:
                if keyword in text:
                    return True  # News négative trouvée
            
            return False  # Pas de mot-clé négatif
            
        except Exception as e:
            print(f"❌ Erreur analyse news: {e}")
            return False
    
    def has_negative_news(self, ticker: str, minutes: int = 30) -> tuple[bool, List[Dict]]:
        """
        Vérifie si une action a des news négatives récentes
        
        IMPORTANT: Ne pas acheter une action avec des news négatives !
        (procès, fraude, downgrade, etc.)
        
        Args:
            ticker: Le symbole de l'action
            minutes: Période à vérifier (défaut: 30 minutes)
        
        Returns:
            Tuple (has_negative, negative_news_list):
            - has_negative: True s'il y a des news négatives
            - negative_news_list: Liste des news négatives
        """
        try:
            # Récupérer toutes les news récentes pour ce ticker
            news_list = self.get_breaking_news(ticker, minutes)
            
            # Filtrer pour garder seulement les négatives
            # List comprehension avec condition
            negative_news = [
                news for news in news_list
                if self.is_negative_news(news)
            ]
            
            has_negative = len(negative_news) > 0
            
            return has_negative, negative_news
            
        except Exception as e:
            print(f"❌ Erreur vérification news négatives {ticker}: {e}")
            return False, []
    
    # --------------------------------------------------------
    # RATINGS (UPGRADES / DOWNGRADES)
    # --------------------------------------------------------
    
    def get_ratings_changes(self, ticker: str, days: int = 1) -> List[Dict]:
        """
        Récupère les changements de ratings des analystes
        
        Les analystes donnent des notes aux actions:
        - Upgrade = amélioration (bullish)
        - Downgrade = dégradation (bearish)
        
        Args:
            ticker: Le symbole de l'action
            days: Période en jours
        
        Returns:
            Liste des changements de ratings
        """
        try:
            # Calculer la plage de dates
            today = datetime.now(self.tz)
            from_date = today - timedelta(days=days)
            
            # Paramètres
            params = {
                'parameters[date_from]': from_date.strftime('%Y-%m-%d'),
                'parameters[date_to]': today.strftime('%Y-%m-%d'),
                'parameters[tickers]': ticker.upper()
            }
            
            # Appeler l'API
            data = self._make_request('calendar/ratings', params)
            
            if data and 'ratings' in data:
                return data['ratings']
            
            return []
            
        except Exception as e:
            print(f"❌ Erreur ratings {ticker}: {e}")
            return []
    
    def has_recent_downgrade(self, ticker: str, days: int = 1) -> tuple[bool, List[Dict]]:
        """
        Vérifie si une action a eu un downgrade récent
        
        Un downgrade = un analyste dégrade sa note sur l'action.
        C'est un signal négatif, on évite d'acheter.
        
        Args:
            ticker: Le symbole de l'action
            days: Période en jours
        
        Returns:
            Tuple (has_downgrade, downgrades_list)
        """
        try:
            # Récupérer tous les changements de ratings
            ratings = self.get_ratings_changes(ticker, days)
            
            # Filtrer pour garder seulement les downgrades
            downgrades = [
                rating for rating in ratings
                if 'downgrade' in rating.get('action', '').lower()
            ]
            
            has_downgrade = len(downgrades) > 0
            
            return has_downgrade, downgrades
            
        except Exception as e:
            print(f"❌ Erreur vérification downgrade {ticker}: {e}")
            return False, []


# ============================================================
# INSTANCE GLOBALE
# ============================================================

# Créer une instance globale
# Usage: from news_monitor import news_monitor
news_monitor = NewsMonitor()


# ============================================================
# CODE DE TEST
# ============================================================

if __name__ == '__main__':
    # Afficher en-tête
    print("\n" + "="*60)
    print("TEST NEWS MONITOR")
    print("="*60 + "\n")
    
    # Créer un monitor pour les tests
    monitor = NewsMonitor()
    
    # Vérifier que la clé API est configurée
    if not BENZINGA_API_KEY:
        print("⚠️  Pas de clé API Benzinga configurée")
        print("Ajoutez BENZINGA_API_KEY dans votre fichier .env")
        exit(1)  # Quitter avec code d'erreur
    
    # ---- Test 1: Calendrier des earnings ----
    print("📅 Earnings calendar (2 prochains jours):\n")
    earnings = monitor.get_earnings_calendar(days_ahead=2)
    
    if earnings:
        # Afficher les 10 premiers
        for i, earning in enumerate(earnings[:10]):
            ticker = earning.get('ticker', 'N/A')
            date = earning.get('date', 'N/A')
            time = earning.get('time', 'N/A')
            print(f"{i+1}. {ticker} - {date} {time}")
    else:
        print("Aucun earning trouvé")
    
    # ---- Test 2: Vérifications sur une action ----
    test_ticker = 'AAPL'
    print(f"\n🔍 Vérifications {test_ticker}:\n")
    
    # Earnings dans les 48h ?
    has_earnings, earnings_info = monitor.has_earnings_soon(test_ticker, hours=48)
    if has_earnings:
        print(f"⚠️  Earnings dans {earnings_info['hours_until']:.1f}h")
        print(f"   Date: {earnings_info['date']} {earnings_info['time']}")
    else:
        print("✅ Pas d'earnings dans les 48h")
    
    # News récentes (30 minutes)
    print(f"\n📰 News récentes (30 min):")
    news = monitor.get_breaking_news(test_ticker, minutes=30)
    if news:
        for i, article in enumerate(news[:5]):
            title = article.get('title', 'N/A')
            created = article.get('created', 'N/A')
            is_neg = monitor.is_negative_news(article)
            emoji = "🔴" if is_neg else "🟢"  # Rouge si négatif, vert sinon
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
