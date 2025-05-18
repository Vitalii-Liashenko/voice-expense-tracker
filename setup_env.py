"""
Скрипт для перевірки та встановлення залежностей.
"""
import subprocess
import sys
import os

def install_requirements():
    """Встановлює необхідні залежності."""
    print("Встановлення необхідних пакетів...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Пакети успішно встановлено.")
    except subprocess.CalledProcessError:
        print("Помилка встановлення пакетів.")
        sys.exit(1)

if __name__ == "__main__":
    install_requirements()
