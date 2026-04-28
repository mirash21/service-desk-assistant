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
        self.app.router.add_get('/health', self.handle_health)
        self.start_time = asyncio.get_event_loop().time()
        logger.info("WebhookServer инициализирован")

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Обработка входящего webhook от MAX"""
        try:
            # MAX API не отправляет Authorization header, проверка отключена
            # auth_header = request.headers.get('Authorization', '')
            # logger.info(f"Получен webhook с Authorization: '{auth_header[:50] if auth_header else 'EMPTY'}...'")

            # Получение данных
            data = await request.json()
            logger.info(f"Получен webhook: {json.dumps(data, ensure_ascii=False)[:500]}")

            # Обработка сообщения
            response = await self.handler.handle_update(data)

            if response:
                # Отправка ответа через MAX API
                await self.send_response(response)

            return web.Response(status=200, text="OK")

        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint с детальной информацией"""
        import time
        from utils.temp_manager import get_dir_size_mb
        
        uptime = time.time() - self.start_time
        temp_size = get_dir_size_mb()
        
        health_data = {
            "status": "healthy",
            "uptime_seconds": round(uptime, 2),
            "temp_directory_size_mb": round(temp_size, 2),
            "timestamp": time.time()
        }
        
        return web.json_response(health_data)

    async def send_response(self, response: dict):
        """Отправка ответа пользователю через MAX API"""
        import aiohttp
        from config import MAX_API_URL

        headers = {
            "Authorization": MAX_BOT_TOKEN,
            "Content-Type": "application/json"
        }

        # MAX API требует user_id в query string
        params = {
            "user_id": str(response["chat_id"])
        }
        
        payload = {
            "text": response["text"]
        }

        async with aiohttp.ClientSession() as session:
            try:
                # Отправка текстового сообщения
                async with session.post(
                    f"{MAX_API_URL}/messages",
                    headers=headers,
                    params=params,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.debug(f"Текстовый ответ отправлен в чат {response['chat_id']}")
                    else:
                        error_text = await resp.text()
                        logger.error(f"Ошибка отправки текста: {resp.status} - {error_text}")
            except Exception as e:
                logger.error(f"Ошибка при отправке текста: {e}")

            # Отправка голосового сообщения (двухэтапный процесс)
            voice_path = response.get("voice_path")
            if voice_path:
                logger.info(f"Попытка отправки голоса: {voice_path}")
                try:
                    # Шаг 1: Получение upload_url и token
                    upload_url_init = f"{MAX_API_URL}/uploads"
                    logger.info(f"MAX upload init URL: {upload_url_init}?type=audio")
                    
                    async with session.post(
                        upload_url_init,
                        headers={"Authorization": MAX_BOT_TOKEN},
                        params={"type": "audio"}
                    ) as upload_init_resp:
                        if upload_init_resp.status != 200:
                            error_text = await upload_init_resp.text()
                            logger.error(f"Ошибка инициализации загрузки: {upload_init_resp.status} - {error_text}")
                            return
                        
                        upload_meta = await upload_init_resp.json()
                        logger.info(f"Upload metadata: {upload_meta}")
                        
                        # MAX возвращает 'url', а не 'upload_url'
                        upload_url = upload_meta.get("upload_url") or upload_meta.get("url")
                        file_token = upload_meta.get("token")
                        
                        if not upload_url or not file_token:
                            logger.error(f"Не удалось получить upload_url или token: {upload_meta}")
                            return
                        
                        logger.info(f"Загрузка файла по URL: {upload_url}")
                        
                        # Шаг 2: Загрузка файла по upload_url
                        with open(voice_path, "rb") as f:
                            upload_form = aiohttp.FormData()
                            upload_form.add_field("file", f, filename="audio.ogg", content_type="audio/ogg")
                            
                            async with session.post(
                                upload_url,
                                data=upload_form
                            ) as upload_resp:
                                if upload_resp.status != 200:
                                    error_text = await upload_resp.text()
                                    logger.error(f"Ошибка загрузки файла: {upload_resp.status} - {error_text}")
                                    return
                                
                                logger.info(f"Файл успешно загружен, token: {file_token}")
                                
                                # Шаг 3: Отправка сообщения с audio attachment (с ретраями)
                                message_payload = {
                                    "text": "Голосовой ответ",
                                    "attachments": [
                                        {
                                            "type": "audio",
                                            "payload": {
                                                "token": file_token
                                            }
                                        }
                                    ]
                                }
                                
                                # Ретраи с экспоненциальной задержкой
                                delay = 1.0  # начальная задержка 1 секунда
                                max_attempts = 5
                                
                                for attempt in range(1, max_attempts + 1):
                                    logger.info(f"Попытка отправки аудио-сообщения #{attempt}")
                                    import json
                                    logger.info(f"Payload JSON: {json.dumps(message_payload, ensure_ascii=False)}")
                                    logger.info(f"URL: {MAX_API_URL}/messages?user_id={response['chat_id']}")
                                    
                                    async with session.post(
                                        f"{MAX_API_URL}/messages",
                                        headers={
                                            "Authorization": MAX_BOT_TOKEN,
                                            "Content-Type": "application/json"
                                        },
                                        params={"user_id": str(response["chat_id"])},
                                        json=message_payload
                                    ) as msg_resp:
                                        if msg_resp.status == 200:
                                            logger.info(f"Голосовое сообщение отправлено в чат {response['chat_id']}")
                                            break
                                        else:
                                            error_text = await msg_resp.text()
                                            try:
                                                error_data = await msg_resp.json()
                                                error_code = error_data.get("code", "")
                                            except:
                                                error_code = ""
                                            
                                            if error_code == "attachment.not.ready":
                                                logger.warning(f"Вложение ещё не готово (попытка {attempt}/{max_attempts}), ждём {delay:.1f}с")
                                                await asyncio.sleep(delay)
                                                delay *= 2  # экспоненциальное увеличение
                                                continue
                                            else:
                                                logger.error(f"Ошибка отправки аудио-сообщения: {msg_resp.status} - {error_text}")
                                                logger.error(f"Payload: {message_payload}")
                                                break
                                else:
                                    logger.error(f"Не удалось отправить аудио после {max_attempts} попыток")
                except Exception as e:
                    logger.error(f"Ошибка отправки голосового файла: {e}", exc_info=True)

    async def run_async(self, host='0.0.0.0', port=8081):
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
