from telethon.sync import TelegramClient
from telethon import events
import pandas as pd
import json
import os
import asyncio
from datetime import datetime, timedelta

# --- CREDENCIAIS TELEGRAM ---
api_id = 22321477
api_hash = 'c882e1999c5422c0c2eb93da72f5fa83'
session_name = 'data/sessao_flavio'


# --- CONFIGURAÇÃO DE GRUPOS ---
grupo_origem_id = -1001941369397
grupo_destino_id = -1002842676004  # ou None se não quiser encaminhar

# --- HISTÓRICO ---
csv_path = 'historico.csv'
json_path = 'historico.json'

client = TelegramClient(session_name, api_id, api_hash)

def salvar_csv_json(messages):
    df = pd.DataFrame(messages)
    df.to_csv(csv_path, index=False)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

async def buscar_mensagens_anteriores():
    print("🔁 Buscando mensagens dos últimos 30 dias...")
    mensagens = []
    async for msg in client.iter_messages(grupo_origem_id, limit=None, offset_date=datetime.now() - timedelta(days=30)):
        if msg.message:
            mensagens.append({
                'data': msg.date.strftime('%Y-%m-%d %H:%M:%S'),
                'texto': msg.message
            })

    if mensagens:
        salvar_csv_json(mensagens)
        print(f"💾 {len(mensagens)} mensagens salvas.")
    else:
        print("⚠️ Nenhuma mensagem recente encontrada.")

@client.on(events.NewMessage(chats=grupo_origem_id))
async def ao_vivo(event):
    if event.message.message:
        nova_linha = {
            'data': event.message.date.strftime('%Y-%m-%d %H:%M:%S'),
            'texto': event.message.message
        }

        # CSV
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            df = pd.DataFrame([nova_linha])
        df.to_csv(csv_path, index=False)

        # JSON
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                historico = json.load(f)
        else:
            historico = []
        historico.append(nova_linha)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)

        # Enviar para destino (opcional)
        if grupo_destino_id:
            try:
                await client.send_message(grupo_destino_id, event.message)
                print("📤 Mensagem encaminhada.")
            except Exception as e:
                print(f"❌ Erro ao encaminhar: {e}")

        print(f"📥 Nova mensagem salva: {nova_linha['data']}")

async def agendador():
    while True:
        await buscar_mensagens_anteriores()
        await asyncio.sleep(1800)  # 30 minutos

async def main():
    await buscar_mensagens_anteriores()
    asyncio.create_task(agendador())
    print("📡 Bot rodando... aguardando mensagens.")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
