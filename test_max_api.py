#!/usr/bin/env python3
"""Тест отправки сообщения через MAX API"""
import asyncio
import aiohttp
import json

MAX_BOT_TOKEN = "f9LHodD0cOJ2ya7qvLeNRhPAEPEix0rYygO51QaYsuksrjgDMaQSjn7_md7whZck3shVUjtIVWQDKlwZI_-C"
MAX_API_URL = "https://platform-api.max.ru"

async def test_send_message():
    """Тест отправки сообщения"""
    headers = {
        "Authorization": MAX_BOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    # Тестируем разные варианты payload согласно официальной документации
    payloads = [
        {
            "user_id": 213686204,  # message.recipient.user_id из webhook
            "text": "Тестовое сообщение"
        },
        {
            "chat_id": 260046720,  # message.recipient.chat_id из webhook
            "text": "Тестовое сообщение"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, payload in enumerate(payloads):
            print(f"\n=== Тест {i+1} ===")
            print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            try:
                async with session.post(
                    f"{MAX_API_URL}/messages",
                    headers=headers,
                    json=payload
                ) as resp:
                    response_text = await resp.text()
                    print(f"Status: {resp.status}")
                    print(f"Response: {response_text}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_send_message())
