"""
Récupération des données boursières via Interactive Brokers (IBKR)
==================================================================
Ce fichier gère toute la communication avec le broker IBKR pour:
- Récupérer les prix en temps réel
- Récupérer les données historiques (OHLCV)
- Analyser l'orderflow (bid/ask)

Prérequis:
- TWS ou IB Gateway doit être lancé
- L'API doit être activée dans les paramètres TWS
"""

# ============================================================
# IMPORTS
# ============================================================

# ib_insync = bibliothèque Python pour communiquer avec IBKR
from ib_insync import IB, Stock, Index, util

import pandas as pd  # Pour manipuler les données en tableaux
from datetime import datetime, timedelta  # Pour les dates
from typing import Optional, Dict, List  # Pour typer les variables

# Nos paramètres de connexion (depuis config.py qui lit .env)
from config import IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID


# ============================================================
# CLASSE PRINCIPALE - StockDataProvider
# ============================================================

class StockDataProvider:
    """
    Fournisseur de données boursières via Interactive Brokers
    
    Cette classe permet de:
    - Se connecter/déconnecter à IBKR
    - Récupérer les prix en temps réel
    - Récupérer les données historiques (chandeliers)
    - Analyser l'orderflow (pression achat/vente)
    """
    
    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    
    def __init__(self):
        """
        Constructeur - Crée une instance IB mais ne se connecte pas encore
        """
        self.ib = IB()  # Objet de connexion IBKR (de la bibliothèque ib_insync)
        self.connected = False  # Flag pour savoir si on est connecté
    
    # --------------------------------------------------------
    # CONNEXION / DÉCONNEXION
    # --------------------------------------------------------
    
    def connect(self):
        """
        Se connecte à Interactive Brokers (TWS ou IB Gateway)
        
        La connexion utilise les paramètres définis dans .env:
        - IBKR_HOST: adresse IP (127.0.0.1 pour local)
        - IBKR_PORT: port (7497 pour paper trading)
        - IBKR_CLIENT_ID: identifiant unique
        """
        # Ne se connecte que si pas déjà connecté
        if not self.connected:
            try:
                # Tentative de connexion avec timeout de 10 secondes
                self.ib.connect(
                    IBKR_HOST,      # Adresse IP
                    IBKR_PORT,      # Port
                    clientId=IBKR_CLIENT_ID,  # ID client
                    timeout=10      # Timeout en secondes
                )
                self.connected = True
                print(f"✅ Connecté à IBKR ({IBKR_HOST}:{IBKR_PORT})")
            except Exception as e:
                print(f"❌ Erreur connexion IBKR: {e}")
                self.connected = False
                raise  # Relancer l'exception pour arrêter le programme
    
    def disconnect(self):
        """
        Se déconnecte proprement d'IBKR
        Important de se déconnecter pour libérer les ressources
        """
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            print("🔌 Déconnecté de IBKR")
    
    # --------------------------------------------------------
    # RÉCUPÉRATION DU CONTRAT
    # --------------------------------------------------------
    
    def get_contract(self, ticker: str) -> Optional[Stock]:
        """
        Récupère le contrat IBKR pour un ticker donné
        
        Un "contrat" dans IBKR représente un instrument financier.
        On doit d'abord qualifier le contrat avant de pouvoir l'utiliser.
        
        Args:
            ticker: Le symbole de l'action (ex: 'AAPL', 'MSFT')
        
        Returns:
            Le contrat qualifié ou None si non trouvé
        """
        try:
            # Se connecter si pas encore fait
            if not self.connected:
                self.connect()
            
            # Créer un contrat Stock (action)
            # 'SMART' = routage intelligent (IBKR choisit le meilleur exchange)
            # 'USD' = devise
            contract = Stock(ticker, 'SMART', 'USD')
            
            # Qualifier le contrat = IBKR vérifie qu'il existe et complète les infos
            qualified = self.ib.qualifyContracts(contract)
            
            if qualified:
                return qualified[0]  # Retourner le premier (et seul) contrat
            else:
                print(f"⚠️  Contrat non trouvé pour {ticker}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur récupération contrat {ticker}: {e}")
            return None
    
    # --------------------------------------------------------
    # PRIX EN TEMPS RÉEL
    # --------------------------------------------------------
    
    def get_current_price(self, ticker: str) -> Optional[Dict]:
        """
        Récupère le prix actuel en temps réel
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Dictionnaire avec les données de marché:
            - last: dernier prix échangé
            - bid: meilleur prix d'achat
            - ask: meilleur prix de vente
            - bid_size: quantité au bid
            - ask_size: quantité à l'ask
            - volume: volume du jour
        """
        try:
            # Récupérer le contrat
            contract = self.get_contract(ticker)
            if not contract:
                return None
            
            # Demander les données de marché en temps réel
            # '' = pas de données génériques spécifiques
            # False, False = pas de snapshot, pas de données réglementaires
            ticker_obj = self.ib.reqMktData(contract, '', False, False)
            
            # Attendre 2 secondes que les données arrivent
            self.ib.sleep(2)
            
            # Vérifier qu'on a un prix valide
            if ticker_obj.last and ticker_obj.last > 0:
                return {
                    'ticker': ticker,
                    'last': ticker_obj.last,  # Dernier prix
                    'bid': ticker_obj.bid if ticker_obj.bid > 0 else None,  # Prix d'achat
                    'ask': ticker_obj.ask if ticker_obj.ask > 0 else None,  # Prix de vente
                    'bid_size': ticker_obj.bidSize,  # Quantité au bid
                    'ask_size': ticker_obj.askSize,  # Quantité à l'ask
                    'volume': ticker_obj.volume,  # Volume journalier
                    'last_timestamp': ticker_obj.time  # Heure du dernier échange
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Erreur prix {ticker}: {e}")
            return None
    
    # --------------------------------------------------------
    # DONNÉES HISTORIQUES (OHLCV)
    # --------------------------------------------------------
    
    def get_ohlcv(self, ticker: str, interval: str = '5 mins', duration: str = '1 D') -> Optional[pd.DataFrame]:
        """
        Récupère les données historiques OHLCV (chandeliers)
        
        OHLCV = Open, High, Low, Close, Volume
        Ce sont les 5 données de base de chaque bougie/chandelier
        
        Args:
            ticker: Le symbole de l'action
            interval: La durée de chaque bougie
                     '1 min', '5 mins', '15 mins', '1 hour', '1 day'
            duration: La période totale à récupérer
                     '1 D' (1 jour), '1 W' (1 semaine), '1 M' (1 mois)
        
        Returns:
            DataFrame pandas avec colonnes: date, open, high, low, close, volume
        """
        try:
            # Récupérer le contrat
            contract = self.get_contract(ticker)
            if not contract:
                return None
            
            # Demander les données historiques
            bars = self.ib.reqHistoricalData(
                contract,                   # Le contrat (l'action)
                endDateTime='',             # '' = maintenant
                durationStr=duration,       # Période (ex: '1 D')
                barSizeSetting=interval,    # Taille des bougies (ex: '5 mins')
                whatToShow='TRADES',        # Type de données (trades réels)
                useRTH=True,                # True = Regular Trading Hours only
                formatDate=1                # Format de date
            )
            
            # Vérifier qu'on a des données
            if not bars:
                print(f"⚠️  Pas de données historiques pour {ticker}")
                return None
            
            # Convertir en DataFrame pandas (plus facile à manipuler)
            df = util.df(bars)
            df['ticker'] = ticker  # Ajouter le symbole
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur OHLCV {ticker}: {e}")
            return None
    
    # --------------------------------------------------------
    # ORDERFLOW (BID/ASK ANALYSIS)
    # --------------------------------------------------------
    
    def get_orderflow(self, ticker: str) -> Optional[Dict]:
        """
        Récupère l'orderflow = analyse du carnet d'ordres
        
        L'orderflow permet de voir la pression acheteuse vs vendeuse:
        - Bid = ordres d'achat (acheteurs)
        - Ask = ordres de vente (vendeurs)
        - Si bid_size > ask_size → pression acheteuse (haussier)
        - Si ask_size > bid_size → pression vendeuse (baissier)
        
        Args:
            ticker: Le symbole de l'action
        
        Returns:
            Dictionnaire avec:
            - bid/ask: prix
            - bid_size/ask_size: quantités
            - spread: écart bid-ask
            - bid_pressure: % de pression acheteuse
            - signal: 1 (haussier), -1 (baissier), 0 (neutre)
        """
        try:
            # Récupérer le contrat
            contract = self.get_contract(ticker)
            if not contract:
                return None
            
            # Demander les données de marché
            ticker_obj = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Attendre les données
            
            # Récupérer bid et ask (prix et quantités)
            bid = ticker_obj.bid if ticker_obj.bid > 0 else 0
            ask = ticker_obj.ask if ticker_obj.ask > 0 else 0
            bid_size = ticker_obj.bidSize  # Quantité disponible au bid
            ask_size = ticker_obj.askSize  # Quantité disponible à l'ask
            
            # Calculer le spread (écart entre bid et ask)
            # Un spread faible = bonne liquidité
            # Un spread élevé = mauvaise liquidité (coûteux à trader)
            spread = 0
            spread_pct = 0
            if bid > 0 and ask > 0:
                spread = ask - bid  # Spread en $
                spread_pct = (spread / ask) * 100  # Spread en %
            
            # Calculer la pression acheteuse (bid pressure)
            # = bid_size / (bid_size + ask_size) * 100
            # Si > 55% → plus d'acheteurs que de vendeurs
            total_size = bid_size + ask_size
            bid_pressure = 0
            if total_size > 0:
                bid_pressure = (bid_size / total_size) * 100
            
            return {
                'ticker': ticker,
                'bid': bid,  # Prix d'achat
                'ask': ask,  # Prix de vente
                'bid_size': bid_size,  # Quantité au bid
                'ask_size': ask_size,  # Quantité à l'ask
                'spread': spread,  # Écart en $
                'spread_pct': spread_pct,  # Écart en %
                'bid_pressure': bid_pressure,  # % pression acheteuse
                # Signal: 1 = haussier (bid_pressure > 55%)
                #        -1 = baissier (bid_pressure < 45%)
                #         0 = neutre (entre 45% et 55%)
                'signal': 1 if bid_pressure > 55 else (-1 if bid_pressure < 45 else 0)
            }
            
        except Exception as e:
            print(f"❌ Erreur orderflow {ticker}: {e}")
            return None
    
    # --------------------------------------------------------
    # PROFIL DE VOLUME
    # --------------------------------------------------------
    
    def get_vix_level(self) -> Optional[float]:
        """
        Récupère le niveau actuel du VIX (indice de volatilité)
        
        Le VIX est un INDEX, pas une action. Il nécessite un type de contrat différent.
        
        Returns:
            Le niveau du VIX (float) ou None si erreur
        """
        try:
            # Se connecter si pas encore fait
            if not self.connected:
                self.connect()
            
            # VIX est un Index sur CBOE
            contract = Index('VIX', 'CBOE', 'USD')
            
            # Qualifier le contrat
            qualified = self.ib.qualifyContracts(contract)
            
            if not qualified:
                print(f"⚠️  Contrat VIX non trouvé")
                return None
            
            # Demander les données de marché
            ticker_obj = self.ib.reqMktData(qualified[0], '', False, False)
            self.ib.sleep(2)
            
            # Retourner le dernier prix
            if ticker_obj.last and ticker_obj.last > 0:
                return ticker_obj.last
            elif ticker_obj.close and ticker_obj.close > 0:
                return ticker_obj.close
            else:
                return None
                
        except Exception as e:
            print(f"❌ Erreur récupération VIX: {e}")
            return None
    
    def get_volume_profile(self, ticker: str, periods: int = 20) -> Optional[Dict]:
        """
        Analyse le volume d'une action
        
        Compare le volume actuel à la moyenne des dernières périodes
        pour détecter les anomalies de volume (signe d'intérêt institutionnel)
        
        Args:
            ticker: Le symbole de l'action
            periods: Nombre de périodes pour calculer la moyenne
        
        Returns:
            Dictionnaire avec:
            - current_volume: volume actuel
            - avg_volume: volume moyen
            - volume_ratio: ratio actuel/moyen
            - is_high_volume: True si volume > 120% de la moyenne
        """
        try:
            # Récupérer 5 jours de données en bougies de 5 minutes
            df = self.get_ohlcv(ticker, interval='5 mins', duration='5 D')
            if df is None or df.empty:
                return None
            
            # Prendre les N dernières périodes
            recent = df.tail(periods)
            
            # Volume de la dernière bougie
            current_volume = recent['volume'].iloc[-1]
            
            # Volume moyen des bougies précédentes (sans la dernière)
            avg_volume = recent['volume'].iloc[:-1].mean()
            
            # Ratio volume actuel / volume moyen
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                'ticker': ticker,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                # Volume élevé si > 120% de la moyenne
                'is_high_volume': volume_ratio >= 1.2
            }
            
        except Exception as e:
            print(f"❌ Erreur volume profile {ticker}: {e}")
            return None


# ============================================================
# INSTANCE GLOBALE
# ============================================================

# Créer une instance globale pour pouvoir l'importer facilement
# Usage: from stock_data import stock_data_provider
stock_data_provider = StockDataProvider()


# ============================================================
# CODE DE TEST
# ============================================================

# Ce code ne s'exécute QUE si on lance: python stock_data.py
if __name__ == '__main__':
    # Afficher en-tête
    print("\n" + "="*60)
    print("TEST STOCK DATA PROVIDER")
    print("="*60 + "\n")
    
    # Créer un provider pour les tests
    provider = StockDataProvider()
    
    try:
        # Se connecter à IBKR
        provider.connect()
        
        # Ticker à tester
        ticker = 'AAPL'
        print(f"📊 Test données {ticker}...\n")
        
        # ---- Test 1: Prix actuel ----
        price_data = provider.get_current_price(ticker)
        if price_data:
            print(f"💰 Prix actuel:")
            print(f"   Last: ${price_data['last']:.2f}")
            print(f"   Bid: ${price_data['bid']:.2f} x {price_data['bid_size']}")
            print(f"   Ask: ${price_data['ask']:.2f} x {price_data['ask_size']}")
            print(f"   Volume: {price_data['volume']:,}")
        
        # ---- Test 2: Orderflow ----
        print(f"\n📈 Orderflow:")
        orderflow = provider.get_orderflow(ticker)
        if orderflow:
            print(f"   Spread: ${orderflow['spread']:.2f} ({orderflow['spread_pct']:.2f}%)")
            print(f"   Bid pressure: {orderflow['bid_pressure']:.1f}%")
            # Emoji selon le signal
            signal_emoji = "🟢" if orderflow['signal'] == 1 else ("🔴" if orderflow['signal'] == -1 else "🟡")
            print(f"   Signal: {signal_emoji} {orderflow['signal']}")
        
        # ---- Test 3: Données OHLCV ----
        print(f"\n📉 OHLCV (5min, 10 dernières bougies):")
        df = provider.get_ohlcv(ticker, '5 mins', '1 D')
        if df is not None and not df.empty:
            # Afficher les 10 dernières lignes
            print(df.tail(10)[['date', 'open', 'high', 'low', 'close', 'volume']])
        
    finally:
        # Toujours se déconnecter à la fin
        provider.disconnect()
