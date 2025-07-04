from telethon.sync import TelegramClient

api_id = 22321477
api_hash = 'c882e1999c5422c0c2eb93da72f5fa83'
session_name = 'data/sessao_railway'  # novo caminho

with TelegramClient(session_name, api_id, api_hash) as client:
    print("✅ Sessão criada com sucesso!")
