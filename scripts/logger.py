"""
Configuration du système de logging
- Logs fichiers + console
- Rotation automatique des fichiers
- Niveaux séparés (général, trades, erreurs)
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

from config import LOGS_DIR

# Créer le dossier logs s'il n'existe pas
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Configure un logger avec fichier + console
    
    Args:
        name: Nom du logger
        log_file: Nom du fichier log
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Éviter les doublons si le logger existe déjà
    if logger.handlers:
        return logger
    
    # Format des logs
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler fichier avec rotation (max 5MB, garde 5 fichiers)
    file_handler = RotatingFileHandler(
        LOGS_DIR / log_file,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# ============================================================================
# LOGGERS PRÉ-CONFIGURÉS
# ============================================================================

# Logger principal du bot
bot_logger = setup_logger('bot', 'bot.log', logging.INFO)

# Logger des trades (achats/ventes)
trade_logger = setup_logger('trades', 'trades.log', logging.INFO)

# Logger des erreurs uniquement
error_logger = setup_logger('errors', 'errors.log', logging.ERROR)


# ============================================================================
# FONCTIONS HELPER POUR LOGGING FACILE
# ============================================================================

def log_info(message: str):
    """Log info général"""
    bot_logger.info(message)


def log_warning(message: str):
    """Log warning"""
    bot_logger.warning(message)


def log_error(message: str):
    """Log erreur (fichier erreurs + bot.log)"""
    bot_logger.error(message)
    error_logger.error(message)


def log_trade(action: str, ticker: str, price: float, quantity: int = 0, 
              pnl: float = None, reason: str = ""):
    """
    Log un trade (achat/vente)
    
    Args:
        action: BUY, SELL, STOP_LOSS, TAKE_PROFIT
        ticker: Symbol de l'action
        price: Prix d'exécution
        quantity: Nombre d'actions
        pnl: Profit/Loss (pour les ventes)
        reason: Raison du trade
    """
    if pnl is not None:
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        msg = f"{action} | {ticker} | ${price:.2f} | {quantity} actions | PnL: {pnl_str} | {reason}"
    else:
        msg = f"{action} | {ticker} | ${price:.2f} | {quantity} actions | {reason}"
    
    trade_logger.info(msg)
    bot_logger.info(f"💰 TRADE: {msg}")


def log_signal(ticker: str, signal_type: str, details: dict = None):
    """
    Log un signal détecté
    
    Args:
        ticker: Symbol
        signal_type: Type de signal (BREAKOUT, PATTERN, etc.)
        details: Détails additionnels
    """
    details_str = ""
    if details:
        details_str = " | " + " | ".join(f"{k}={v}" for k, v in details.items())
    
    msg = f"SIGNAL | {ticker} | {signal_type}{details_str}"
    bot_logger.info(f"📊 {msg}")


def log_market_status(spy_change: float, qqq_change: float, vix: float, status: str):
    """Log l'état du marché"""
    msg = f"MARKET | SPY: {spy_change:+.2%} | QQQ: {qqq_change:+.2%} | VIX: {vix:.1f} | {status}"
    bot_logger.info(f"📈 {msg}")


def log_startup(capital: float, dry_run: bool, paper: bool, watchlist_count: int):
    """Log au démarrage du bot"""
    bot_logger.info("=" * 60)
    bot_logger.info("🤖 BOT ACTIONS US MOMENTUM - DÉMARRAGE")
    bot_logger.info("=" * 60)
    bot_logger.info(f"Capital: ${capital:,.2f}")
    bot_logger.info(f"Mode: {'DRY RUN' if dry_run else 'RÉEL'}")
    bot_logger.info(f"Paper Trading: {'OUI' if paper else 'NON'}")
    bot_logger.info(f"Watchlist: {watchlist_count} actions")
    bot_logger.info("=" * 60)


def log_shutdown():
    """Log à l'arrêt du bot"""
    bot_logger.info("=" * 60)
    bot_logger.info("🛑 BOT ARRÊTÉ")
    bot_logger.info("=" * 60)


def log_cycle(cycle_num: int, opportunities: int, positions: int):
    """Log fin de cycle de scan"""
    bot_logger.info(f"🔄 Cycle #{cycle_num} terminé | Opportunités: {opportunities} | Positions: {positions}")


# ============================================================================
# TEST
# ============================================================================

if __name__ == '__main__':
    print("Test du système de logging...\n")
    
    log_startup(10000, True, True, 50)
    log_info("Test message info")
    log_warning("Test message warning")
    log_error("Test message erreur")
    log_market_status(0.0125, 0.0098, 18.5, "BULLISH")
    log_signal("AAPL", "BREAKOUT", {"resistance": 185.50, "volume": "150%"})
    log_trade("BUY", "AAPL", 185.75, 10, reason="Breakout confirmé")
    log_trade("TAKE_PROFIT", "AAPL", 222.90, 10, pnl=371.50, reason="+20% atteint")
    log_cycle(1, 3, 2)
    log_shutdown()
    
    print(f"\n✅ Logs créés dans: {LOGS_DIR}")
    print("   - bot.log")
    print("   - trades.log")
    print("   - errors.log")

