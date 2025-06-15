from telethon import TelegramClient, events
import asyncio
import os
import logging
import signal
import time
import requests
import jwt  # pyjwt
import json
from dotenv import load_dotenv
from db import init_db, save_message
from logging.handlers import RotatingFileHandler
from collections import defaultdict, deque
import pytz
from datetime import datetime, timedelta

# Настройка логирования (в файл и консоль с ротацией)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
log_file = "assistant.log"
file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

# Загрузка переменных из .env
load_dotenv()

# Получаем значения из .env
api_id = int(os.getenv("API_ID"))  # без кавычек, как число
api_hash = os.getenv("API_HASH")   # строка
phone = os.getenv("PHONE")         # строка
channel_id = int(os.getenv('CHANNEL_ID'))
feedback_chat_id = int(os.getenv('FEEDBACK_CHAT_ID'))
YANDEX_GPT_FOLDER_ID = os.getenv("YANDEX_GPT_FOLDER_ID")
YANDEX_KEY_PATH = os.getenv("YANDEX_KEY_PATH", "key.json")  # путь к key.json

# Память на весь чат
chat_history = deque(maxlen=100)
used_morning_messages = set()
used_jokes = set()

PROMPT = """
Ты — виртуальная помощница по имени Светлана в Telegram-канале. Твоя задача — нативно поддерживать беседу, отвечать на вопросы участников, собирать интересные идеи, жалобы и предложения, а также фиксировать частые вопросы и проблемы пользователей. Все собранные данные ты структурируешь и отправляешь в отдельный чат для анализа и улучшения основного AI-бота.
"""

def get_iam_token_from_key(key_path="key.json"):
    """Автоматическое получение IAM-токена по ключу сервисного аккаунта."""
    with open(key_path, "r") as f:
        key_data = json.load(f)
    now = int(time.time())
    payload = {
        "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        "iss": key_data["service_account_id"],
        "iat": now,
        "exp": now + 360  # JWT живёт 6 минут
    }
    encoded_jwt = jwt.encode(
        payload,
        key_data["private_key"],
        algorithm="PS256",
        headers={"kid": key_data["id"]}
    )
    response = requests.post(
        "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        json={"jwt": encoded_jwt}
    )
    response.raise_for_status()
    return response.json()["iamToken"]

def ask_yandex_gpt(prompt, folder_id, key_path="key.json", history=None):
    iam_token = get_iam_token_from_key(key_path)
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Bearer {iam_token}",
        "Content-Type": "application/json"
    }
    messages = [{"role": "system", "text": PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "text": prompt})
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 2000
        },
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    if response.status_code != 200:
        print("YandexGPT API error:", response.status_code, response.text)
    response.raise_for_status()
    result = response.json()
    return result["result"]["alternatives"][0]["message"]["text"]

async def send_morning_message(client):
    while True:
        moscow = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow)
        next_morning = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= next_morning:
            next_morning += timedelta(days=1)
        wait_seconds = (next_morning - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        # Генерируем пожелание и шутку через YandexGPT
        wish_prompt = (
            "Придумай оригинальное, позитивное пожелание доброго утра и хорошего настроения для коллег в рабочем чате. "
            "Не повторяйся, используй креативные формулировки."
        )
        joke_prompt = (
            "Придумай короткую, добрую и мотивирующую шутку для коллег, чтобы поднять рабочее настроение и стимулировать к действиям. "
            "Не повторяйся, избегай банальных шуток."
        )
        wish = ask_yandex_gpt(wish_prompt, YANDEX_GPT_FOLDER_ID, YANDEX_KEY_PATH)
        joke = ask_yandex_gpt(joke_prompt, YANDEX_GPT_FOLDER_ID, YANDEX_KEY_PATH)
        if wish in used_morning_messages or joke in used_jokes:
            continue
        used_morning_messages.add(wish)
        used_jokes.add(joke)
        message = f"{wish}\n\nШутка дня: {joke}"
        await client.send_message(channel_id, message)
        logging.info(f"Утреннее сообщение отправлено: {message}")

async def main():
    try:
        init_db()  # Инициализация базы данных
        client = TelegramClient('assistant_session', api_id, api_hash)
        shutdown_event = asyncio.Event()
        def handle_signal():
            logging.info("Получен сигнал завершения. Отключение...")
            shutdown_event.set()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, handle_signal)
            except NotImplementedError:
                pass
        # Запускаем задачу отправки утреннего сообщения
        asyncio.create_task(send_morning_message(client))
        @client.on(events.NewMessage(chats=channel_id))
        async def handler(event):
            text = event.raw_text.strip()
            user_id = event.sender_id
            username = (await event.get_sender()).username if await event.get_sender() else None
            try:
                msg_type = "other"
                if '?' in text:
                    msg_type = "question"
                elif any(word in text.lower() for word in ['идея', 'предложение']):
                    msg_type = "idea"
                elif any(word in text.lower() for word in ['жаль', 'не работает', 'ошибка', 'проблема']):
                    msg_type = "complaint"
                elif any(word in text.lower() for word in ['спасибо', 'отзыв', 'фидбек', 'feedback']):
                    msg_type = "feedback"
                save_message(msg_type, user_id, username, text)
                # История для всего чата
                history = list(chat_history)
                reply = ask_yandex_gpt(text, YANDEX_GPT_FOLDER_ID, YANDEX_KEY_PATH, history=history)
                chat_history.append({"role": "user", "text": text})
                chat_history.append({"role": "assistant", "text": reply})
                await event.reply(reply)
                await client.send_message(feedback_chat_id, f"[{msg_type}] от пользователя @{username or user_id}: {event.raw_text}")
                logging.info(f"[{msg_type}] Сохранено и отправлен ответ: {reply}")
            except Exception as e:
                logging.error(f"Ошибка при обработке сообщения: {e}")
        await client.start(phone=phone)
        logging.info("Помощница запущена!")
        await shutdown_event.wait()
        await client.disconnect()
        logging.info("Ассистент корректно завершил работу.")
    except Exception as e:
        logging.critical(f"Ошибка при запуске ассистента: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Критическая ошибка: {e}")