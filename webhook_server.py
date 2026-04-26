"""
Webhook сервер для получения сообщений от MAX Messenger
"""
import asyncio
from aiohttp import web
from handlers.message_handler import MessageHandler
from utils.logger import logger
from config import MAX_BOT_TOKEN
import json


class WebhookServer:
    """Webhook сервер для MAX Messenger"""

    def __init__(self):
        self.handler = MessageHandler()
        self.app = web.Application()
        self.app.router.add_post('/webhook', self.handle_webhook)
        logger.info("WebhookServer инициализирован")

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Обработка входящего webhook от MAX"""
        try:
            # Проверка авторизации
            auth_header = request.headers.get('Authorization', '')
            if auth_header != f"Bearer {MAX_BOT_TOKEN}":
                logger.warning("Неверная авторизация webhook")
                return web.Response(status=401, text="Unauthorized")

            # Получение данных
            data = await request.json()
            logger.debug(f"Получен webhook: {json.dumps(data, ensure_ascii=False)[:200]}")

            # Обработка сообщения
            response = await self.handler.handle_update(data)

            if response:
                # Отправка ответа через MAX API
                await self.send_response(response)

            return web.Response(status=200, text="OK")

        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    async def send_response(self, response: dict):
        """Отправка ответа пользователю через MAX API"""
        import aiohttp
        from config import MAX_API_URL

        headers = {
            "Authorization": f"Bearer {MAX_BOT_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "chat_id": response["chat_id"],
            "text": response["text"],
            "format": "markdown"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{MAX_API_URL}/messages",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.debug(f"Ответ отправлен в чат {response['chat_id']}")
                    else:
                        logger.error(f"Ошибка отправки ответа: {resp.status}")
            except Exception as e:
                logger.error(f"Ошибка при отправке ответа: {e}")

    async def run_async(self, host='0.0.0.0', port=8080):
        """Асинхронный запуск webhook сервера"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"🌐 Webhook сервер запущен на http://{host}:{port}/webhook")
        
        # Бесконечный цикл для поддержания работы
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            await runner.cleanup()


if __name__ == "__main__":
    server = WebhookServer()
    asyncio.run(server.run_async())
