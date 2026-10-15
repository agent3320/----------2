import json
import queue
import sys
import os
import time
import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from gigachat import GigaChat
from venSpeakerPy import lib_speak

# ============================================================
# 1. НАСТРОЙКИ
# ============================================================

VOSK_MODEL_PATH = r"C:\vosk_model"
CERT_PATH = r"C:\Users\PC\Desktop\портфолио\Новая папка\russian_trusted_root_ca_pem.crt"
AUTH_KEY = "MDFhMTM5ZDUtZWY3Zi03ODk0LWJmOTgtZmNhNjFkNmQ1MDdlOmE2OGUxMGNiLWUwNWQtNGJiMS1hZDAzLTI4MGI5NGZhZWFhNQ=="
VOICE = "baya"

# Флаг: сейчас говорит ассистент?
is_speaking = False

# ============================================================
# 2. ИНИЦИАЛИЗАЦИЯ
# ============================================================

print("⏳ Загружаю Vosk...")
vosk_model = Model(VOSK_MODEL_PATH)
rec = KaldiRecognizer(vosk_model, 16000)
q = queue.Queue()
print("✅ Vosk готов")

print("⏳ Подключаюсь к GigaChat...")
giga = GigaChat(
    base_url="https://api.giga.chat/v1",
    credentials=AUTH_KEY,
    scope="GIGACHAT_API_PERS",
    ca_bundle_file=CERT_PATH,
    model="GigaChat-2",
)
print("✅ GigaChat готов")

print("⏳ Загружаю синтез речи...")
speaker = lib_speak.Speaker(
    model_id="ru_v3",
    language="ru",
    speaker=VOICE,
    device="cpu",
)
print("✅ Синтез речи готов")

# ============================================================
# 3. ФУНКЦИИ
# ============================================================

def clear_queue():
    """Очищает очередь от накопившегося аудио."""
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break


def say(text):
    """Озвучивает текст. На время речи микрофон игнорируется."""
    global is_speaking
    is_speaking = True
    try:
        chunks = []
        for chunk, _ in speaker.speak(text=text, sample_rate=48000, speed=1.0):
            chunks.append(np.frombuffer(chunk, dtype=np.float32))
        if chunks:
            audio = np.concatenate(chunks)
            sd.play(audio, samplerate=48000)
            sd.wait()
    except Exception as e:
        print(f"⚠️ Ошибка синтеза: {e}")
    finally:
        # Даём микрофону "успокоиться" и чистим очередь
        time.sleep(0.5)
        clear_queue()
        is_speaking = False


def ask_gigachat(prompt):
    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка GigaChat: {e}"


def callback(indata, frames, time_info, status):
    """Callback микрофона. Игнорируем звук, пока говорит ассистент."""
    if status:
        print(status, file=sys.stderr)
    if is_speaking:
        return  # пропускаем — это голос ассистента
    q.put(bytes(indata))


# ============================================================
# 4. ОСНОВНОЙ ЦИКЛ
# ============================================================

print("\n" + "=" * 50)
print("🎤 Голосовой ассистент запущен!")
print("Скажите 'выход' для завершения.")
print("=" * 50 + "\n")

say("Привет! Я готов к работе.")

with sd.RawInputStream(
    samplerate=16000,
    blocksize=8000,
    device=None,
    dtype="int16",
    channels=1,
    callback=callback,
):
    while True:
        data = q.get()

        # Пока ассистент говорит — не обрабатываем
        if is_speaking:
            continue

        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "").strip()

            if not text:
                continue

            print(f"👤 Вы: {text}")

            if any(word in text.lower() for word in ["выход", "стоп", "пока"]):
                say("До свидания!")
                print("👋 Завершение работы...")
                break

            print("🤔 Думаю...")
            answer = ask_gigachat(text)
            print(f"🤖 GigaChat: {answer}\n")

            say(answer)