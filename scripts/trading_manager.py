"""
Gestionnaire de trading - Entrées, sorties, gestion positions
"""
from ib_insync import IB, Stock, LimitOrder, MarketOrder, Order
from typing import Optional, Dict, Tuple
import asyncio
from datetime import datetime
from stock_data import StockDataProvider
from risk_manager import RiskManager
from telegram_notifier import TelegramNotifier
from news_monitor import NewsMonitor
from config import (
    IBKR_HOST,
    IBKR_PORT,
    IBKR_CLIENT_ID,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    DRY_RUN_MODE,
    SPREAD_MAX_PCT
)


class TradingManager:
    """Gestionnaire d'exécution des trades"""
    
    def __init__(
        self,
        data_provider: StockDataProvider,
        risk_manager: RiskManager,
        telegram_notifier: TelegramNotifier,
        news_monitor: NewsMonitor
    ):
        self.data_provider = data_provider
        self.risk_manager = risk_manager
        self.telegram = telegram_notifier
        self.news_monitor = news_monitor
        self.ib = data_provider.ib
    
    def calculate_stop_take_prices(self, entry_price: float) -> Tuple[float, float]:
        """Calcule prix stop-loss et take-profit"""
        stop_loss = entry_price * (1 - STOP_LOSS_PCT)
        take_profit = entry_price * (1 + TAKE_PROFIT_PCT)
        return stop_loss, take_profit
    
    def enter_position(self, ticker: str, validation_details: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Entre en position
        
        Args:
            ticker: Symbole
            validation_details: Résultats validation filtres
        
        Returns: (success, trade_details)
        """
        try:
            # Vérifier risque
            can_trade, reason = self.risk_manager.can_trade()
            if not can_trade:
                print(f"❌ Impossible de trader: {reason}")
                return False, None
            
            # Obtenir prix actuel
            price_data = self.data_provider.get_current_price(ticker)
            if not price_data:
                print(f"❌ Impossible d'obtenir prix pour {ticker}")
                return False, None
            
            current_price = price_data['ask']  # Acheter à l'ask
            
            # Calculer quantité
            quantity = self.risk_manager.calculate_position_size(current_price)
            
            if quantity < 1:
                print(f"❌ Quantité insuffisante pour {ticker}")
                return False, None
            
            # Calculer SL/TP
            stop_loss, take_profit = self.calculate_stop_take_prices(current_price)
            
            print(f"\n{'='*60}")
            print(f"📊 PRÉPARATION ACHAT {ticker}")
            print(f"{'='*60}")
            print(f"Prix: ${current_price:.2f}")
            print(f"Quantité: {quantity}")
            print(f"Valeur: ${current_price * quantity:,.2f}")
            print(f"Stop-Loss: ${stop_loss:.2f} (-{STOP_LOSS_PCT*100}%)")
            print(f"Take-Profit: ${take_profit:.2f} (+{TAKE_PROFIT_PCT*100}%)")
            print(f"{'='*60}\n")
            
            if DRY_RUN_MODE:
                print("🧪 MODE DRY RUN - Pas d'ordre réel envoyé")
                
                # Simulation
                trade_details = {
                    'ticker': ticker,
                    'entry_price': current_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'dry_run': True
                }
                
                # Ajouter position (même en dry run pour tracking)
                self.risk_manager.add_position(
                    ticker,
                    current_price,
                    quantity,
                    stop_loss,
                    take_profit
                )
                
                # Notification
                asyncio.run(
                    self.telegram.notify_entry(
                        ticker,
                        current_price,
                        quantity,
                        validation_details
                    )
                )
                
                return True, trade_details
            
            # ORDRE RÉEL
            contract = self.data_provider.get_contract(ticker)
            if not contract:
                print(f"❌ Contrat non trouvé pour {ticker}")
                return False, None
            
            # Ordre bracket (entrée + SL + TP)
            parent_order = LimitOrder(
                action='BUY',
                totalQuantity=quantity,
                lmtPrice=current_price * 1.002  # +0.2% pour être sûr d'avoir fill
            )
            
            stop_loss_order = Order()
            stop_loss_order.orderType = 'STP'
            stop_loss_order.action = 'SELL'
            stop_loss_order.totalQuantity = quantity
            stop_loss_order.auxPrice = stop_loss
            
            take_profit_order = Order()
            take_profit_order.orderType = 'LMT'
            take_profit_order.action = 'SELL'
            take_profit_order.totalQuantity = quantity
            take_profit_order.lmtPrice = take_profit
            
            # Placer bracket order
            bracket = self.ib.bracketOrder(
                parent_order,
                takeProfitPrice=take_profit,
                stopLossPrice=stop_loss
            )
            
            for order in bracket:
                self.ib.placeOrder(contract, order)
            
            print(f"✅ Ordre bracket placé pour {ticker}")
            
            # Ajouter position
            self.risk_manager.add_position(
                ticker,
                current_price,
                quantity,
                stop_loss,
                take_profit
            )
            
            trade_details = {
                'ticker': ticker,
                'entry_price': current_price,
                'quantity': quantity,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'dry_run': False
            }
            
            # Notification
            asyncio.run(
                self.telegram.notify_entry(
                    ticker,
                    current_price,
                    quantity,
                    validation_details
                )
            )
            
            return True, trade_details
            
        except Exception as e:
            error_msg = f"Erreur entrée position {ticker}: {str(e)}"
            print(f"❌ {error_msg}")
            asyncio.run(self.telegram.notify_error(error_msg))
            return False, None
    
    def exit_position(self, ticker: str, reason: str) -> Tuple[bool, Optional[Dict]]:
        """
        Sort d'une position
        
        Args:
            ticker: Symbole
            reason: Raison de sortie
        
        Returns: (success, exit_details)
        """
        try:
            # Récupérer position
            position = self.risk_manager.get_position(ticker)
            if not position:
                print(f"❌ Position {ticker} non trouvée")
                return False, None
            
            # Prix actuel
            price_data = self.data_provider.get_current_price(ticker)
            if not price_data:
                print(f"❌ Impossible d'obtenir prix pour {ticker}")
                return False, None
            
            exit_price = price_data['bid']  # Vendre au bid
            quantity = position['quantity']
            entry_price = position['entry_price']
            
            print(f"\n{'='*60}")
            print(f"📉 PRÉPARATION VENTE {ticker}")
            print(f"{'='*60}")
            print(f"Raison: {reason}")
            print(f"Prix entrée: ${entry_price:.2f}")
            print(f"Prix sortie: ${exit_price:.2f}")
            print(f"Quantité: {quantity}")
            print(f"{'='*60}\n")
            
            if DRY_RUN_MODE:
                print("🧪 MODE DRY RUN - Pas d'ordre réel envoyé")
                
                # Fermer position
                closed = self.risk_manager.close_position(ticker, exit_price, reason)
                
                # Notification appropriée
                pnl = closed['pnl']
                pnl_pct = closed['pnl_pct']
                
                if reason in ['TAKE_PROFIT', 'TP']:
                    asyncio.run(
                        self.telegram.notify_take_profit(
                            ticker,
                            entry_price,
                            exit_price,
                            quantity,
                            pnl_pct,
                            pnl
                        )
                    )
                elif reason in ['STOP_LOSS', 'SL']:
                    asyncio.run(
                        self.telegram.notify_stop_loss(
                            ticker,
                            entry_price,
                            exit_price,
                            quantity,
                            pnl_pct,
                            pnl
                        )
                    )
                else:
                    asyncio.run(
                        self.telegram.notify_emergency_exit(
                            ticker,
                            reason,
                            entry_price,
                            exit_price,
                            quantity
                        )
                    )
                
                return True, closed
            
            # ORDRE RÉEL
            contract = self.data_provider.get_contract(ticker)
            if not contract:
                print(f"❌ Contrat non trouvé pour {ticker}")
                return False, None
            
            # Market order pour sortie rapide
            order = MarketOrder(
                action='SELL',
                totalQuantity=quantity
            )
            
            trade = self.ib.placeOrder(contract, order)
            
            # Attendre fill (max 30 secondes)
            self.ib.sleep(30)
            
            print(f"✅ Ordre vente exécuté pour {ticker}")
            
            # Fermer position
            closed = self.risk_manager.close_position(ticker, exit_price, reason)
            
            # Notifications
            pnl = closed['pnl']
            pnl_pct = closed['pnl_pct']
            
            if reason in ['TAKE_PROFIT', 'TP']:
                asyncio.run(
                    self.telegram.notify_take_profit(
                        ticker,
                        entry_price,
                        exit_price,
                        quantity,
                        pnl_pct,
                        pnl
                    )
                )
            elif reason in ['STOP_LOSS', 'SL']:
                asyncio.run(
                    self.telegram.notify_stop_loss(
                        ticker,
                        entry_price,
                        exit_price,
                        quantity,
                        pnl_pct,
                        pnl
                    )
                )
            else:
                asyncio.run(
                    self.telegram.notify_emergency_exit(
                        ticker,
                        reason,
                        entry_price,
                        exit_price,
                        quantity
                    )
                )
            
            return True, closed
            
        except Exception as e:
            error_msg = f"Erreur sortie position {ticker}: {str(e)}"
            print(f"❌ {error_msg}")
            asyncio.run(self.telegram.notify_error(error_msg))
            return False, None
    
    def check_emergency_exit_conditions(self, ticker: str) -> Tuple[bool, str]:
        """
        Vérifie conditions de sortie urgente
        
        Returns: (should_exit, reason)
        """
        # 1. News négatives
        has_negative, news_list = self.news_monitor.has_negative_news(ticker, minutes=10)
        if has_negative:
            return True, f"News négative: {news_list[0].get('title', 'N/A')}"
        
        # 2. Downgrade
        has_downgrade, downgrades = self.news_monitor.has_recent_downgrade(ticker, days=1)
        if has_downgrade:
            analyst = downgrades[0].get('analyst', 'N/A')
            return True, f"Downgrade: {analyst}"
        
        # 3. Spread trop large
        orderflow = self.data_provider.get_orderflow(ticker)
        if orderflow and orderflow['spread_pct'] > SPREAD_MAX_PCT * 100 * 2:  # 2x limite normale
            return True, f"Spread excessif: {orderflow['spread_pct']:.2f}%"
        
        return False, "OK"
    
    def monitor_open_positions(self):
        """Surveille positions ouvertes pour sorties urgentes"""
        open_positions = self.risk_manager.get_open_positions()
        
        for position in open_positions:
            ticker = position['ticker']
            
            # Vérifier conditions urgentes
            should_exit, reason = self.check_emergency_exit_conditions(ticker)
            
            if should_exit:
                print(f"⚠️  Sortie urgente détectée pour {ticker}: {reason}")
                self.exit_position(ticker, f"URGENCE: {reason}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("TEST TRADING MANAGER")
    print("="*60 + "\n")
    
    from stock_data import StockDataProvider
    from risk_manager import RiskManager
    from telegram_notifier import TelegramNotifier
    from news_monitor import NewsMonitor
    
    # Initialisation
    provider = StockDataProvider()
    risk_mgr = RiskManager(capital=10000)
    telegram = TelegramNotifier()
    news_mon = NewsMonitor()
    
    trading_mgr = TradingManager(provider, risk_mgr, telegram, news_mon)
    
    print("✅ Trading Manager initialisé")
    print(f"📊 Mode: {'DRY RUN' if DRY_RUN_MODE else 'RÉEL'}")
    print(f"💰 Capital: ${risk_mgr.capital:,.2f}")
    
    try:
        provider.connect()
        
        # Test calcul SL/TP
        test_price = 150.00
        sl, tp = trading_mgr.calculate_stop_take_prices(test_price)
        print(f"\n📏 Calculs pour prix ${test_price:.2f}:")
        print(f"   Stop-Loss: ${sl:.2f} (-{STOP_LOSS_PCT*100}%)")
        print(f"   Take-Profit: ${tp:.2f} (+{TAKE_PROFIT_PCT*100}%)")
        
        # Test surveillance positions
        print(f"\n👁️  Surveillance positions ouvertes...")
        trading_mgr.monitor_open_positions()
        print(f"   {len(risk_mgr.get_open_positions())} position(s) surveillée(s)")
        
    finally:
        provider.disconnect()

