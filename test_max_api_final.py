#!/usr/bin/env python3
"""Тест отправки сообщения через MAX API с query parameters"""
import asyncio
import aiohttp
import json

MAX_BOT_TOKEN = "f9LHodD0cOJ2ya7qvLeNRhPAEPEix0rYygO51QaYsuksrjgDMaQSjn7_md7whZck3shVUjtIVWQDKlwZI_-C"
MAX_API_URL = "https://platform-api.max.ru"

async def test_send_message():
    """Тест отправки сообщения с chat_id в query string"""
    headers = {
        "Authorization": MAX_BOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    # Тестируем с user_id отправителя
    params = {"user_id": "63137852"}
    payload = {"text": "Тестовое сообщение"}
    
    print(f"URL: {MAX_API_URL}/messages")
    print(f"Params: {params}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{MAX_API_URL}/messages",
                headers=headers,
                params=params,
                json=payload
            ) as resp:
                response_text = await resp.text()
                print(f"Status: {resp.status}")
                print(f"Response: {response_text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_send_message())
