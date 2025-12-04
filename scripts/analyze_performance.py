"""
Analyseur de performance - Statistiques et optimisation
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Chemins
BASE_DIR = Path(__file__).resolve().parent.parent
POSITIONS_FILE = BASE_DIR / 'data' / 'positions.json'
TRADES_LOG = BASE_DIR / 'logs' / 'trades.log'


def load_positions():
    """Charge les positions depuis le fichier JSON"""
    try:
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement positions: {e}")
        return {'open_positions': [], 'closed_positions': [], 'statistics': {}}


def analyze_trades():
    """Analyse complète des trades"""
    data = load_positions()
    closed = data.get('closed_positions', [])
    
    if not closed:
        print("❌ Aucun trade clôturé à analyser")
        return
    
    print("\n" + "=" * 70)
    print("📊 ANALYSE DE PERFORMANCE")
    print("=" * 70)
    
    # Stats de base
    total_trades = len(closed)
    wins = [t for t in closed if t['pnl'] > 0]
    losses = [t for t in closed if t['pnl'] < 0]
    
    win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
    
    total_pnl = sum(t['pnl'] for t in closed)
    avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
    
    # Profit Factor
    gross_profit = sum(t['pnl'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    print(f"\n📈 RÉSUMÉ GLOBAL")
    print(f"   Total trades: {total_trades}")
    print(f"   Gagnants: {len(wins)} | Perdants: {len(losses)}")
    print(f"   Win Rate: {win_rate:.1f}%")
    print(f"   PnL Total: ${total_pnl:+,.2f}")
    print(f"   Gain moyen: ${avg_win:+,.2f}")
    print(f"   Perte moyenne: ${avg_loss:+,.2f}")
    print(f"   Profit Factor: {profit_factor:.2f}")
    
    # Analyse par raison de sortie
    print(f"\n📋 ANALYSE PAR TYPE DE SORTIE")
    by_reason = defaultdict(list)
    for t in closed:
        reason = t.get('exit_reason', 'UNKNOWN')
        by_reason[reason].append(t)
    
    for reason, trades in by_reason.items():
        count = len(trades)
        pnl = sum(t['pnl'] for t in trades)
        pct = (count / total_trades) * 100
        print(f"   {reason}: {count} trades ({pct:.1f}%) | PnL: ${pnl:+,.2f}")
    
    # Analyse par ticker (top performers)
    print(f"\n🎯 TOP PERFORMERS (par ticker)")
    by_ticker = defaultdict(list)
    for t in closed:
        by_ticker[t['ticker']].append(t)
    
    ticker_stats = []
    for ticker, trades in by_ticker.items():
        pnl = sum(t['pnl'] for t in trades)
        wins_count = len([t for t in trades if t['pnl'] > 0])
        wr = (wins_count / len(trades)) * 100
        ticker_stats.append({'ticker': ticker, 'trades': len(trades), 'pnl': pnl, 'win_rate': wr})
    
    # Top 5 par PnL
    ticker_stats.sort(key=lambda x: x['pnl'], reverse=True)
    print("\n   🏆 Top 5 (meilleurs):")
    for i, stat in enumerate(ticker_stats[:5], 1):
        print(f"   {i}. {stat['ticker']}: ${stat['pnl']:+,.2f} ({stat['trades']} trades, WR: {stat['win_rate']:.0f}%)")
    
    # Bottom 5 par PnL
    print("\n   💀 Bottom 5 (pires):")
    for i, stat in enumerate(ticker_stats[-5:], 1):
        print(f"   {i}. {stat['ticker']}: ${stat['pnl']:+,.2f} ({stat['trades']} trades, WR: {stat['win_rate']:.0f}%)")
    
    # Analyse temporelle
    print(f"\n⏰ ANALYSE PAR HEURE D'ENTRÉE")
    by_hour = defaultdict(list)
    for t in closed:
        try:
            entry_time = datetime.fromisoformat(t['entry_time'])
            hour = entry_time.hour
            by_hour[hour].append(t)
        except:
            pass
    
    for hour in sorted(by_hour.keys()):
        trades = by_hour[hour]
        pnl = sum(t['pnl'] for t in trades)
        wins_count = len([t for t in trades if t['pnl'] > 0])
        wr = (wins_count / len(trades)) * 100 if trades else 0
        print(f"   {hour:02d}h: {len(trades)} trades | WR: {wr:.0f}% | PnL: ${pnl:+,.2f}")
    
    # Durée moyenne des trades
    print(f"\n⏱️  DURÉE DES TRADES")
    durations = []
    for t in closed:
        try:
            entry = datetime.fromisoformat(t['entry_time'])
            exit_time = datetime.fromisoformat(t['exit_time'])
            duration = (exit_time - entry).total_seconds() / 3600  # en heures
            durations.append(duration)
        except:
            pass
    
    if durations:
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        print(f"   Durée moyenne: {avg_duration:.1f} heures")
        print(f"   Min: {min_duration:.1f}h | Max: {max_duration:.1f}h")
    
    # Recommandations
    print(f"\n" + "=" * 70)
    print("💡 RECOMMANDATIONS D'OPTIMISATION")
    print("=" * 70)
    
    recommendations = []
    
    if win_rate < 50:
        recommendations.append("⚠️  Win rate < 50% - Resserrer les filtres d'entrée")
    if win_rate > 70:
        recommendations.append("✅ Win rate excellent - Considérer augmenter taille positions")
    
    if profit_factor < 1:
        recommendations.append("⚠️  Profit Factor < 1 - Bot perdant, revoir stratégie")
    elif profit_factor < 1.5:
        recommendations.append("⚠️  Profit Factor faible - Améliorer ratio risk/reward")
    else:
        recommendations.append("✅ Profit Factor OK")
    
    if avg_loss and abs(avg_loss) > avg_win * 1.5:
        recommendations.append("⚠️  Pertes trop grandes vs gains - Resserrer stop-loss")
    
    # Recommandations par heure
    if by_hour:
        worst_hour = min(by_hour.items(), key=lambda x: sum(t['pnl'] for t in x[1]))
        if sum(t['pnl'] for t in worst_hour[1]) < 0:
            recommendations.append(f"⚠️  Éviter trades à {worst_hour[0]:02d}h (perdant)")
    
    # Tickers à blacklister
    for stat in ticker_stats[-3:]:
        if stat['pnl'] < -100 and stat['win_rate'] < 40:
            recommendations.append(f"⚠️  Considérer blacklister {stat['ticker']} (perdant)")
    
    for rec in recommendations:
        print(f"   {rec}")
    
    print("\n" + "=" * 70)


def analyze_logs():
    """Analyse les logs de trades"""
    print("\n" + "=" * 70)
    print("📜 ANALYSE DES LOGS")
    print("=" * 70)
    
    try:
        with open(TRADES_LOG, 'r') as f:
            lines = f.readlines()
        
        print(f"\n   Total lignes: {len(lines)}")
        
        buys = [l for l in lines if 'BUY' in l]
        sells = [l for l in lines if 'SELL' in l or 'TAKE_PROFIT' in l or 'STOP_LOSS' in l]
        
        print(f"   Achats: {len(buys)}")
        print(f"   Ventes: {len(sells)}")
        
        # Dernières opérations
        print(f"\n   📋 Dernières opérations:")
        for line in lines[-10:]:
            print(f"   {line.strip()}")
            
    except FileNotFoundError:
        print("   ❌ Fichier trades.log non trouvé")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")


if __name__ == '__main__':
    analyze_trades()
    analyze_logs()

