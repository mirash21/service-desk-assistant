"""
Основной обработчик сообщений от MAX
"""
import json
import os
from services.yandex_service import YandexAIService
from rag.supabase_manager import SupabaseRAGManager
from utils.prompt_builder import (
    build_analysis_prompt,
    build_user_reply_prompt,
    build_rag_prompt
)
from utils.file_handler import download_file
from utils.rate_limiter import RateLimiter
from utils.logger import logger
from config import MAX_BOT_TOKEN, MAX_API_URL, DATA_DIR, TEMP_DIR, MAX_FILE_SIZE


class MessageHandler:
    """Обработка входящих сообщений"""

    def __init__(self):
        self.yandex_ai = YandexAIService()
        self.rag_manager = SupabaseRAGManager()
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        logger.info("MessageHandler инициализирован")

    async def handle_update(self, update: dict) -> dict:
        """
        Обработка входящего обновления

        Args:
            update: Словарь с данными обновления от MAX

        Returns:
            Dict с ответом для пользователя
        """
        message = update.get("message", {})
        if not message:
            return None

        # MAX API использует другую структуру: recipient вместо chat, sender вместо from
        # Для отправки ответа используем user_id отправителя
        user_id = message.get("sender", {}).get("user_id") or message.get("from", {}).get("user_id")
        chat_id = user_id  # Используем user_id как chat_id для отправки ответа
        
        # Проверка rate limit
        if not self.rate_limiter.is_allowed(user_id):
            logger.warning(f"Rate limit для пользователя {user_id}")
            return {
                "chat_id": chat_id,
                "text": "⏳ Слишком много запросов. Подождите минуту и попробуйте снова."
            }

        # Обработка команд
        text = message.get("text") or message.get("body", {}).get("text", "")
        if text.startswith("/"):
            return await self._handle_command(message, chat_id, user_id)

        # Обработка контента
        return await self._handle_content(message, chat_id, user_id)

    async def _handle_command(self, message: dict, chat_id: str, user_id: str) -> dict:
        """Обработка команд бота"""
        text = message.get("text") or message.get("body", {}).get("text", "")
        parts = text.split(maxsplit=1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if command == "/start":
            return {
                "chat_id": chat_id,
                "text": "👋 Привет! Я ассистент сервис-деска.\n\n"
                        "Отправь мне описание проблемы текстом, голосом или фото.\n\n"
                        "Команды:\n"
                        "/mode [text|rag|voice] — переключить режим\n"
                        "/index — проиндексировать базу знаний\n"
                        "/stats — статистика базы знаний\n"
                        "/help — помощь"
            }

        elif command == "/mode":
            if args in ["text", "rag", "voice"]:
                success = self.rag_manager.set_user_mode(user_id, args)
                if success:
                    return {"chat_id": chat_id, "text": f"✓ Режим переключен на: **{args}**"}
                else:
                    return {"chat_id": chat_id, "text": "❌ Ошибка сохранения режима"}
            else:
                return {"chat_id": chat_id, "text": "Доступные режимы: text, rag, voice"}

        elif command == "/index":
            return await self._index_documents(chat_id)

        elif command == "/stats":
            stats = self.rag_manager.get_stats()
            return {
                "chat_id": chat_id,
                "text": f"📊 **Статистика базы знаний**\n\n"
                        f"Документов: {stats['total_docs']}\n"
                        f"Чанков: {stats['chunks']}"
            }

        elif command == "/help":
            return {
                "chat_id": chat_id,
                "text": "**Как пользоваться ботом:**\n\n"
                        "1. **Текстовый режим** (/mode text)\n"
                        "   Опишите проблему текстом\n\n"
                        "2. **RAG режим** (/mode rag)\n"
                        "   Задавайте вопросы по базе знаний\n\n"
                        "3. **Голосовой режим** (/mode voice)\n"
                        "   Получайте голосовые ответы\n\n"
                        "Можно отправлять фото ошибок и PDF документы."
            }

        return None

    async def _index_documents(self, chat_id: str) -> dict:
        """Индексация документов из папки data/"""
        docs_indexed = 0

        if not os.path.exists(DATA_DIR):
            logger.warning("Папка data/ не найдена")
            return {"chat_id": chat_id, "text": "❌ Папка data/ не найдена"}

        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            if os.path.isfile(file_path):
                try:
                    content = ""
                    
                    # Обработка .docx файлов
                    if filename.endswith('.docx'):
                        from docx import Document
                        doc = Document(file_path)
                        content = "\n".join([para.text for para in doc.paragraphs])
                    # Обработка текстовых файлов
                    else:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    
                    if content.strip():  # Индексируем только если есть контент
                        # Разбиваем длинный текст на чанки (максимум 1000 символов)
                        chunk_size = 1000
                        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                        
                        for i, chunk in enumerate(chunks):
                            try:
                                self.rag_manager.index_document(
                                    content=chunk,
                                    metadata={"filename": filename, "chunk": i+1, "total_chunks": len(chunks)}
                                )
                                docs_indexed += 1
                                logger.info(f"Индексирован чанк {i+1}/{len(chunks)} документа: {filename}")
                            except Exception as chunk_error:
                                logger.error(f"Ошибка индексации чанка {i+1} файла {filename}: {chunk_error}")
                    else:
                        logger.warning(f"Пустой документ: {filename}")
                        
                except Exception as e:
                    logger.error(f"Ошибка индексации {filename}: {e}", exc_info=True)

        logger.info(f"Проиндексировано документов: {docs_indexed}")
        return {
            "chat_id": chat_id,
            "text": f"✓ Проиндексировано документов: **{docs_indexed}**"
        }

    async def _handle_content(self, message: dict, chat_id: str, user_id: str) -> dict:
        """Обработка контента (текст, голос, фото, документы)"""
        try:
            mode = self.rag_manager.get_user_mode(user_id)
        except Exception as e:
            logger.warning(f"Не удалось получить режим пользователя {user_id}: {e}. Используем режим по умолчанию 'text'")
            mode = "text"
        context_parts = []
        logger.info(f"Обработка сообщения от {user_id} в режиме {mode}")

        # RAG режим: поиск в базе знаний
        text = message.get("text") or message.get("body", {}).get("text")
        if mode == "rag" and text:
            relevant_docs = self.rag_manager.search_text_only(text, top_k=3)
            if relevant_docs:
                context = "\n\n---\n\n".join(relevant_docs)
                prompt = build_rag_prompt(text, context)
                answer = self.yandex_ai.generate_text(prompt)
                logger.info(f"RAG ответ для {user_id}")
                return {"chat_id": chat_id, "text": answer}
            else:
                logger.info(f"RAG: информация не найдена для {user_id}")
                return {"chat_id": chat_id, "text": "Информация не найдена в базе знаний"}

        # Обработка аудио вложений (MAX API) - проверяем первым
        attachments = message.get("attachments") or message.get("body", {}).get("attachments", [])
        logger.info(f"Проверка attachments: {bool(attachments)}")
        if attachments:
            logger.info(f"Найдено {len(attachments)} вложений")
            for attachment in attachments:
                payload = attachment.get("payload", {})
                url = payload.get("url")
                logger.info(f"Обработка вложения с URL: {url[:50] if url else 'None'}...")
                if url:
                    try:
                        logger.info(f"Обнаружено вложение от {user_id}: {url[:100]}...")
                        audio_path = await download_file(url, {}, "mp3")
                        text_from_voice = self.yandex_ai.speech_to_text(audio_path)
                        context_parts.append(f"VOICE_TEXT: {text_from_voice}")
                        logger.info(f"Аудио распознано: {text_from_voice[:50]}...")
                    except Exception as e:
                        logger.error(f"Ошибка обработки вложения: {e}")
        
        # Обработка голосовых сообщений (Telegram-style)
        elif message.get("voice"):
            file_id = message["voice"]["file_id"]
            headers = {"Authorization": MAX_BOT_TOKEN}
            voice_path = await download_file(
                f"{MAX_API_URL}/files/{file_id}",
                headers,
                "ogg"
            )
            logger.info(f"Загружено голосовое сообщение от {user_id}")
            text_from_voice = self.yandex_ai.speech_to_text(voice_path)
            context_parts.append(f"VOICE_TEXT: {text_from_voice}")

        # Обработка изображений
        if message.get("photo"):
            file_id = message["photo"][-1]["file_id"]
            headers = {"Authorization": MAX_BOT_TOKEN}
            photo_path = await download_file(
                f"{MAX_API_URL}/files/{file_id}",
                headers,
                "jpg"
            )
            logger.info(f"Загружено фото от {user_id}")
            vision_result = self.yandex_ai.analyze_image(photo_path)
            if vision_result["text"]:
                context_parts.append(f"IMAGE_TEXT: {vision_result['text']}")
            if vision_result["description"]:
                context_parts.append(f"IMAGE_DESCRIPTION: {vision_result['description']}")

        # Текстовое сообщение
        text = message.get("text") or message.get("body", {}).get("text")
        if text:
            context_parts.append(f"USER_TEXT: {text}")

        if not context_parts:
            logger.warning(f"Не удалось обработать сообщение от {user_id}")
            return {"chat_id": chat_id, "text": "Не удалось обработать сообщение"}

        # Анализ и создание заявки
        full_context = "\n\n".join(context_parts)
        analysis_prompt = build_analysis_prompt(full_context)

        try:
            ticket_json = self.yandex_ai.generate_text(
                analysis_prompt,
                system_prompt="Ты — ассистент сервис-деска. Отвечай только валидным JSON."
            )
            logger.info(f"Заявка создана для {user_id}")

            # Генерация ответа пользователю
            reply_prompt = build_user_reply_prompt(ticket_json)
            reply_text = self.yandex_ai.generate_text(reply_prompt)
            logger.info(f"Ответ сгенерирован для {user_id}")

            # Голосовой ответ (если режим voice)
            voice_path = None
            if mode == "voice":
                try:
                    os.makedirs(TEMP_DIR, exist_ok=True)
                    voice_path = os.path.join(TEMP_DIR, f"response_{user_id}.ogg")
                    self.yandex_ai.text_to_speech(reply_text, voice_path)
                    logger.info(f"Голосовой ответ создан для {user_id}")
                except Exception as e:
                    logger.error(f"Ошибка создания голоса для {user_id}: {e}")
                    voice_path = None

            return {
                "chat_id": chat_id,
                "text": reply_text,
                "voice_path": voice_path
            }

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения от {user_id}: {e}", exc_info=True)
            return {
                "chat_id": chat_id,
                "text": f"❌ Ошибка обработки: {str(e)}"
            }
