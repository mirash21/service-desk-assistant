"""
Основной обработчик сообщений от MAX
"""
import json
import os
from datetime import datetime
from typing import Optional
from services.yandex_service import YandexAIService
from services.unanswered_logger import UnansweredQuestionsLogger
from services.voice_manager import VoicePreferencesManager, TTSCacheManager
from rag.supabase_manager import SupabaseRAGManager
from utils.prompt_builder import (
    build_analysis_prompt,
    build_user_reply_prompt,
    build_rag_prompt
)
from utils.file_handler import download_file
from utils.rate_limiter import RateLimiter
from utils.rag_cache import RAGCacheManager
from utils.logger import logger
from config import MAX_BOT_TOKEN, MAX_API_URL, DATA_DIR, TEMP_DIR, MAX_FILE_SIZE


class MessageHandler:
    """Обработка входящих сообщений"""

    def __init__(self):
        self.yandex_ai = YandexAIService()
        self.rag_manager = SupabaseRAGManager()
        self.unanswered_logger = UnansweredQuestionsLogger()
        self.voice_prefs = VoicePreferencesManager()
        self.tts_cache = TTSCacheManager()
        self.rag_cache = RAGCacheManager(ttl_hours=24)  # Кэш на 24 часа
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        logger.info("MessageHandler инициализирован")

    def save_chat_history(self, user_id: str, message_type: str, content: str, metadata: dict = None):
        """
        Сохраняет сообщение в историю чата
        
        Args:
            user_id: ID пользователя
            message_type: Тип сообщения ('user' или 'bot')
            content: Содержимое сообщения
            metadata: Дополнительные метаданные
        """
        try:
            # Пробуем через RPC функцию
            try:
                result = self.rag_manager.client.rpc(
                    'insert_chat_history',
                    {
                        'p_user_id': user_id,
                        'p_message_type': message_type,
                        'p_content': content,
                        'p_metadata': metadata or {}
                    }
                ).execute()
                logger.debug(f"История чата сохранена (RPC) для {user_id}: {message_type}")
            except Exception as rpc_error:
                # Если RPC не работает, используем прямой insert
                logger.debug(f"RPC недоступен, используем прямой insert для {user_id}")
                data = {
                    "user_id": user_id,
                    "message_type": message_type,
                    "content": content,
                    "metadata": metadata or {}
                }
                result = self.rag_manager.client.table("chat_history").insert(data).execute()
                
                if result.data:
                    logger.debug(f"История чата сохранена (direct) для {user_id}: {message_type}")
                else:
                    logger.warning(f"Не удалось сохранить историю чата (direct) для {user_id}")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения истории чата: {e}")

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
        logger.info(f"Извлеченный текст: '{text}' (длина: {len(text)})")
        
        # Сохраняем сообщение пользователя в историю
        if text:
            self.save_chat_history(user_id, 'user', text, {'command': True if text.startswith('/') else False})
        
        if text.startswith("/"):
            logger.info(f"Обнаружена команда: {text}")
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
                        #"/mode [text|rag|voice] — переключить режим\n"
                        "/voice [on|off] — включить/выключить озвучку ответов\n"
                        #"/index — проиндексировать базу знаний\n"
                        #"/stats — статистика базы знаний\n"
                        #"/help — помощь"
            }

        elif command == "/voice":
            # Управление озвучкой ответов
            if args.lower() in ["on", "вкл", "включить"]:
                self.voice_prefs.set_user_voice_preference(user_id, True)
                return {"chat_id": chat_id, "text": "✅ Озвучка ответов включена. Теперь я буду отправлять голосовые сообщения."}
            elif args.lower() in ["off", "выкл", "выключить"]:
                self.voice_prefs.set_user_voice_preference(user_id, False)
                return {"chat_id": chat_id, "text": "❌ Озвучка ответов выключена. Буду отвечать только текстом."}
            else:
                current = self.voice_prefs.get_user_voice_preference(user_id)
                status = "включена" if current else "выключена"
                return {
                    "chat_id": chat_id,
                    "text": f"🔊 Текущий статус озвучки: {status}\n\n"
                            f"Используйте:\n"
                            f"/voice on — включить озвучку\n"
                            f"/voice off — выключить озвучку"
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

        # Файлы, которые нужно исключить из индексации
        excluded_files = [
            'user_preferences.json',
            'unanswered_questions.json'
        ]

        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            
            # Пропускаем исключённые файлы
            if filename in excluded_files:
                logger.info(f"Пропущен служебный файл: {filename}")
                continue
            
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

    def _generate_voice_response(self, text: str, user_id: str) -> Optional[str]:
        """
        Генерирует голосовой ответ с кэшированием
        
        Args:
            text: Текст для озвучивания
            user_id: ID пользователя (для создания уникального пути)
            
        Returns:
            Путь к аудиофайлу или None при ошибке
        """
        try:
            # Проверяем кэш
            cached_path = self.tts_cache.get_cached_audio(text)
            if cached_path:
                logger.info(f"TTS кэш hit для пользователя {user_id}")
                return cached_path
            
            # Генерируем новый аудиофайл
            os.makedirs(TEMP_DIR, exist_ok=True)
            temp_path = os.path.join(TEMP_DIR, f"tts_{user_id}_{int(datetime.now().timestamp())}.ogg")
            
            logger.info(f"Генерация TTS для пользователя {user_id}: {text[:50]}...")
            from config import TTS_VOICE, TTS_LANGUAGE
            audio_path = self.yandex_ai.text_to_speech(text, temp_path, voice=TTS_VOICE, lang=TTS_LANGUAGE)
            
            # Кэшируем результат
            cached_path = self.tts_cache.cache_audio(text, audio_path)
            
            logger.info(f"TTS сгенерирован: {cached_path}")
            return cached_path
            
        except Exception as e:
            logger.error(f"Ошибка генерации TTS для {user_id}: {e}", exc_info=True)
            return None

    async def _classify_intent(self, text: str, has_image: bool = False) -> str:
        """
        Классификация намерения пользователя
        
        Args:
            text: Текст сообщения
            has_image: Есть ли изображение в сообщении
            
        Returns:
            'question', 'ticket_creation' или 'unknown'
        """
        # Ключевые слова для создания задачи (явные запросы)
        ticket_keywords = [
            "создай задачу", "создать задачу", "зарегистрируй инцидент", 
            "зарегистрировать инцидент", "открой тикет", "открыть тикет",
            "оформи заявку", "оформить заявку"
        ]
        
        # Ключевые слова, указывающие на проблему/ошибку (но это могут быть вопросы)
        problem_indicators = [
            "не работает", "сломалось", "ошибка", "баг", "поломка", "авария",
            "не открывается", "не запускается", "не подключается"
        ]
        
        # Ключевые слова для вопросов
        question_keywords = [
            "как", "что", "где", "когда", "почему", "зачем",
            "сколько", "какой", "который", "можешь", "можно ли",
            "объясни", "расскажи", "подскажи", "помоги понять",
            "посмотри", "посмотрите", "видишь", "видите", "распознай"
        ]
        
        # Специальные ключевые слова для вопросов по изображению
        image_question_keywords = [
            "что это", "что здесь", "что написано", "прочитай", "переведи",
            "распознай текст", "что на фото", "что на картинке"
        ]
        
        text_lower = text.lower()
        
        # Фильтруем служебные сообщения об ошибках
        if "IMAGE_ERROR" in text or "Не удалось проанализировать" in text:
            # Если есть изображение и только сообщение об ошибке - считаем как image_question
            if has_image:
                return "image_question"
        
        # Если есть изображение, проверяем специальные паттерны
        if has_image:
            # Вопросы по изображению
            for keyword in image_question_keywords:
                if keyword in text_lower:
                    return "image_question"
            
            # Если только изображение без текста или короткий текст - скорее всего вопрос
            text_stripped = text.strip() if text else ""
            if not text or len(text_stripped) < 10:
                return "image_question"
        
        # Проверяем наличие явных ключевых слов для создания задачи
        for keyword in ticket_keywords:
            if keyword in text_lower:
                return "ticket_creation"
        
        # Проверяем наличие вопросительных слов - приоритет у вопросов
        for keyword in question_keywords:
            if keyword in text_lower:
                return "question"
        
        # Если есть вопросительный знак, скорее всего это вопрос
        if "?" in text:
            return "question"
        
        # Если есть индикаторы проблемы, но нет явного запроса на создание задачи -
        # считаем это вопросом (RAG может содержать решение)
        for indicator in problem_indicators:
            if indicator in text_lower:
                return "question"
        
        # По умолчанию считаем, что это вопрос (более безопасно)
        return "question"

    async def _handle_question(self, context: str, chat_id: str, user_id: str) -> dict:
        """
        Обработка обычного вопроса - даем прямой ответ без создания задачи
        
        Args:
            context: Контекст сообщения
            chat_id: ID чата
            user_id: ID пользователя
            
        Returns:
            Ответ пользователю
        """
        # Проверяем кэш RAG ответов
        cached = self.rag_cache.get(context, top_k=3)
        if cached:
            logger.info(f"✅ Кэш попадание для вопроса: {context[:50]}...")
            user_answer = cached['answer']
            rag_results = [{'content': ctx} for ctx in cached['contexts']]
            
            # Проверяем, включена ли озвучка для пользователя
            voice_enabled = self.voice_prefs.get_user_voice_preference(user_id)
            voice_path = None
            if voice_enabled:
                voice_path = self._generate_voice_response(user_answer, user_id)
            
            # Сохраняем ответ бота в историю
            self.save_chat_history(user_id, 'bot', user_answer, {'has_voice': voice_enabled, 'voice_path': voice_path, 'from_cache': True})
            
            return {
                "chat_id": chat_id,
                "text": user_answer,
                "voice_path": voice_path
            }
        
        logger.info(f"❌ Кэш промах, обрабатываем вопрос: {context[:50]}...")
        
        # Получаем историю чата для контекста
        conversation_history = self.rag_manager.get_chat_history(user_id, limit=5)
        logger.info(f"Получено {len(conversation_history)} сообщений истории для {user_id}")
        
        # Поиск релевантных документов через RAG
        logger.info(f"Поиск по базе знаний для вопроса: {context[:100]}")
        rag_results = self.rag_manager.search(context, top_k=3)
        
        if rag_results:
            logger.info(f"Найдено {len(rag_results)} документов в базе знаний")
            # Формируем контекст из найденных документов
            knowledge_context = "\n\n".join([
                f"Документ {i+1}:\n{doc.get('content', '')}"
                for i, doc in enumerate(rag_results)
            ])
            logger.info(f"RAG контекст (первые 500 симв.): {knowledge_context[:500]}")
        else:
            logger.info("Документы в базе знаний не найдены")
            knowledge_context = "Информация в базе знаний отсутствует."
        
        # Используем RAG промпт с историей диалога
        prompt = build_rag_prompt(context, knowledge_context, conversation_history)
        
        try:
            answer = self.yandex_ai.generate_text(prompt)
            logger.info(f"Ответ на вопрос для {user_id}")
            
            # Извлекаем черновик ответа если он есть (убираем техническую метку)
            user_answer = answer  # по умолчанию весь ответ
            suggested_answer = None
            
            draft_markers = ["[ЧЕРНОВИК ОТВЕТА - ТРЕБУЕТ ПРОВЕРКИ ЭКСПЕРТОМ]", 
                            "[ЧЕРНОВИК ОТВЕТА — ТРЕБУЕТ ПРОВЕРКИ ЭКСПЕРТОМ]"]
            
            for marker in draft_markers:
                if marker in answer:
                    parts = answer.split(marker)
                    if len(parts) > 1:
                        suggested_answer = parts[1].strip()
                        # Пользователю отправляем только часть до метки
                        user_answer = parts[0].strip()
                        logger.info(f"Удалена техническая метка из ответа")
                        logger.info(f"Ответ пользователю (полный): {user_answer}")
                    break
            
            # Проверяем, включена ли озвучка для пользователя
            voice_enabled = self.voice_prefs.get_user_voice_preference(user_id)
            logger.info(f"Озвучка для {user_id}: {'включена' if voice_enabled else 'выключена'}")
            
            voice_path = None
            if voice_enabled:
                logger.info(f"Генерация TTS для {user_id}...")
                voice_path = self._generate_voice_response(user_answer, user_id)
                logger.info(f"TTS результат: {voice_path}")
            
            # Сохраняем в кэш RAG
            contexts = [doc.get('content', '') for doc in rag_results] if rag_results else []
            self.rag_cache.set(context, user_answer, contexts, top_k=3)
            logger.info(f"💾 Ответ сохранен в кэш")
            
            # Сохраняем ответ бота в историю
            self.save_chat_history(user_id, 'bot', user_answer, {'has_voice': voice_enabled, 'voice_path': voice_path, 'from_cache': False})
            
            return {
                "chat_id": chat_id,
                "text": user_answer,
                "voice_path": voice_path
            }
        except Exception as e:
            logger.error(f"Ошибка ответа на вопрос: {e}", exc_info=True)
            return {
                "chat_id": chat_id,
                "text": "❌ Извините, не удалось обработать ваш вопрос. Попробуйте переформулировать."
            }

    async def _handle_image_question(self, context: str, chat_id: str, user_id: str) -> dict:
        """
        Обработка вопроса по изображению - анализируем содержимое и отвечаем
        
        Args:
            context: Контекст с IMAGE_TEXT и IMAGE_DESCRIPTION
            chat_id: ID чата
            user_id: ID пользователя
            
        Returns:
            Ответ пользователю с анализом изображения
        """
        # Получаем историю чата для контекста
        conversation_history = self.rag_manager.get_chat_history(user_id, limit=5)
        logger.info(f"Получено {len(conversation_history)} сообщений истории для {user_id} (image question)")
        
        # Извлекаем текст изображения
        image_text = ""
        if "IMAGE_TEXT:" in context:
            image_text = context.split("IMAGE_TEXT:")[1].split("\n")[0].strip()
        
        logger.info(f"Извлеченный текст с изображения (первые 150 симв): {image_text[:150]}")
        
        # Проверяем, является ли текст описанием ошибки/проблемы (а не вопросом)
        error_indicators = [
            "возникла проблема", "необходимо перезагрузить", "ошибка", 
            "критическая ошибка", "синий экран", "bsod",
            "не удалось", "отказано в доступе", "не найдено"
        ]
        
        is_error = any(indicator in image_text.lower() for indicator in error_indicators)
        logger.info(f"Проверка на ошибку: is_error={is_error}, indicators_found={[ind for ind in error_indicators if ind in image_text.lower()]}")
        
        if is_error:
            logger.info(f"Обнаружена ошибка на изображении, создаём заявку")
            # Создаём заявку через стандартный метод
            return await self._create_ticket(context, chat_id, user_id, "text")
        
        # Если это не ошибка, используем RAG для ответа на вопрос
        logger.info(f"Поиск по базе знаний для вопроса по изображению")
        rag_results = self.rag_manager.search(context, top_k=3)
        
        if rag_results:
            logger.info(f"Найдено {len(rag_results)} документов в базе знаний")
            knowledge_context = "\n\n".join([
                f"Документ {i+1}:\n{doc.get('content', '')}"
                for i, doc in enumerate(rag_results)
            ])
        else:
            logger.info("Документы в базе знаний не найдены")
            knowledge_context = "Информация в базе знаний отсутствует."
        
        prompt = build_rag_prompt(
            f"Вопрос пользователя по изображению:\n{context}\n\nКонтекст изображения учитывай при ответе.",
            knowledge_context,
            conversation_history
        )
        
        try:
            answer = self.yandex_ai.generate_text(prompt)
            logger.info(f"Ответ на вопрос по изображению для {user_id}")
            
            # Извлекаем черновик ответа если он есть (убираем техническую метку)
            user_answer = answer  # по умолчанию весь ответ
            
            draft_markers = ["[ЧЕРНОВИК ОТВЕТА - ТРЕБУЕТ ПРОВЕРКИ ЭКСПЕРТОМ]", 
                            "[ЧЕРНОВИК ОТВЕТА — ТРЕБУЕТ ПРОВЕРКИ ЭКСПЕРТОМ]"]
            
            for marker in draft_markers:
                if marker in answer:
                    parts = answer.split(marker)
                    if len(parts) > 1:
                        # Пользователю отправляем только часть до метки
                        user_answer = parts[0].strip()
                        logger.info(f"Удалена техническая метка из ответа")
                    break
            
            # Проверяем, включена ли озвучка для пользователя
            voice_path = None
            if self.voice_prefs.get_user_voice_preference(user_id):
                voice_path = self._generate_voice_response(user_answer, user_id)
            
            # Сохраняем ответ бота в историю
            self.save_chat_history(user_id, 'bot', user_answer, {'has_voice': voice_path is not None, 'image_question': True})
            
            return {
                "chat_id": chat_id,
                "text": user_answer,
                "voice_path": voice_path
            }
        except Exception as e:
            logger.error(f"Ошибка ответа на вопрос по изображению: {e}", exc_info=True)
            return {
                "chat_id": chat_id,
                "text": "❌ Извините, не удалось проанализировать изображение. Попробуйте отправить другое фото или опишите проблему текстом."
            }

    async def _create_ticket(self, context: str, chat_id: str, user_id: str, mode: str) -> dict:
        """
        Создание задачи из сообщения
        
        Args:
            context: Контекст сообщения (может включать IMAGE_TEXT, VOICE_TEXT и т.д.)
            chat_id: ID чата
            user_id: ID пользователя
            mode: Режим пользователя (text/rag/voice)
            
        Returns:
            Ответ пользователю с подтверждением создания задачи
        """
        analysis_prompt = build_analysis_prompt(context)

        try:
            ticket_json = self.yandex_ai.generate_text(
                analysis_prompt,
                system_prompt="Ты — ассистент сервис-деска. Отвечай только валидным JSON."
            )
            logger.info(f"Заявка создана для {user_id}")

            # Генерация ответа пользователю с учетом контекста
            reply_prompt = build_user_reply_prompt(ticket_json)
            
            # Добавляем информацию об источнике проблемы (фото, голос, текст)
            if "IMAGE_TEXT" in context or "IMAGE_DESCRIPTION" in context:
                reply_prompt += "\n\nВажно: Пользователь отправил изображение с проблемой. Упомяни это в ответе (например: 'по полученному скриншоту', 'на основе отправленного фото')."
            elif "VOICE_TEXT" in context:
                reply_prompt += "\n\nВажно: Пользователь отправил голосовое сообщение. Учитывай это при формировании ответа."
            
            reply_text = self.yandex_ai.generate_text(reply_prompt)
            logger.info(f"Ответ сгенерирован для {user_id}")

            # Голосовой ответ (если включена озвучка или режим voice)
            voice_path = None
            if mode == "voice" or self.voice_prefs.get_user_voice_preference(user_id):
                try:
                    # Используем кэширование TTS
                    voice_path = self._generate_voice_response(reply_text, user_id)
                    if voice_path:
                        logger.info(f"Голосовой ответ создан для {user_id} (кэш: {self.tts_cache.get_cached_audio(reply_text) is not None})")
                except Exception as e:
                    logger.error(f"Ошибка создания голоса для {user_id}: {e}")
                    voice_path = None

            # Сохраняем ответ бота в историю
            self.save_chat_history(user_id, 'bot', reply_text, {'ticket_created': True, 'has_voice': voice_path is not None, 'mode': mode})

            return {
                "chat_id": chat_id,
                "text": reply_text,
                "voice_path": voice_path
            }

        except Exception as e:
            logger.error(f"Ошибка создания задачи от {user_id}: {e}", exc_info=True)
            return {
                "chat_id": chat_id,
                "text": f"❌ Ошибка обработки: {str(e)}"
            }

    async def _handle_content(self, message: dict, chat_id: str, user_id: str) -> dict:
        """Обработка контента (текст, голос, фото, документы)"""
        try:
            mode = self.rag_manager.get_user_mode(user_id)
        except Exception as e:
            logger.warning(f"Не удалось получить режим пользователя {user_id}: {e}. Используем режим по умолчанию 'rag'")
            mode = "rag"  # По умолчанию используем RAG
        context_parts = []
        has_image = False  # Флаг наличия изображения
        logger.info(f"Обработка сообщения от {user_id} в режиме {mode}")

        # RAG режим: поиск в базе знаний (по умолчанию для всех текстовых вопросов)
        text = message.get("text") or message.get("body", {}).get("text")
        if mode == "rag" and text:
            # Получаем историю чата для контекста
            conversation_history = self.rag_manager.get_chat_history(user_id, limit=5)
            logger.info(f"Получено {len(conversation_history)} сообщений истории для {user_id} (RAG mode)")
            
            relevant_docs = self.rag_manager.search_text_only(text, top_k=3)
            if relevant_docs:
                context = "\n\n---\n\n".join(relevant_docs)
                prompt = build_rag_prompt(text, context, conversation_history)
                answer = self.yandex_ai.generate_text(prompt)
                logger.info(f"RAG ответ найден для {user_id}")
                return {"chat_id": chat_id, "text": answer}
            else:
                # RAG не нашел релевантных документов - генерируем ответ с черновиком
                logger.info(f"RAG: информация не найдена для {user_id}")
                
                # Генерируем черновик ответа через LLM с пустым контекстом
                empty_context_prompt = build_rag_prompt(text, "(база знаний пуста или не содержит релевантной информации)", conversation_history)
                llm_response = self.yandex_ai.generate_text(empty_context_prompt)
                
                # Извлекаем черновик ответа если он есть
                suggested_answer = None
                user_response = llm_response  # по умолчанию весь ответ
                
                logger.info(f"LLM ответ (первые 200 симв.): {llm_response[:200]}")
                
                # Поддерживаем оба варианта тире: дефис (-) и длинное тире (—)
                draft_markers = ["[ЧЕРНОВИК ОТВЕТА - ТРЕБУЕТ ПРОВЕРКИ ЭКСПЕРТОМ]", 
                                "[ЧЕРНОВИК ОТВЕТА — ТРЕБУЕТ ПРОВЕРКИ ЭКСПЕРТОМ]"]
                
                for marker in draft_markers:
                    if marker in llm_response:
                        logger.info(f"Найдена метка: {repr(marker)}")
                        parts = llm_response.split(marker)
                        if len(parts) > 1:
                            suggested_answer = parts[1].strip()
                            # Пользователю отправляем только часть до метки
                            user_response = parts[0].strip()
                            logger.info(f"Ответ пользователю: {user_response[:100]}")
                        break
                
                # Логируем неразрешенный вопрос
                self.unanswered_logger.log_unanswered_question(
                    question=text,
                    user_id=user_id,
                    suggested_answer=suggested_answer,
                    has_image=has_image,
                    mode=mode
                )
                
                # Отвечаем пользователю (без метки черновика)
                return {
                    "chat_id": chat_id,
                    "text": user_response
                }

        # Обработка вложений (MAX API) - проверяем первым
        attachments = message.get("attachments") or message.get("body", {}).get("attachments", [])
        logger.info(f"Проверка attachments: {bool(attachments)}")
        if attachments:
            logger.info(f"Найдено {len(attachments)} вложений")
            for attachment in attachments:
                payload = attachment.get("payload", {})
                url = payload.get("url")
                
                # Определяем тип вложения
                is_photo = "photo_id" in payload or "photo" in payload
                is_audio = "audio_id" in payload or "voice" in payload or "duration" in payload
                
                logger.info(f"Обработка вложения: photo={is_photo}, audio={is_audio}, URL: {url[:50] if url else 'None'}...")
                
                if url and is_photo:
                    # Это изображение - обрабатываем как фото
                    try:
                        logger.info(f"Обнаружено фото от {user_id}")
                        has_image = True
                        photo_path = await download_file(url, {}, "jpg")
                        
                        # Если это WebP (начинается с RIFF), конвертируем в JPEG
                        with open(photo_path, 'rb') as f:
                            header = f.read(10)
                        
                        if header[:4] == b'RIFF':
                            logger.info("Обнаружен формат WebP, конвертируем в JPEG")
                            try:
                                from PIL import Image
                                img = Image.open(photo_path)
                                jpeg_path = photo_path.replace('.jpg', '_converted.jpg')
                                img.convert('RGB').save(jpeg_path, 'JPEG', quality=95)
                                logger.info(f"Конвертация WebP -> JPEG успешна")
                                photo_path = jpeg_path
                            except Exception as e:
                                logger.error(f"Ошибка конвертации WebP: {e}")
                        
                        vision_result = self.yandex_ai.analyze_image(photo_path)
                        if vision_result["text"]:
                            context_parts.append(f"IMAGE_TEXT: {vision_result['text']}")
                            logger.info(f"Распознан текст на изображении: {len(vision_result['text'])} симв.")
                        if vision_result["description"]:
                            context_parts.append(f"IMAGE_DESCRIPTION: {vision_result['description']}")
                            logger.info(f"Описание изображения: {vision_result['description']}")
                        
                        # Сохраняем информацию об изображении в историю
                        image_metadata = {
                            'has_image': True,
                            'image_text': vision_result.get('text', ''),
                            'image_description': vision_result.get('description', '')
                        }
                        self.save_chat_history(user_id, 'user', '[Изображение]', image_metadata)
                        
                    except Exception as e:
                        logger.error(f"Ошибка анализа изображения: {e}", exc_info=True)
                        context_parts.append("IMAGE_ERROR: Не удалось проанализировать изображение")
                        
                elif url and is_audio:
                    # Это аудио - обрабатываем как голосовое сообщение
                    try:
                        logger.info(f"Обнаружено аудио от {user_id}: {url[:100]}...")
                        audio_path = await download_file(url, {}, "mp3")
                        text_from_voice = self.yandex_ai.speech_to_text(audio_path)
                        context_parts.append(f"VOICE_TEXT: {text_from_voice}")
                        logger.info(f"Аудио распознано: {text_from_voice[:50]}...")
                        
                        # Сохраняем голосовое сообщение в историю
                        self.save_chat_history(user_id, 'user', text_from_voice, {'has_voice': True, 'voice_type': 'audio_attachment'})
                        
                    except Exception as e:
                        logger.error(f"Ошибка обработки аудио: {e}")
                        # Graceful degradation: если STT не работает, отправляем сообщение
                        return {
                            "chat_id": chat_id,
                            "text": "❌ Не удалось распознать речь. Попробуйте отправить текстовое сообщение или запишите голосовое сообщение четче."
                        }
                elif url:
                    # Неизвестный тип вложения - пробуем как аудио (для обратной совместимости)
                    logger.warning(f"Неизвестный тип вложения, пытаемся обработать как аудио")
                    try:
                        audio_path = await download_file(url, {}, "mp3")
                        text_from_voice = self.yandex_ai.speech_to_text(audio_path)
                        context_parts.append(f"VOICE_TEXT: {text_from_voice}")
                    except Exception as e:
                        logger.error(f"Ошибка обработки неизвестного вложения: {e}")
        
        # Обработка голосовых сообщений (Telegram-style) - резервный вариант
        elif message.get("voice"):
            file_id = message["voice"]["file_id"]
            headers = {"Authorization": MAX_BOT_TOKEN}
            voice_path = await download_file(
                f"{MAX_API_URL}/files/{file_id}",
                headers,
                "ogg"
            )
            logger.info(f"Загружено голосовое сообщение от {user_id}")
            try:
                text_from_voice = self.yandex_ai.speech_to_text(voice_path)
                context_parts.append(f"VOICE_TEXT: {text_from_voice}")
            except Exception as e:
                logger.error(f"Ошибка распознавания голоса: {e}")
                return {
                    "chat_id": chat_id,
                    "text": "❌ Не удалось распознать речь. Попробуйте отправить текстовое сообщение или запишите голосовое сообщение четче."
                }

        # Текстовое сообщение
        text = message.get("text") or message.get("body", {}).get("text")
        if text:
            context_parts.append(f"USER_TEXT: {text}")
            # Сохраняем текстовое сообщение в историю (если еще не сохранено как команда)
            if not text.startswith('/'):
                self.save_chat_history(user_id, 'user', text, {'has_image': has_image})

        if not context_parts:
            logger.warning(f"Не удалось обработать сообщение от {user_id}")
            return {"chat_id": chat_id, "text": "Не удалось обработать сообщение"}

        # Классификация намерения пользователя
        full_context = "\n\n".join(context_parts)
        intent = await self._classify_intent(full_context, has_image)
        logger.info(f"Классифицированное намерение для {user_id}: {intent} (has_image={has_image})")

        # Обработка в зависимости от намерения
        if intent == "image_question":
            # Вопрос по изображению - анализируем и отвечаем
            return await self._handle_image_question(full_context, chat_id, user_id)
        elif intent == "question":
            # Если есть изображение, используем обработчик изображений
            if has_image:
                return await self._handle_image_question(full_context, chat_id, user_id)
            
            # Обычный вопрос без изображения
            if mode == "rag" and not has_image:
                # В режиме RAG используем базу знаний
                text = message.get("text") or message.get("body", {}).get("text")
                if text:
                    # Получаем историю чата для контекста
                    conversation_history = self.rag_manager.get_chat_history(user_id, limit=5)
                    logger.info(f"Получено {len(conversation_history)} сообщений истории для {user_id} (классификация)")
                    
                    relevant_docs = self.rag_manager.search_text_only(text, top_k=3)
                    if relevant_docs:
                        context = "\n\n---\n\n".join(relevant_docs)
                        prompt = build_rag_prompt(text, context, conversation_history)
                        answer = self.yandex_ai.generate_text(prompt)
                        logger.info(f"RAG ответ найден для {user_id} (через классификацию)")
                        return {"chat_id": chat_id, "text": answer}
                    else:
                        # RAG не нашел ответа - генерируем черновик и логируем
                        logger.info(f"RAG: информация не найдена для {user_id} (через классификацию)")
                        
                        # Генерируем черновик ответа через LLM с пустым контекстом
                        empty_context_prompt = build_rag_prompt(text, "(база знаний пуста или не содержит релевантной информации)", conversation_history)
                        llm_response = self.yandex_ai.generate_text(empty_context_prompt)
                        
                        # Извлекаем черновик ответа если он есть
                        suggested_answer = None
                        user_response = llm_response  # по умолчанию весь ответ
                        
                        # Поддерживаем оба варианта тире: дефис (-) и длинное тире (—)
                        draft_markers = ["[ЧЕРНОВИК ОТВЕТА - ТРЕБУЕТ ПРОВЕРКИ ЭКСПЕРТОМ]", 
                                        "[ЧЕРНОВИК ОТВЕТА — ТРЕБУЕТ ПРОВЕРКИ ЭКСПЕРТОМ]"]
                        
                        for marker in draft_markers:
                            if marker in llm_response:
                                parts = llm_response.split(marker)
                                if len(parts) > 1:
                                    suggested_answer = parts[1].strip()
                                    # Пользователю отправляем только часть до метки
                                    user_response = parts[0].strip()
                                break
                        
                        # Логируем неразрешенный вопрос
                        self.unanswered_logger.log_unanswered_question(
                            question=text,
                            user_id=user_id,
                            suggested_answer=suggested_answer,
                            context=full_context,
                            has_image=has_image,
                            mode=mode
                        )
                        
                        return {
                            "chat_id": chat_id,
                            "text": user_response
                        }
            # Если не RAG режим или есть изображение - даем прямой ответ
            return await self._handle_question(full_context, chat_id, user_id)
        elif intent == "ticket_creation":
            # Запрос на создание задачи - создаем заявку
            return await self._create_ticket(full_context, chat_id, user_id, mode)
        else:
            # По умолчанию создаем задачу (для обратной совместимости)
            logger.info(f"Неопределенное намерение, создаем задачу по умолчанию для {user_id}")
            return await self._create_ticket(full_context, chat_id, user_id, mode)
