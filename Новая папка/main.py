from gigachat import GigaChat
from venSpeakerPy import lib_speak
import sounddevice as sd
import numpy as np
import os

# === GigaChat ===
cert_path = r"C:\Users\PC\Desktop\портфолио\Новая папка\russian_trusted_root_ca_pem.crt"
AUTH_KEY = "MDFhMTM5ZDUtZWY3Zi03ODk0LWJmOTgtZmNhNjFkNmQ1MDdlOmE2OGUxMGNiLWUwNWQtNGJiMS1hZDAzLTI4MGI5NGZhZWFhNQ=="

giga = GigaChat(
    base_url="https://api.giga.chat/v1",
    credentials=AUTH_KEY,
    scope="GIGACHAT_API_PERS",
    ca_bundle_file=cert_path,
    model="GigaChat-2",
)

# === Синтез речи ===
speaker = lib_speak.Speaker(
    model_id="ru_v3", language="ru", speaker="baya", device="cpu"
)

def say(text):
    chunks = []
    for chunk, _ in speaker.speak(text=text, sample_rate=48000, speed=1.0):
        chunks.append(np.frombuffer(chunk, dtype=np.float32))
    audio = np.concatenate(chunks)
    sd.play(audio, samplerate=48000)
    sd.wait()

# === Диалог ===
print("🤖 GigaChat готов. Напишите 'выход' для завершения.\n")
while True:
    user_input = input("Вы: ")
    if user_input.lower() in ("выход", "exit", "quit"):
        break

    response = giga.chat(user_input)
    answer = response.choices[0].message.content
    print(f"🤖 GigaChat: {answer}\n")

    say(answer)  # озвучиваем ответ