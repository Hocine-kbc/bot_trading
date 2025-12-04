"""
Script pour obtenir facilement le CHAT_ID Telegram
"""
import os
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
import requests

# Charger .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN non trouvé dans .env")
    sys.exit(1)

print("🔍 Recherche de votre CHAT_ID...\n")
print("📱 Assurez-vous d'avoir envoyé un message à votre bot (@momentum_tradingtest_bot)\n")

try:
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    response = requests.get(url)
    data = response.json()
    
    if not data.get('ok'):
        print(f"❌ Erreur API: {data.get('description', 'Inconnue')}")
        sys.exit(1)
    
    results = data.get('result', [])
    
    if not results:
        print("❌ Aucun message trouvé!")
        print("\n💡 Actions à faire:")
        print("   1. Ouvrez Telegram")
        print("   2. Cherchez: @momentum_tradingtest_bot")
        print("   3. Envoyez-lui un message (ex: /start)")
        print("   4. Relancez ce script")
        sys.exit(1)
    
    print("✅ Messages trouvés!\n")
    print("=" * 60)
    
    chat_ids = set()
    for update in results:
        if 'message' in update:
            msg = update['message']
            chat = msg.get('chat', {})
            chat_id = chat.get('id')
            chat_type = chat.get('type')
            
            if chat_id:
                chat_ids.add(chat_id)
                
                print(f"\n📨 Message de:")
                if 'username' in chat:
                    print(f"   Username: @{chat.get('username')}")
                if 'first_name' in chat:
                    print(f"   Nom: {chat.get('first_name')} {chat.get('last_name', '')}")
                print(f"   Type: {chat_type}")
                print(f"   🎯 CHAT_ID: {chat_id}")
    
    print("\n" + "=" * 60)
    
    if chat_ids:
        print(f"\n✅ Votre CHAT_ID est: {list(chat_ids)[0]}")
        print(f"\n📝 Ajoutez cette ligne dans votre fichier .env:")
        print(f"\nTELEGRAM_CHAT_ID={list(chat_ids)[0]}\n")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)

