"""
Service Desk Assistant - главный файл бота
Интеграция: MAX Messenger + Yandex AI Studio + Supabase
"""
import asyncio
import aiohttp
from config import MAX_BOT_TOKEN, MAX_API_URL, validate_config
from handlers.message_handler import MessageHandler
from utils.logger import logger
from utils.file_handler import cleanup_temp_files


class ServiceDeskBot:
    """Главный класс бота"""

    def __init__(self):
        self.token = MAX_BOT_TOKEN
        self.api_url = MAX_API_URL
        self.handler = MessageHandler()
        self.offset = 0
        logger.info("ServiceDeskBot инициализирован")

    async def send_message(self, chat_id: str, text: str, voice_path: str = None):
        """
        Отправка сообщения пользователю

        Args:
            chat_id: ID чата
            text: Текст сообщения
            voice_path: Путь к голосовому файлу (опционально)
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "chat_id": chat_id,
            "text": text,
            "format": "markdown"
        }

        async with aiohttp.ClientSession() as session:
            # Отправка текста
            try:
                async with session.post(
                    f"{self.api_url}/messages",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Ошибка отправки сообщения: {resp.status}")
                    else:
                        logger.debug(f"Сообщение отправлено в чат {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения: {e}")

            # Отправка голосового сообщения
            if voice_path:
                try:
                    with open(voice_path, "rb") as f:
                        form = aiohttp.FormData()
                        form.add_field("chat_id", chat_id)
                        form.add_field("file", f, filename="voice.ogg")

                        async with session.post(
                            f"{self.api_url}/messages",
                            headers={"Authorization": f"Bearer {self.token}"},
                            data=form
                        ) as voice_resp:
                            if voice_resp.status != 200:
                                logger.error(f"Ошибка отправки голоса: {voice_resp.status}")
                            else:
                                logger.debug(f"Голосовое сообщение отправлено в чат {chat_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки голосового файла: {e}")

    async def setup_webhook(self, webhook_url: str):
        """Настройка webhook в MAX API"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": webhook_url
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_url}/webhook",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Webhook настроен: {webhook_url}")
                    else:
                        error_text = await resp.text()
                        logger.error(f"Ошибка настройки webhook: {resp.status} - {error_text}")
            except Exception as e:
                logger.error(f"Ошибка при настройке webhook: {e}")

    async def get_updates(self):
        """Long Polling для получения обновлений от MAX"""
        headers = {"Authorization": f"Bearer {self.token}"}

        logger.info("🤖 Бот запущен и ожидает сообщения...")

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.api_url}/updates",
                        headers=headers,
                        params={"offset": self.offset, "timeout": 30}
                    ) as resp:
                        if resp.status != 200:
                            logger.error(f"Ошибка получения обновлений: {resp.status}")
                            await asyncio.sleep(5)
                            continue

                        updates = await resp.json()

                        for update in updates.get("updates", []):
                            try:
                                # Обработка сообщения
                                response = await self.handler.handle_update(update)

                                if response:
                                    await self.send_message(
                                        chat_id=response["chat_id"],
                                        text=response["text"],
                                        voice_path=response.get("voice_path")
                                    )

                                # Обновляем offset
                                self.offset = update["update_id"] + 1

                            except Exception as e:
                                logger.error(f"Ошибка обработки обновления: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"Ошибка в цикле обновлений: {e}", exc_info=True)
                await asyncio.sleep(5)

            await asyncio.sleep(0.5)


async def main():
    """Точка входа"""
    from config import WEBHOOK_URL
    
    # Валидация конфигурации
    validate_config()
    logger.info("Конфигурация проверена")
    
    # Очистка временных файлов при запуске
    cleanup_temp_files()
    logger.info("Временные файлы очищены")
    
    bot = ServiceDeskBot()
    
    if WEBHOOK_URL:
        # Режим webhook
        logger.info(f"🌐 Запуск в режиме webhook: {WEBHOOK_URL}")
        await bot.setup_webhook(WEBHOOK_URL)
        
        # Запуск webhook сервера
        from webhook_server import WebhookServer
        server = WebhookServer()
        await server.run_async(host='0.0.0.0', port=8080)
    else:
        # Режим long polling
        logger.info("🤖 Бот запущен и ожидает сообщения...")
        try:
            await bot.get_updates()
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        finally:
            cleanup_temp_files()
            logger.info("Временные файлы очищены при завершении")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
