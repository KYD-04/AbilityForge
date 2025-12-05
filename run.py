#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор Способностей Персонажей
Основной файл запуска системы

Автор: MiniMax Agent
Дата создания: 2025-12-04
"""

import os
import sys
import subprocess
import webbrowser
import time
import logging
from pathlib import Path

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Настройка системы логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ability_generator.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_dependencies():
    """Проверка зависимостей"""
    logger = logging.getLogger(__name__)
    
    try:
        import flask
        import requests
        import numpy
        logger.info("Все Python зависимости установлены")
        return True
    except ImportError as e:
        logger.error(f"✗ Отсутствуют зависимости: {e}")
        logger.info("Устанавливаю зависимости...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            logger.info("Зависимости успешно установлены")
            return True
        except subprocess.CalledProcessError:
            logger.error("✗ Не удалось установить зависимости")
            return False

def check_ollama_connection(host="localhost", port=57002):
    """Проверка доступности Ollama"""
    logger = logging.getLogger(__name__)
    
    try:
        import requests
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            logger.info(f"Ollama доступен на {host}:{port}")
            logger.info(f"Доступные модели: {[model['name'] for model in models.get('models', [])]}")
            return True
        else:
            logger.warning(f"⚠ Ollama ответил с кодом {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.warning("⚠ Ollama не запущен или недоступен")
        logger.info("Инструкции по запуску Ollama:")
        logger.info("1. Убедитесь, что Docker установлен")
        logger.info("2. Выполните: sudo docker run -d --gpus=all -v ollama:/root/.ollama -p 57002:11434 --name ollama ollama/ollama")
        logger.info("3. Проверьте доступность: http://localhost:57002")
        return False
    except Exception as e:
        logger.warning(f"⚠ Ошибка при проверке Ollama: {e}")
        return False

def create_directories():
    """Создание необходимых директорий"""
    logger = logging.getLogger(__name__)
    
    directories = [
        'templates',
        'static/css',
        'static/js',
        'static/images',
        'logs',
        'saved_projects'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Директория {directory} готова")

def open_browser(url, delay=2):
    """Открытие браузера с задержкой"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"Открываю браузер: {url}")
    except Exception as e:
        print(f"⚠ Не удалось автоматически открыть браузер: {e}")
        print(f"Откройте вручную: {url}")

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("ГЕНЕРАТОР СПОСОБНОСТЕЙ ПЕРСОНАЖЕЙ")
    print("=" * 60)
    print("Автор: MiniMax Agent")
    print("Дата: 2025-12-04")
    print("=" * 60)
    
    logger = setup_logging()
    
    # Проверка зависимостей
    print("\nПроверка зависимостей...")
    if not check_dependencies():
        print("Не удалось установить зависимости. Завершение работы.")
        sys.exit(1)
    
    # Создание директорий
    print("\nПодготовка директорий...")
    create_directories()
    
    # Проверка Ollama
    print("\nПроверка Ollama...")
    ollama_available = check_ollama_connection()
    
    if not ollama_available:
        print("\nВНИМАНИЕ: Ollama недоступен!")
        print("Система будет работать в ограниченном режиме без ИИ-генерации.")
        print("Для полной функциональности:")
        print("1. Установите Docker")
        print("2. Запустите: sudo docker run -d --gpus=all -v ollama:/root/.ollama -p 57002:11434 --name ollama ollama/ollama")
        print("3. Установите модель: docker exec ollama ollama pull llama3.1:latest")
        print("\nПродолжить запуск? (y/N): ", end="")
        
        response = input().lower().strip()
        if response not in ['y', 'yes', 'да', 'д']:
            print("Запуск отменен пользователем.")
            sys.exit(0)
    
    # Запуск веб-сервера
    print("\nЗапуск веб-сервера...")
    
    try:
        from app import app
        print("Flask приложение загружено")
        
        # Определяем URL для открытия
        url = "http://localhost:5000"
        
        print(f"\nСистема запущена!")
        print(f"Откройте в браузере: {url}")
        print(f"Для остановки нажмите Ctrl+C")
        print("=" * 60)
        
        # Запуск приложения
        app.run(debug=False, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n\nЗавершение работы по запросу пользователя...")
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        print(f"\nОшибка при запуске: {e}")
        sys.exit(1)
    finally:
        print("\nСпасибо за использование Генератора Способностей Персонажей!")

if __name__ == "__main__":
    main()