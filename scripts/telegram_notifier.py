"""
Notifications Telegram
"""
import asyncio
from datetime import datetime
from typing import Optional
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NOTIFICATION_COOLDOWN_SECONDS
import time


class TelegramNotifier:
    """Gestionnaire de notifications Telegram"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.bot = None
        self.last_notifications = {}  # Anti-spam
    
    async def _init_bot(self):
        """Initialise le bot Telegram"""
        if not self.bot:
            self.bot = Bot(token=self.bot_token)
    
    def _can_send(self, ticker: str, notification_type: str) -> bool:
        """Vérifie cooldown anti-spam"""
        key = f"{ticker}_{notification_type}"
        
        if key in self.last_notifications:
            elapsed = time.time() - self.last_notifications[key]
            if elapsed < NOTIFICATION_COOLDOWN_SECONDS:
                return False
        
        self.last_notifications[key] = time.time()
        return True
    
    async def send_message(self, message: str, parse_mode: str = 'Markdown'):
        """Envoie message Telegram"""
        try:
            await self._init_bot()
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            print(f"❌ Erreur envoi Telegram: {e}")
            return False
    
    async def notify_entry(self, ticker: str, price: float, quantity: int, filters_passed: dict):
        """Notification achat"""
        if not self._can_send(ticker, 'entry'):
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
🟢 **ACHAT** 🟢

**Ticker**: {ticker}
**Prix**: ${price:.2f}
**Quantité**: {quantity}
**Valeur**: ${price * quantity:,.2f}

**Stop-Loss**: -5% (${price * 0.95:.2f})
**Take-Profit**: +20% (${price * 1.20:.2f})

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_take_profit(self, ticker: str, entry_price: float, exit_price: float, quantity: int, profit_pct: float, profit_amount: float):
        """Notification take profit"""
        if not self._can_send(ticker, 'take_profit'):
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
🎯 **TAKE PROFIT** 🎯

**Ticker**: {ticker}
**Entrée**: ${entry_price:.2f}
**Sortie**: ${exit_price:.2f}
**Quantité**: {quantity}

**Gain**: +{profit_pct:.2f}% (${profit_amount:,.2f})

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_stop_loss(self, ticker: str, entry_price: float, exit_price: float, quantity: int, loss_pct: float, loss_amount: float):
        """Notification stop loss"""
        if not self._can_send(ticker, 'stop_loss'):
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
🛑 **STOP LOSS** 🛑

**Ticker**: {ticker}
**Entrée**: ${entry_price:.2f}
**Sortie**: ${exit_price:.2f}
**Quantité**: {quantity}

**Perte**: {loss_pct:.2f}% (${loss_amount:,.2f})

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_emergency_exit(self, ticker: str, reason: str, entry_price: float, exit_price: float, quantity: int):
        """Notification sortie urgente"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        pnl_amount = (exit_price - entry_price) * quantity
        
        emoji = "🟢" if pnl_amount >= 0 else "🔴"
        
        message = f"""
⚠️ **SORTIE URGENCE** ⚠️

**Ticker**: {ticker}
**Raison**: {reason}

**Entrée**: ${entry_price:.2f}
**Sortie**: ${exit_price:.2f}
**Quantité**: {quantity}

{emoji} **PnL**: {pnl_pct:+.2f}% (${pnl_amount:+,.2f})

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_error(self, error_msg: str):
        """Notification erreur"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
❌ **ERREUR** ❌

{error_msg}

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_pause(self, reason: str):
        """Notification pause trading"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
⏸️ **PAUSE TRADING** ⏸️

**Raison**: {reason}

Le bot est en pause et ne prendra plus de nouvelles positions.

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_daily_summary(self, stats: dict):
        """Résumé journalier"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        trades_count = stats.get('trades_count', 0)
        winning = stats.get('winning_trades', 0)
        losing = stats.get('losing_trades', 0)
        win_rate = stats.get('win_rate', 0)
        pnl = stats.get('total_pnl', 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        message = f"""
📊 **RÉSUMÉ JOURNALIER** 📊

**Trades**: {trades_count}
• Gagnants: {winning}
• Perdants: {losing}
• Win Rate: {win_rate:.1f}%

{emoji} **PnL Total**: ${pnl:+,.2f}

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_signal_detected(self, ticker: str, pattern: str, confidence: int):
        """Notification signal détecté (optionnel)"""
        if not self._can_send(ticker, 'signal'):
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
🔔 **SIGNAL DÉTECTÉ** 🔔

**Ticker**: {ticker}
**Pattern**: {pattern}
**Confiance**: {confidence}%

⏰ {timestamp}
"""
        
        await self.send_message(message)


# Fonctions helper synchrones pour appeler depuis code non-async
def send_telegram_sync(message: str):
    """Helper synchrone pour envoi message"""
    notifier = TelegramNotifier()
    asyncio.run(notifier.send_message(message))


# Instance globale
telegram_notifier = TelegramNotifier()


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST TELEGRAM NOTIFIER")
    print("="*60 + "\n")
    
    async def test_notifications():
        notifier = TelegramNotifier()
        
        print("📤 Envoi notifications test...\n")
        
        # Test achat
        await notifier.notify_entry('AAPL', 150.50, 10, {})
        print("✅ Notification achat envoyée")
        
        await asyncio.sleep(1)
        
        # Test take profit
        await notifier.notify_take_profit('AAPL', 150.50, 180.60, 10, 20.0, 301.00)
        print("✅ Notification take profit envoyée")
        
        await asyncio.sleep(1)
        
        # Test erreur
        await notifier.notify_error("Connexion IBKR perdue")
        print("✅ Notification erreur envoyée")
        
        print("\n🎉 Tests terminés - Vérifiez votre Telegram!")
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        asyncio.run(test_notifications())
    else:
        print("⚠️  Token ou Chat ID manquant")
        print("Configurez TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID dans .env")

