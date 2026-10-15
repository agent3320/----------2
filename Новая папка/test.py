from telethon import TelegramClient, events, connection
from gigachat import GigaChat
import asyncio
import logging

# === Отключаем лишние логи Telethon ===
logging.basicConfig(
    format='[%(levelname)s %(asctime)s] %(name)s: %(message)s',
    level=logging.WARNING
)

# ============================================================
# НАСТРОЙКИ
# ============================================================

# Telegram
API_ID = 34361981
API_HASH = "bfdc8eb1aecc971c07910164e57c8306"

PROXY_SECRET = "c2b06d1d5f08a1ec44f2377dbc736e46"
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1443

TARGET_USERNAME = "nastasyawe"  # без @

# GigaChat
GIGACHAT_KEY = "MDFhMTM5ZDUtZWY3Zi03ODk0LWJmOTgtZmNhNjFkNmQ1MDdlOmE2OGUxMGNiLWUwNWQtNGJiMS1hZDAzLTI4MGI5NGZhZWFhNQ=="
GIGACHAT_CERT = r"C:\Users\PC\Desktop\портфолио\Новая папка\russian_trusted_root_ca_pem.crt"

# ============================================================
# ОЗВУЧКА (ВЫКЛЮЧЕНА)
# ============================================================

# from venSpeakerPy import lib_speak
# import sounddevice as sd
# import numpy as np
#
# _speaker = lib_speak.Speaker(
#     model_id="ru_v3", language="ru", speaker="baya", device="cpu"
# )
#
# def say(text):
#     chunks = []
#     for chunk, _ in _speaker.speak(text=text, sample_rate=48000, speed=1.0):
#         chunks.append(np.frombuffer(chunk, dtype=np.float32))
#     if chunks:
#         audio = np.concatenate(chunks)
#         sd.play(audio, samplerate=48000)
#         sd.wait()

def say(text):
    """Заглушка — озвучка отключена."""
    print(f"🔇 [озвучка выключена]: {text}")

# ============================================================
# GIGACHAT
# ============================================================

giga = GigaChat(
    base_url="https://api.giga.chat/v1",
    credentials=GIGACHAT_KEY,
    scope="GIGACHAT_API_PERS",
    ca_bundle_file=GIGACHAT_CERT,
    model="GigaChat-2",
    verify_ssl_certs=False,  # на всякий случай, если сертификат не подхватится
)

def ask_gigachat(prompt: str) -> str:
    """Отправляет запрос в GigaChat и возвращает ответ."""
    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content
    except Exception as e:
        return f"[GigaChat error] {e}"

# ============================================================
# TELEGRAM КЛИЕНТ
# ============================================================

client = TelegramClient(
    "session_listener",
    API_ID,
    API_HASH,
    connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
    proxy=(PROXY_HOST, PROXY_PORT, PROXY_SECRET),
)

# ============================================================
# ОБРАБОТЧИК СООБЩЕНИЙ
# ============================================================

@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()

    if not sender or not getattr(sender, "username", None):
        return

    if sender.username.lower() != TARGET_USERNAME.lower():
        return

    text = event.raw_text
    print(f"\n📩 @{sender.username}: {text}")

    # Запрос к GigaChat
    answer = ask_gigachat(text)
    print(f"🤖 GigaChat: {answer}")

    # Озвучка (отключена — просто заглушка)
    # say(answer)

    # Отправляем ответ обратно в чат (раскомментируй, если нужно)
    # await event.reply(answer)

# ============================================================
# ЗАПУСК
# ============================================================

async def main():
    print("🔌 Подключаюсь к Telegram...")
    await client.start()

    me = await client.get_me()
    print(f"✅ Подключено как: {me.first_name} (@{me.username})")
    print(f"🎧 Слушаю сообщения от @{TARGET_USERNAME}...")
    print("Нажми Ctrl+C для выхода.\n")

    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановлено")