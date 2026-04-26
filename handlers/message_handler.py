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

        chat_id = message.get("chat", {}).get("chat_id")
        user_id = message.get("from", {}).get("user_id")
        
        # Проверка rate limit
        if not self.rate_limiter.is_allowed(user_id):
            logger.warning(f"Rate limit для пользователя {user_id}")
            return {
                "chat_id": chat_id,
                "text": "⏳ Слишком много запросов. Подождите минуту и попробуйте снова."
            }

        # Обработка команд
        if message.get("text", "").startswith("/"):
            return await self._handle_command(message, chat_id, user_id)

        # Обработка контента
        return await self._handle_content(message, chat_id, user_id)

    async def _handle_command(self, message: dict, chat_id: str, user_id: str) -> dict:
        """Обработка команд бота"""
        text = message.get("text", "")
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
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    self.rag_manager.index_document(
                        content=content,
                        metadata={"filename": filename}
                    )
                    docs_indexed += 1
                    logger.info(f"Индексирован документ: {filename}")
                except Exception as e:
                    logger.error(f"Ошибка индексации {filename}: {e}")

        logger.info(f"Проиндексировано документов: {docs_indexed}")
        return {
            "chat_id": chat_id,
            "text": f"✓ Проиндексировано документов: **{docs_indexed}**"
        }

    async def _handle_content(self, message: dict, chat_id: str, user_id: str) -> dict:
        """Обработка контента (текст, голос, фото, документы)"""
        mode = self.rag_manager.get_user_mode(user_id)
        context_parts = []
        logger.info(f"Обработка сообщения от {user_id} в режиме {mode}")

        # RAG режим: поиск в базе знаний
        if mode == "rag" and message.get("text"):
            relevant_docs = self.rag_manager.search_text_only(message["text"], top_k=3)
            if relevant_docs:
                context = "\n\n---\n\n".join(relevant_docs)
                prompt = build_rag_prompt(message["text"], context)
                answer = self.yandex_ai.generate_text(prompt)
                logger.info(f"RAG ответ для {user_id}")
                return {"chat_id": chat_id, "text": answer}
            else:
                logger.info(f"RAG: информация не найдена для {user_id}")
                return {"chat_id": chat_id, "text": "Информация не найдена в базе знаний"}

        # Обработка голосовых сообщений
        if message.get("voice"):
            file_id = message["voice"]["file_id"]
            headers = {"Authorization": f"Bearer {MAX_BOT_TOKEN}"}
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
            headers = {"Authorization": f"Bearer {MAX_BOT_TOKEN}"}
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
        if message.get("text"):
            context_parts.append(f"USER_TEXT: {message['text']}")

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
                os.makedirs(TEMP_DIR, exist_ok=True)
                voice_path = os.path.join(TEMP_DIR, f"response_{user_id}.ogg")
                self.yandex_ai.text_to_speech(reply_text, voice_path)
                logger.info(f"Голосовой ответ создан для {user_id}")

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
