"""
Test des connexions API : IBKR, Benzinga, Telegram
"""
import asyncio
import sys
from datetime import datetime
from ib_insync import IB, util
import requests
from telegram import Bot

# Import config
try:
    from config import (
        IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID,
        BENZINGA_API_KEY,
        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    )
except ImportError:
    print("❌ Erreur: Fichier config.py non trouvé ou erreur d'import")
    sys.exit(1)


def test_ibkr():
    """Test connexion Interactive Brokers"""
    print("\n" + "="*60)
    print("🔌 TEST CONNEXION IBKR")
    print("="*60)
    
    try:
        ib = IB()
        print(f"📡 Tentative connexion {IBKR_HOST}:{IBKR_PORT}...")
        
        ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, timeout=10)
        
        print(f"✅ Connexion réussie à IBKR!")
        print(f"   - Host: {IBKR_HOST}")
        print(f"   - Port: {IBKR_PORT} ({'Paper Trading' if IBKR_PORT == 7497 else 'Live Trading'})")
        print(f"   - Client ID: {IBKR_CLIENT_ID}")
        
        # Test récupération compte
        accounts = ib.managedAccounts()
        if accounts:
            print(f"   - Comptes: {', '.join(accounts)}")
        
        # Test récupération prix
        print("\n📊 Test récupération données SPY...")
        spy = ib.qualifyContracts(util.Stock('SPY', 'SMART', 'USD'))[0]
        ticker = ib.reqMktData(spy)
        ib.sleep(2)
        
        if ticker.last and ticker.last > 0:
            print(f"   - SPY Prix: ${ticker.last:.2f}")
            print(f"   - Bid: ${ticker.bid:.2f} | Ask: ${ticker.ask:.2f}")
            print(f"   - Volume: {ticker.volume:,}")
            print("✅ Récupération données OK")
        else:
            print("⚠️  Pas de données temps réel (market fermé ou delayed data)")
        
        ib.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Erreur connexion IBKR: {str(e)}")
        print("\n💡 Vérifications:")
        print("   1. TWS ou IB Gateway est lancé ?")
        print("   2. API activée dans TWS/Gateway ?")
        print(f"   3. Port {IBKR_PORT} est correct ?")
        print("   4. 'Read-Only API' désactivé ?")
        return False


def test_benzinga():
    """Test API Benzinga Pro"""
    print("\n" + "="*60)
    print("📰 TEST API BENZINGA")
    print("="*60)
    
    if not BENZINGA_API_KEY:
        print("⚠️  Pas de clé API Benzinga dans .env")
        print("💡 Ajouter: BENZINGA_API_KEY=votre_cle")
        return False
    
    try:
        # Test endpoint calendar (earnings)
        url = "https://api.benzinga.com/api/v2.1/calendar/earnings"
        params = {
            'token': BENZINGA_API_KEY,
            'parameters[date_from]': datetime.now().strftime('%Y-%m-%d'),
            'parameters[date_to]': datetime.now().strftime('%Y-%m-%d')
        }
        
        print(f"📡 Test récupération earnings du jour...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            earnings = data.get('earnings', [])
            
            print(f"✅ Connexion Benzinga réussie!")
            print(f"   - Earnings aujourd'hui: {len(earnings)}")
            
            if earnings:
                print(f"\n   Exemples (3 premiers):")
                for earning in earnings[:3]:
                    ticker = earning.get('ticker', 'N/A')
                    time = earning.get('time', 'N/A')
                    print(f"   - {ticker}: {time}")
            
            return True
        else:
            print(f"❌ Erreur API Benzinga: Status {response.status_code}")
            print(f"   Réponse: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur Benzinga: {str(e)}")
        print("\n💡 Vérifications:")
        print("   1. Clé API valide ?")
        print("   2. Abonnement actif ?")
        print("   3. Connexion internet OK ?")
        return False


async def test_telegram():
    """Test Telegram Bot"""
    print("\n" + "="*60)
    print("📱 TEST TELEGRAM BOT")
    print("="*60)
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Token ou Chat ID manquant dans .env")
        print("💡 Ajouter:")
        print("   TELEGRAM_BOT_TOKEN=votre_token")
        print("   TELEGRAM_CHAT_ID=votre_chat_id")
        return False
    
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Test bot info
        print(f"📡 Test connexion bot...")
        bot_info = await bot.get_me()
        print(f"✅ Bot connecté!")
        print(f"   - Nom: {bot_info.first_name}")
        print(f"   - Username: @{bot_info.username}")
        print(f"   - ID: {bot_info.id}")
        
        # Test envoi message
        print(f"\n📨 Envoi message test...")
        message = (
            "🤖 **Test Connexion Bot**\n\n"
            "✅ Bot Actions Momentum configuré\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Prêt à recevoir les alertes de trading!"
        )
        
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        
        print(f"✅ Message envoyé avec succès!")
        print(f"   - Chat ID: {TELEGRAM_CHAT_ID}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur Telegram: {str(e)}")
        print("\n💡 Vérifications:")
        print("   1. Token bot valide ?")
        print("   2. Chat ID correct ?")
        print("   3. Bot ajouté au chat/groupe ?")
        print("   4. Bot a permissions d'écrire ?")
        return False


def main():
    """Tests séquentiels"""
    print("\n" + "🚀 "* 20)
    print("🤖 TEST CONNEXIONS - BOT ACTIONS MOMENTUM")
    print("🚀 " * 20)
    
    results = {
        'IBKR': False,
        'Benzinga': False,
        'Telegram': False
    }
    
    # Test IBKR
    results['IBKR'] = test_ibkr()
    
    # Test Benzinga
    results['Benzinga'] = test_benzinga()
    
    # Test Telegram (async)
    results['Telegram'] = asyncio.run(test_telegram())
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    for service, success in results.items():
        status = "✅ OK" if success else "❌ ÉCHEC"
        print(f"{service:.<40} {status}")
    
    all_success = all(results.values())
    
    print("\n" + "="*60)
    if all_success:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ Le bot est prêt à être configuré")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("💡 Vérifiez la configuration et réessayez")
    print("="*60 + "\n")
    
    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(main())

