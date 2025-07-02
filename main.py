from telethon.sync import TelegramClient
from telethon import events
from telethon.tl.types import PeerChannel
import pandas as pd
import json
import os
import asyncio
from datetime import datetime, timedelta

# --- SUAS CREDENCIAIS TELEGRAM ---
api_id = 22321477
api_hash = 'c882e1999c5422c0c2eb93da72f5fa83'
session_name = 'sessao_flavio'

# --- CONFIG GRUPOS ---
grupo_origem_id = -1001941369397
grupo_destino_id = -1002842676004  # ou None, se não quiser encaminhar

# --- ARQUIVOS DE HISTÓRICO ---
csv_path = 'historico.csv'
json_path = 'historico.json'

# --- CLIENT TELEGRAM ---
client = TelegramClient(session_name, api_id, api_hash)

async def buscar_mensagens_anteriores():
    print("🔄 Buscando mensagens dos últimos 30 dias...")
    messages = []
    async for msg in client.iter_messages(grupo_origem_id, limit=None, offset_date=datetime.now() - timedelta(days=30)):
        if msg.message:
            messages.append({
                'data': msg.date.strftime('%Y-%m-%d %H:%M:%S'),
                'texto': msg.message
            })
    if messages:
        df = pd.DataFrame(messages)
        df.to_csv(csv_path, index=False)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(messages)} mensagens salvas em '{csv_path}' e '{json_path}'")
    else:
        print("⚠️ Nenhuma mensagem encontrada nos últimos 30 dias.")

@client.on(events.NewMessage(chats=grupo_origem_id))
async def copiar_em_tempo_real(event):
    if event.message.message:
        linha = {
            'data': event.message.date.strftime('%Y-%m-%d %H:%M:%S'),
            'texto': event.message.message
        }
        # Atualiza CSV
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([linha])], ignore_index=True)
        else:
            df = pd.DataFrame([linha])
        df.to_csv(csv_path, index=False)

        # Atualiza JSON
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                historico = json.load(f)
        else:
            historico = []
        historico.append(linha)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)

        # Encaminha (opcional)
        if grupo_destino_id:
            try:
                await client.send_message(grupo_destino_id, event.message)
                print("📤 Mensagem encaminhada.")
            except Exception as e:
                print(f"[❌] Falha ao enviar para grupo de destino: {e}")

        print(f"💾 Mensagem salva: {linha['data']}")

async def main():
    await buscar_mensagens_anteriores()
    print("📡 Monitorando grupo em tempo real...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
