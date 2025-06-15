# Telegram Assistant Svetlana

Виртуальная помощница для Telegram-канала на базе Telethon и YandexGPT.

## Возможности
- Автоматические ответы на вопросы участников (YandexGPT)
- Сбор идей, жалоб, предложений, частых вопросов
- Сохранение всех сообщений в базу данных SQLite
- Отправка обратной связи в отдельный чат для анализа
- Логирование в файл и консоль

## Структура проекта
- `assistant.py` — основной скрипт ассистента
- `db.py` — работа с базой данных SQLite
- `requirements.txt` — зависимости
- `README.md` — инструкция
- `tools/` — вспомогательные скрипты для анализа чатов (не обязательны для работы ассистента)
- `.env`, `key.json`, `*.session`, `assistant_data.db`, `assistant.log` — **НЕ публиковать!**

## Работа с базой данных
- Все идеи, жалобы, вопросы и обратная связь сохраняются в таблицу `messages` (файл `assistant_data.db`).
- Структура таблицы: id, type, user_id, username, text, date.

## Логирование
- Логи пишутся в файл `assistant.log` с ротацией (до 3 файлов по 1 МБ) и в консоль.

## Установка
1. Клонируйте репозиторий
2. Создайте и активируйте виртуальную среду:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # или
   source venv/bin/activate      # Linux/Mac
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Добавьте `.env` и `key.json` (см. пример ниже)

## Настройка .env
```
API_ID=ваш_api_id
API_HASH=ваш_api_hash
PHONE=ваш_номер_телефона
CHANNEL_ID=ваш_channel_id
FEEDBACK_CHAT_ID=ваш_feedback_chat_id
YANDEX_GPT_FOLDER_ID=ваш_folder_id
YANDEX_KEY_PATH=key.json
```

## Запуск
```bash
python assistant.py
```

## Запуск как сервис (systemd, Linux)
1. Создайте unit-файл `/etc/systemd/system/assistant.service`:
   ```
   [Unit]
   Description=Telegram Assistant Svetlana
   After=network.target

   [Service]
   Type=simple
   User=ваш_пользователь
   WorkingDirectory=/путь/к/проекту
   ExecStart=/путь/к/venv/bin/python assistant.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
2. Активируйте сервис:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable assistant
   sudo systemctl start assistant
   sudo systemctl status assistant
   ```

## Безопасность
- Не публикуйте `.env`, `key.json`, файлы сессий, базу данных и логи.
- Все секреты должны быть только на сервере.

## Примечания
- Скрипты для анализа чатов теперь в папке `tools/`.
- Для масштабирования можно перейти на PostgreSQL/MySQL.
- Для мониторинга используйте логи или внешние сервисы (опционально).

---
Если возникнут вопросы — пишите!