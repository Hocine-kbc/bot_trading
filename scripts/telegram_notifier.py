"""
Notifications Telegram
Ce fichier gère l'envoi de notifications vers Telegram pour informer
l'utilisateur des actions du bot (achats, ventes, erreurs, etc.)
"""

# ============================================================
# IMPORTS - Bibliothèques nécessaires
# ============================================================

import asyncio  # Permet d'exécuter du code asynchrone (non-bloquant)
from datetime import datetime  # Pour obtenir l'heure actuelle des notifications
from typing import Optional  # Pour typer les variables optionnelles
from telegram import Bot  # Classe principale de la bibliothèque python-telegram-bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NOTIFICATION_COOLDOWN_SECONDS  # Nos paramètres depuis .env
import time  # Pour mesurer le temps écoulé (anti-spam)


# ============================================================
# CLASSE PRINCIPALE - TelegramNotifier
# ============================================================

class TelegramNotifier:
    """
    Gestionnaire de notifications Telegram
    Cette classe envoie des messages formatés à votre chat Telegram
    """
    
    # --------------------------------------------------------
    # INITIALISATION
    # --------------------------------------------------------
    
    def __init__(self):
        """
        Constructeur - appelé quand on crée un TelegramNotifier()
        Initialise les variables nécessaires
        """
        self.bot_token = TELEGRAM_BOT_TOKEN  # Token secret du bot (depuis .env)
        self.chat_id = TELEGRAM_CHAT_ID  # ID du chat où envoyer les messages (depuis .env)
        self.bot = None  # L'objet Bot sera créé plus tard (lazy loading)
        self.last_notifications = {}  # Dictionnaire pour stocker quand on a envoyé chaque notif (anti-spam)
    
    # --------------------------------------------------------
    # MÉTHODES INTERNES (commencent par _)
    # --------------------------------------------------------
    
    async def _init_bot(self):
        """
        Initialise le bot Telegram si pas encore fait
        'async' signifie que cette fonction est asynchrone
        """
        if not self.bot:  # Si le bot n'existe pas encore
            self.bot = Bot(token=self.bot_token)  # Créer le bot avec notre token
    
    def _can_send(self, ticker: str, notification_type: str) -> bool:
        """
        Vérifie si on peut envoyer une notification (anti-spam)
        Empêche d'envoyer la même notif plusieurs fois en peu de temps
        
        Args:
            ticker: Le symbole de l'action (ex: 'AAPL')
            notification_type: Le type de notif (ex: 'entry', 'stop_loss')
        
        Returns:
            True si on peut envoyer, False sinon
        """
        # Créer une clé unique pour cette combinaison ticker + type
        key = f"{ticker}_{notification_type}"  # Ex: "AAPL_entry"
        
        # Vérifier si on a déjà envoyé cette notif récemment
        if key in self.last_notifications:
            # Calculer le temps écoulé depuis la dernière notif
            elapsed = time.time() - self.last_notifications[key]
            # Si pas assez de temps s'est écoulé, bloquer l'envoi
            if elapsed < NOTIFICATION_COOLDOWN_SECONDS:  # 300 secondes = 5 minutes par défaut
                return False  # Ne pas envoyer (trop tôt)
        
        # Enregistrer l'heure actuelle pour cette notif
        self.last_notifications[key] = time.time()
        return True  # OK pour envoyer
    
    # --------------------------------------------------------
    # MÉTHODE D'ENVOI PRINCIPALE
    # --------------------------------------------------------
    
    async def send_message(self, message: str, parse_mode: str = 'Markdown'):
        """
        Envoie un message Telegram
        
        Args:
            message: Le texte à envoyer
            parse_mode: Le format ('Markdown' permet le gras, italique, etc.)
        
        Returns:
            True si envoyé avec succès, False sinon
        """
        try:
            await self._init_bot()  # S'assurer que le bot est initialisé
            # Envoyer le message via l'API Telegram
            await self.bot.send_message(
                chat_id=self.chat_id,  # À qui envoyer
                text=message,  # Le contenu du message
                parse_mode=parse_mode  # Le format (Markdown)
            )
            return True  # Succès
        except Exception as e:  # Si une erreur survient
            print(f"❌ Erreur envoi Telegram: {e}")  # Afficher l'erreur dans la console
            return False  # Échec
    
    # --------------------------------------------------------
    # NOTIFICATIONS SPÉCIFIQUES
    # --------------------------------------------------------
    
    async def notify_entry(self, ticker: str, price: float, quantity: int, filters_passed: dict):
        """
        Notification d'ACHAT - Envoyée quand le bot achète une action
        
        Args:
            ticker: Symbole de l'action (ex: 'AAPL')
            price: Prix d'achat
            quantity: Nombre d'actions achetées
            filters_passed: Dictionnaire des filtres validés (non utilisé ici)
        """
        # Vérifier anti-spam - ne pas envoyer si notif récente pour ce ticker
        if not self._can_send(ticker, 'entry'):
            return  # Sortir sans rien faire
        
        # Obtenir l'heure actuelle formatée (ex: "14:30:25")
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Construire le message avec formatage Markdown
        # Les ** font du texte en GRAS
        # Les f-strings permettent d'insérer des variables avec {variable}
        # :.2f = 2 décimales, :,.2f = séparateur milliers + 2 décimales
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
        
        # Envoyer le message
        await self.send_message(message)
    
    async def notify_take_profit(self, ticker: str, entry_price: float, exit_price: float, quantity: int, profit_pct: float, profit_amount: float):
        """
        Notification TAKE PROFIT - Envoyée quand on vend avec gain
        
        Args:
            ticker: Symbole de l'action
            entry_price: Prix d'achat initial
            exit_price: Prix de vente
            quantity: Nombre d'actions vendues
            profit_pct: Pourcentage de gain
            profit_amount: Montant du gain en $
        """
        # Vérifier anti-spam
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
        """
        Notification STOP LOSS - Envoyée quand on vend avec perte
        
        Args:
            ticker: Symbole de l'action
            entry_price: Prix d'achat initial
            exit_price: Prix de vente
            quantity: Nombre d'actions vendues
            loss_pct: Pourcentage de perte
            loss_amount: Montant de la perte en $
        """
        # Vérifier anti-spam
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
        """
        Notification SORTIE URGENTE - Envoyée en cas de vente forcée
        (ex: limite de perte journalière atteinte, news négative, etc.)
        
        Args:
            ticker: Symbole de l'action
            reason: Raison de la sortie urgente
            entry_price: Prix d'achat initial
            exit_price: Prix de vente
            quantity: Nombre d'actions vendues
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Calculer le PnL (Profit and Loss = Gain/Perte)
        # Formule: ((prix_vente - prix_achat) / prix_achat) * 100
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        # Montant en dollars
        pnl_amount = (exit_price - entry_price) * quantity
        
        # Choisir emoji selon si gain ou perte
        emoji = "🟢" if pnl_amount >= 0 else "🔴"  # Vert si positif, Rouge si négatif
        
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
        # Note: :+.2f affiche le signe + ou - devant le nombre
        
        await self.send_message(message)
    
    async def notify_error(self, error_msg: str):
        """
        Notification ERREUR - Envoyée quand quelque chose ne va pas
        
        Args:
            error_msg: Description de l'erreur
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
❌ **ERREUR** ❌

{error_msg}

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_pause(self, reason: str):
        """
        Notification PAUSE - Envoyée quand le bot arrête de trader
        (ex: limite de perte atteinte, hors horaires, etc.)
        
        Args:
            reason: Raison de la pause
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
⏸️ **PAUSE TRADING** ⏸️

**Raison**: {reason}

Le bot est en pause et ne prendra plus de nouvelles positions.

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_daily_summary(self, stats: dict):
        """
        Notification RÉSUMÉ JOURNALIER - Envoyée en fin de journée
        Récapitule toutes les performances du jour
        
        Args:
            stats: Dictionnaire contenant les statistiques du jour
        """
        # Format avec date complète pour le résumé
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Extraire les stats du dictionnaire avec valeurs par défaut si absentes
        # .get('clé', valeur_defaut) retourne valeur_defaut si la clé n'existe pas
        trades_count = stats.get('trades_count', 0)  # Nombre total de trades
        winning = stats.get('winning_trades', 0)  # Trades gagnants
        losing = stats.get('losing_trades', 0)  # Trades perdants
        win_rate = stats.get('win_rate', 0)  # Taux de réussite en %
        pnl = stats.get('total_pnl', 0)  # Profit/Perte total en $
        
        # Emoji selon performance
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
    
    async def notify_bot_started(self, capital: float, dry_run: bool, watchlist_count: int):
        """
        Notification DÉMARRAGE DU BOT
        Envoyée quand le bot se connecte avec succès à IBKR
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mode = "🧪 DRY RUN (simulation)" if dry_run else "💰 RÉEL"
        
        message = f"""
🤖 **BOT DÉMARRÉ** 🤖

**Mode**: {mode}
**Capital**: ${capital:,.2f}
**Watchlist**: {watchlist_count} actions

✅ Connexion IBKR OK
✅ Telegram OK

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_market_unfavorable(self, details: dict):
        """
        Notification MARCHÉ DÉFAVORABLE
        Envoyée quand les conditions de marché ne permettent pas de trader
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Extraire les infos
        spy = details.get('spy', {})
        qqq = details.get('qqq', {})
        vix = details.get('vix', {})
        
        spy_change = spy.get('change_pct', 0) if spy else 0
        qqq_change = qqq.get('change_pct', 0) if qqq else 0
        vix_level = vix.get('level', 20) if vix else 20
        
        spy_emoji = "✅" if spy.get('is_bullish', False) else "❌"
        qqq_emoji = "✅" if qqq.get('is_bullish', False) else "❌"
        vix_emoji = "✅" if vix.get('is_favorable', True) else "❌"
        
        message = f"""
📊 **MARCHÉ DÉFAVORABLE** 📊

{spy_emoji} SPY: {spy_change:+.2f}%
{qqq_emoji} QQQ: {qqq_change:+.2f}%
{vix_emoji} VIX: {vix_level:.1f}

⏸️ Le bot attend des conditions favorables.

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_market_closed(self, reason: str):
        """
        Notification MARCHÉ FERMÉ
        Envoyée quand le bot détecte que le marché US est fermé
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        message = f"""
🌙 **MARCHÉ FERMÉ** 🌙

{reason}

Le bot attend l'ouverture du marché US.
📅 Horaires: 15h30 - 22h00 (Paris)

⏰ {timestamp}
"""
        
        await self.send_message(message)
    
    async def notify_signal_detected(self, ticker: str, pattern: str, confidence: int):
        """
        Notification SIGNAL DÉTECTÉ - Envoyée quand un pattern est repéré
        (optionnel, pour être informé des opportunités)
        
        Args:
            ticker: Symbole de l'action
            pattern: Nom du pattern détecté (ex: 'HAMMER', 'BULLISH_ENGULFING')
            confidence: Niveau de confiance en %
        """
        # Vérifier anti-spam
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


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def send_telegram_sync(message: str):
    """
    Helper synchrone pour envoyer un message
    Permet d'envoyer depuis du code non-async (synchrone classique)
    
    Args:
        message: Le texte à envoyer
    
    Exemple d'utilisation:
        send_telegram_sync("Ceci est un test")
    """
    notifier = TelegramNotifier()  # Créer un notifier
    asyncio.run(notifier.send_message(message))  # Exécuter la fonction async


# ============================================================
# INSTANCE GLOBALE
# ============================================================

# Créer une instance globale pour pouvoir l'importer facilement
# Usage: from telegram_notifier import telegram_notifier
telegram_notifier = TelegramNotifier()


# ============================================================
# CODE DE TEST
# ============================================================

# Ce code ne s'exécute QUE si on lance ce fichier directement
# (python telegram_notifier.py)
# Il ne s'exécute PAS si on importe le fichier depuis un autre fichier

if __name__ == '__main__':
    # Afficher un en-tête de test
    print("\n" + "="*60)
    print("TEST TELEGRAM NOTIFIER")
    print("="*60 + "\n")
    ########################### ENVOI DE MESSAGE TELEGRAME POUR TESTER ############################
    async def test_notifications():
        """
        Fonction de test qui envoie plusieurs notifications
        """
        notifier = TelegramNotifier()  # Créer un notifier pour les tests
        
        print("📤 Envoi notifications test...\n")
        
        # Test 1: Notification d'achat
        await notifier.notify_entry('AAPL', 150.50, 10, {})
        print("✅ Notification achat envoyée")
        
        # Attendre 1 seconde entre les messages (pour ne pas surcharger)
        await asyncio.sleep(1)
        
        # Test 2: Notification take profit
        await notifier.notify_take_profit('AAPL', 150.50, 180.60, 10, 20.0, 301.00)
        print("✅ Notification take profit envoyée")
        
        await asyncio.sleep(1)
        
        # Test 3: Notification erreur
        await notifier.notify_error("Connexion IBKR perdue")
        print("✅ Notification erreur envoyée")
        
        print("\n🎉 Tests terminés - Vérifiez votre Telegram!")
    
    # Vérifier que les credentials sont configurés
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        # Lancer les tests
        asyncio.run(test_notifications())
    else:
        # Afficher un avertissement si pas configuré
        print("⚠️  Token ou Chat ID manquant")
        print("Configurez TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID dans .env")
