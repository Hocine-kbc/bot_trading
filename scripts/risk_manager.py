"""
Gestion du risque et limites de trading
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
from config import (
    MAX_POSITIONS,
    DAILY_LOSS_LIMIT,
    WEEKLY_LOSS_LIMIT,
    POSITION_SIZE_PCT,
    POSITIONS_FILE,
    TIMEZONE
)


class RiskManager:
    """Gestionnaire de risque"""
    
    def __init__(self, capital: float):
        self.capital = capital
        self.tz = pytz.timezone(TIMEZONE)
        self.positions_file = POSITIONS_FILE
        self.positions = self._load_positions()
    
    def _load_positions(self) -> Dict:
        """Charge positions depuis fichier"""
        try:
            with open(self.positions_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement positions: {e}")
            return {
                'open_positions': [],
                'closed_positions': [],
                'statistics': {}
            }
    
    def _save_positions(self):
        """Sauvegarde positions"""
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            print(f"❌ Erreur sauvegarde positions: {e}")
    
    def get_open_positions(self) -> List[Dict]:
        """Retourne positions ouvertes"""
        return self.positions.get('open_positions', [])
    
    def get_position(self, ticker: str) -> Optional[Dict]:
        """Récupère une position spécifique"""
        for pos in self.get_open_positions():
            if pos['ticker'] == ticker:
                return pos
        return None
    
    def can_open_position(self) -> Tuple[bool, str]:
        """Vérifie si on peut ouvrir nouvelle position"""
        open_count = len(self.get_open_positions())
        
        if open_count >= MAX_POSITIONS:
            return False, f"Limite positions atteinte ({open_count}/{MAX_POSITIONS})"
        
        return True, "OK"
    
    def calculate_position_size(self, price: float) -> int:
        """Calcule taille position (en quantité)"""
        max_value = self.capital * POSITION_SIZE_PCT
        quantity = int(max_value / price)
        return max(1, quantity)  # Au moins 1 action
    
    def get_daily_pnl(self) -> float:
        """Calcule PnL du jour"""
        today = datetime.now(self.tz).date()
        
        daily_pnl = 0.0
        
        # PnL des positions fermées aujourd'hui
        for pos in self.positions.get('closed_positions', []):
            exit_date = datetime.fromisoformat(pos['exit_time']).date()
            if exit_date == today:
                daily_pnl += pos['pnl']
        
        return daily_pnl
    
    def get_weekly_pnl(self) -> float:
        """Calcule PnL de la semaine"""
        now = datetime.now(self.tz)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        weekly_pnl = 0.0
        
        for pos in self.positions.get('closed_positions', []):
            exit_time = datetime.fromisoformat(pos['exit_time'])
            if exit_time >= week_start:
                weekly_pnl += pos['pnl']
        
        return weekly_pnl
    
    def check_daily_loss_limit(self) -> Tuple[bool, str]:
        """Vérifie limite perte journalière"""
        daily_pnl = self.get_daily_pnl()
        max_loss = self.capital * DAILY_LOSS_LIMIT
        
        if daily_pnl <= -max_loss:
            return False, f"Limite perte journalière atteinte: ${daily_pnl:,.2f}"
        
        return True, "OK"
    
    def check_weekly_loss_limit(self) -> Tuple[bool, str]:
        """Vérifie limite perte hebdomadaire"""
        weekly_pnl = self.get_weekly_pnl()
        max_loss = self.capital * WEEKLY_LOSS_LIMIT
        
        if weekly_pnl <= -max_loss:
            return False, f"Limite perte hebdomadaire atteinte: ${weekly_pnl:,.2f}"
        
        return True, "OK"
    
    def can_trade(self) -> Tuple[bool, str]:
        """Validation complète des limites de risque"""
        # Vérifier limite positions
        can_open, reason = self.can_open_position()
        if not can_open:
            return False, reason
        
        # Vérifier perte journalière
        daily_ok, reason = self.check_daily_loss_limit()
        if not daily_ok:
            return False, reason
        
        # Vérifier perte hebdomadaire
        weekly_ok, reason = self.check_weekly_loss_limit()
        if not weekly_ok:
            return False, reason
        
        return True, "OK"
    
    def add_position(self, ticker: str, entry_price: float, quantity: int, stop_loss: float, take_profit: float):
        """Ajoute nouvelle position"""
        position = {
            'ticker': ticker,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': datetime.now(self.tz).isoformat(),
            'value': entry_price * quantity
        }
        
        self.positions['open_positions'].append(position)
        self._save_positions()
        
        print(f"✅ Position ajoutée: {ticker} x{quantity} @ ${entry_price:.2f}")
    
    def close_position(self, ticker: str, exit_price: float, exit_reason: str):
        """Ferme une position"""
        position = self.get_position(ticker)
        
        if not position:
            print(f"❌ Position {ticker} non trouvée")
            return None
        
        # Calcul PnL
        entry_price = position['entry_price']
        quantity = position['quantity']
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # Créer position fermée
        closed_position = {
            **position,
            'exit_price': exit_price,
            'exit_time': datetime.now(self.tz).isoformat(),
            'exit_reason': exit_reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        }
        
        # Mettre à jour
        self.positions['open_positions'] = [
            p for p in self.get_open_positions()
            if p['ticker'] != ticker
        ]
        self.positions['closed_positions'].append(closed_position)
        
        # Mettre à jour stats
        self._update_statistics()
        
        self._save_positions()
        
        print(f"✅ Position fermée: {ticker} | PnL: ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
        
        return closed_position
    
    def _update_statistics(self):
        """Met à jour statistiques"""
        closed = self.positions.get('closed_positions', [])
        
        if not closed:
            return
        
        total_trades = len(closed)
        winning_trades = len([p for p in closed if p['pnl'] > 0])
        losing_trades = len([p for p in closed if p['pnl'] < 0])
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        wins = [p['pnl'] for p in closed if p['pnl'] > 0]
        losses = [p['pnl'] for p in closed if p['pnl'] < 0]
        
        average_gain = sum(wins) / len(wins) if wins else 0
        average_loss = sum(losses) / len(losses) if losses else 0
        
        profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0
        
        total_pnl = sum(p['pnl'] for p in closed)
        
        self.positions['statistics'] = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'average_gain': average_gain,
            'average_loss': average_loss,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl
        }
    
    def get_statistics(self) -> Dict:
        """Retourne statistiques"""
        return self.positions.get('statistics', {})
    
    def get_risk_summary(self) -> Dict:
        """Résumé complet du risque"""
        daily_pnl = self.get_daily_pnl()
        weekly_pnl = self.get_weekly_pnl()
        open_positions = len(self.get_open_positions())
        
        return {
            'capital': self.capital,
            'open_positions': open_positions,
            'max_positions': MAX_POSITIONS,
            'daily_pnl': daily_pnl,
            'daily_limit': -self.capital * DAILY_LOSS_LIMIT,
            'weekly_pnl': weekly_pnl,
            'weekly_limit': -self.capital * WEEKLY_LOSS_LIMIT,
            'can_trade': self.can_trade()[0]
        }


if __name__ == '__main__':
    # Test
    print("\n" + "="*60)
    print("TEST RISK MANAGER")
    print("="*60 + "\n")
    
    # Capital de test
    capital = 10000
    risk_mgr = RiskManager(capital)
    
    print(f"💰 Capital: ${capital:,.2f}\n")
    
    # Résumé risque
    summary = risk_mgr.get_risk_summary()
    print("📊 Résumé risque:")
    print(f"   Positions ouvertes: {summary['open_positions']}/{summary['max_positions']}")
    print(f"   PnL jour: ${summary['daily_pnl']:+,.2f} (limite: ${summary['daily_limit']:,.2f})")
    print(f"   PnL semaine: ${summary['weekly_pnl']:+,.2f} (limite: ${summary['weekly_limit']:,.2f})")
    print(f"   Peut trader: {'✅ Oui' if summary['can_trade'] else '❌ Non'}")
    
    # Test calcul position
    print(f"\n📏 Calcul taille position:")
    test_price = 150.00
    quantity = risk_mgr.calculate_position_size(test_price)
    value = quantity * test_price
    print(f"   Prix: ${test_price:.2f}")
    print(f"   Quantité: {quantity}")
    print(f"   Valeur: ${value:,.2f} ({value/capital*100:.1f}% du capital)")
    
    # Statistiques
    stats = risk_mgr.get_statistics()
    if stats:
        print(f"\n📈 Statistiques:")
        print(f"   Total trades: {stats.get('total_trades', 0)}")
        print(f"   Win rate: {stats.get('win_rate', 0):.1f}%")
        print(f"   PnL total: ${stats.get('total_pnl', 0):+,.2f}")

