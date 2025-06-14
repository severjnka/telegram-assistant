from telethon import TelegramClient, events
import asyncio

# Вставь свои значения
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
phone = 'YOUR_PHONE_NUMBER'  # например, +79991234567

# ID канала и чата для сбора информации
channel_id = -1001234567890  # ID канала, где вести беседу
feedback_chat_id = -1009876543210  # ID чата для сбора идей

# Промт для генерации ответов (можно интегрировать с OpenAI/GPT)
PROMPT = """
Ты — виртуальная помощница в Telegram-канале. Твоя задача — нативно поддерживать беседу, отвечать на вопросы участников, собирать интересные идеи, жалобы и предложения, а также фиксировать частые вопросы и проблемы пользователей. Все собранные данные ты структурируешь и отправляешь в отдельный чат для анализа и улучшения основного AI-бота.
"""

async def main():
    client = TelegramClient('assistant_session', api_id, api_hash)

    @client.on(events.NewMessage(chats=channel_id))
    async def handler(event):
        text = event.raw_text.lower()
        # Пример простой логики: если вопрос, ответить, иначе собрать инфу
        if '?' in text:
            reply = "Спасибо за вопрос! Сейчас уточню и вернусь с ответом."
            await event.reply(reply)
            # Отправить в чат для анализа
            await client.send_message(feedback_chat_id, f"Вопрос от пользователя: {event.raw_text}")
        elif any(word in text for word in ['идея', 'предложение', 'жаль', 'не работает']):
            await client.send_message(feedback_chat_id, f"Обратная связь: {event.raw_text}")

    await client.start(phone=phone)
    print("Помощница запущена!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())