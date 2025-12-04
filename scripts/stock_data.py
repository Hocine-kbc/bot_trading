"""
Récupération données actions via IBKR
"""
from ib_insync import IB, Stock, util
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from config import IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID


class StockDataProvider:
    """Fournisseur de données actions via IBKR"""
    
    def __init__(self):
        self.ib = IB()
        self.connected = False
    
    def connect(self):
        """Connexion à IBKR"""
        if not self.connected:
            try:
                self.ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, timeout=10)
                self.connected = True
                print(f"✅ Connecté à IBKR ({IBKR_HOST}:{IBKR_PORT})")
            except Exception as e:
                print(f"❌ Erreur connexion IBKR: {e}")
                self.connected = False
                raise
    
    def disconnect(self):
        """Déconnexion"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            print("🔌 Déconnecté de IBKR")
    
    def get_contract(self, ticker: str) -> Optional[Stock]:
        """Récupère le contrat IBKR pour un ticker"""
        try:
            if not self.connected:
                self.connect()
            
            contract = Stock(ticker, 'SMART', 'USD')
            qualified = self.ib.qualifyContracts(contract)
            
            if qualified:
                return qualified[0]
            else:
                print(f"⚠️  Contrat non trouvé pour {ticker}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur récupération contrat {ticker}: {e}")
            return None
    
    def get_current_price(self, ticker: str) -> Optional[Dict]:
        """Récupère prix actuel temps réel"""
        try:
            contract = self.get_contract(ticker)
            if not contract:
                return None
            
            ticker_obj = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Attendre données
            
            if ticker_obj.last and ticker_obj.last > 0:
                return {
                    'ticker': ticker,
                    'last': ticker_obj.last,
                    'bid': ticker_obj.bid if ticker_obj.bid > 0 else None,
                    'ask': ticker_obj.ask if ticker_obj.ask > 0 else None,
                    'bid_size': ticker_obj.bidSize,
                    'ask_size': ticker_obj.askSize,
                    'volume': ticker_obj.volume,
                    'last_timestamp': ticker_obj.time
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Erreur prix {ticker}: {e}")
            return None
    
    def get_ohlcv(self, ticker: str, interval: str = '5 mins', duration: str = '1 D') -> Optional[pd.DataFrame]:
        """
        Récupère données OHLCV historiques
        
        interval: '1 min', '5 mins', '15 mins', '1 hour', '1 day'
        duration: '1 D', '1 W', '1 M'
        """
        try:
            contract = self.get_contract(ticker)
            if not contract:
                return None
            
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=interval,
                whatToShow='TRADES',
                useRTH=True,  # Regular Trading Hours only
                formatDate=1
            )
            
            if not bars:
                print(f"⚠️  Pas de données historiques pour {ticker}")
                return None
            
            # Convertir en DataFrame
            df = util.df(bars)
            df['ticker'] = ticker
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur OHLCV {ticker}: {e}")
            return None
    
    def get_orderflow(self, ticker: str) -> Optional[Dict]:
        """
        Récupère orderflow (bid/ask sizes, imbalance)
        """
        try:
            contract = self.get_contract(ticker)
            if not contract:
                return None
            
            ticker_obj = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)
            
            bid = ticker_obj.bid if ticker_obj.bid > 0 else 0
            ask = ticker_obj.ask if ticker_obj.ask > 0 else 0
            bid_size = ticker_obj.bidSize
            ask_size = ticker_obj.askSize
            
            # Calcul spread
            spread = 0
            spread_pct = 0
            if bid > 0 and ask > 0:
                spread = ask - bid
                spread_pct = (spread / ask) * 100
            
            # Imbalance bid/ask
            total_size = bid_size + ask_size
            bid_pressure = 0
            if total_size > 0:
                bid_pressure = (bid_size / total_size) * 100
            
            return {
                'ticker': ticker,
                'bid': bid,
                'ask': ask,
                'bid_size': bid_size,
                'ask_size': ask_size,
                'spread': spread,
                'spread_pct': spread_pct,
                'bid_pressure': bid_pressure,
                'signal': 1 if bid_pressure > 55 else (-1 if bid_pressure < 45 else 0)
            }
            
        except Exception as e:
            print(f"❌ Erreur orderflow {ticker}: {e}")
            return None
    
    def get_volume_profile(self, ticker: str, periods: int = 20) -> Optional[Dict]:
        """Analyse volume (moyenne, comparaison)"""
        try:
            df = self.get_ohlcv(ticker, interval='5 mins', duration='5 D')
            if df is None or df.empty:
                return None
            
            recent = df.tail(periods)
            current_volume = recent['volume'].iloc[-1]
            avg_volume = recent['volume'].iloc[:-1].mean()
            
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                'ticker': ticker,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'is_high_volume': volume_ratio >= 1.2
            }
            
        except Exception as e:
            print(f"❌ Erreur volume profile {ticker}: {e}")
            return None


# Instance globale
stock_data_provider = StockDataProvider()


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST STOCK DATA PROVIDER")
    print("="*60 + "\n")
    
    provider = StockDataProvider()
    
    try:
        provider.connect()
        
        ticker = 'AAPL'
        print(f"📊 Test données {ticker}...\n")
        
        # Prix actuel
        price_data = provider.get_current_price(ticker)
        if price_data:
            print(f"💰 Prix actuel:")
            print(f"   Last: ${price_data['last']:.2f}")
            print(f"   Bid: ${price_data['bid']:.2f} x {price_data['bid_size']}")
            print(f"   Ask: ${price_data['ask']:.2f} x {price_data['ask_size']}")
            print(f"   Volume: {price_data['volume']:,}")
        
        # Orderflow
        print(f"\n📈 Orderflow:")
        orderflow = provider.get_orderflow(ticker)
        if orderflow:
            print(f"   Spread: ${orderflow['spread']:.2f} ({orderflow['spread_pct']:.2f}%)")
            print(f"   Bid pressure: {orderflow['bid_pressure']:.1f}%")
            signal_emoji = "🟢" if orderflow['signal'] == 1 else ("🔴" if orderflow['signal'] == -1 else "🟡")
            print(f"   Signal: {signal_emoji} {orderflow['signal']}")
        
        # OHLCV
        print(f"\n📉 OHLCV (5min, 10 dernières bougies):")
        df = provider.get_ohlcv(ticker, '5 mins', '1 D')
        if df is not None and not df.empty:
            print(df.tail(10)[['date', 'open', 'high', 'low', 'close', 'volume']])
        
    finally:
        provider.disconnect()

