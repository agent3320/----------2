import os
import subprocess
import time
import urllib.request
import sys

# ============================================================
# НАСТРОЙКИ — ИСПРАВЛЕНО ПОД ТВОИ ПУТИ
# ============================================================

TOR_EXE = r"C:\Tor\tor\tor.exe"
TOR_DIR = r"C:\Tor\tor"
TORRC = r"C:\Tor\tor\torrc"
LYREBIRD = r"C:\Tor\tor\pluggable_transports\lyrebird.exe"
BRIDGES_FILE = r"C:\Tor\tor\bridges.txt"

# Источники мостов (пробуем по очереди)
BRIDGE_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/TOR-BRIDGES/TOR_BRIDGES_OBFS4.txt",
    "https://gitlab.com/igareck/vpn-configs-for-russia/-/raw/main/TOR-BRIDGES/TOR_BRIDGES_OBFS4.txt",
    "https://gitea.com/igareck/vpn-configs-for-russia/raw/branch/main/TOR-BRIDGES/TOR_BRIDGES_OBFS4.txt",
]

BRIDGES_TO_USE = 3   # сколько мостов брать из списка

# ============================================================
# СКАЧИВАНИЕ МОСТОВ
# ============================================================

def download_bridges():
    """Скачивает свежий список мостов. Возвращает список строк."""
    for url in BRIDGE_URLS:
        try:
            print(f"📥 Пробую скачать мосты: {url[:60]}...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            bridges = [
                line.strip()
                for line in content.splitlines()
                if line.strip().startswith("obfs4 ")
            ]

            if bridges:
                print(f"✅ Скачано мостов: {len(bridges)}")
                with open(BRIDGES_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(bridges))
                return bridges

        except Exception as e:
            print(f"⚠️ Не удалось скачать с {url[:40]}: {type(e).__name__}")

    # Если ничего не скачалось — пробуем использовать старый файл
    if os.path.exists(BRIDGES_FILE):
        print("📂 Использую сохранённый bridges.txt")
        with open(BRIDGES_FILE, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip().startswith("obfs4 ")]

    return []

# ============================================================
# ГЕНЕРАЦИЯ TORRC
# ============================================================

def write_torrc(bridges):
    """Создаёт torrc с указанными мостами."""
    used = bridges[:BRIDGES_TO_USE]

    lines = [
        "UseBridges 1",
        f'ClientTransportPlugin obfs4 exec "{LYREBIRD}"',
    ]
    for b in used:
        lines.append(f"Bridge {b}")

    with open(TORRC, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ torrc обновлён ({len(used)} мостов)")
    for b in used:
        print(f"   🔗 {b[:60]}...")

# ============================================================
# ЗАПУСК TOR
# ============================================================

def start_tor():
    """Запускает tor.exe и ждёт Bootstrapped 100%."""
    print("\n🚀 Запускаю Tor...")

    proc = subprocess.Popen(
        [TOR_EXE, "-f", TORRC],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore",
        bufsize=1,
    )

    start_time = time.time()
    timeout = 120  # 2 минуты на подключение

    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            print("❌ Tor завершился неожиданно")
            return None

        if line:
            line = line.strip()
            if "Bootstrapped" in line:
                print(f"   {line}")
            if "Bootstrapped 100%" in line:
                print("\n✅ Tor подключён! SOCKS5: 127.0.0.1:9050")
                return proc

        if time.time() - start_time > timeout:
            print(f"\n❌ Tor не подключился за {timeout} сек")
            print("💡 Возможно, мосты заблокированы. Перезапусти скрипт —")
            print("   он скачает свежие мосты из репозитория igareck.")
            proc.terminate()
            return None

# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def main():
    # Проверка файлов
    if not os.path.exists(TOR_EXE):
        print(f"❌ Не найден tor.exe по пути: {TOR_EXE}")
        sys.exit(1)

    if not os.path.exists(LYREBIRD):
        print(f"❌ Не найден lyrebird.exe по пути: {LYREBIRD}")
        sys.exit(1)

    # 1. Скачиваем свежие мосты
    bridges = download_bridges()
    if not bridges:
        print("❌ Не удалось получить мосты")
        sys.exit(1)

    # 2. Генерируем torrc
    write_torrc(bridges)

    # 3. Запускаем Tor
    proc = start_tor()
    if not proc:
        sys.exit(1)

    # 4. Держим Tor запущенным
    print("\n" + "=" * 50)
    print("✅ Tor работает. Не закрывай это окно.")
    print("Во втором окне запусти autoconnect.py")
    print("=" * 50)
    input("\nНажми Enter для остановки Tor...\n")
    proc.terminate()
    print("🛑 Tor остановлен")


if __name__ == "__main__":
    main()