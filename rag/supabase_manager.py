"""
Менеджер для работы с векторной БД Supabase
Поддерживает индексацию документов и семантический поиск
"""
from supabase import create_client, Client
from utils.logger import logger
from config import SUPABASE_URL, SUPABASE_KEY
from services.yandex_service import YandexAIService


class SupabaseRAGManager:
    """Управление RAG базой знаний в Supabase"""

    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.yandex = YandexAIService()
        self.table_name = "documents"
        self.users_table = "user_settings"
        logger.info("SupabaseRAGManager инициализирован")

    def init_database(self):
        """
        Инициализация базы данных

        Выполните этот SQL в Supabase SQL Editor:

        -- Включить векторное расширение
        CREATE EXTENSION IF NOT EXISTS vector;

        -- Создать таблицу документов
        CREATE TABLE documents (
          id BIGSERIAL PRIMARY KEY,
          content TEXT NOT NULL,
          metadata JSONB DEFAULT '{}'::jsonb,
          embedding vector(256),
          created_at TIMESTAMP DEFAULT NOW()
        );

        -- Создать индекс для быстрого поиска
        CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);

        -- Функция для семантического поиска
        CREATE OR REPLACE FUNCTION match_documents(
          query_embedding vector(256),
          match_count int DEFAULT 3,
          filter jsonb DEFAULT '{}'::jsonb
        )
        RETURNS TABLE (
          id bigint,
          content text,
          metadata jsonb,
          similarity float
        )
        LANGUAGE sql STABLE
        AS $$
          SELECT
            id,
            content,
            metadata,
            1 - (embedding <=> query_embedding) AS similarity
          FROM documents
          WHERE metadata @> filter
          ORDER BY embedding <=> query_embedding
          LIMIT match_count;
        $$;

        -- Таблица настроек пользователей
        CREATE TABLE IF NOT EXISTS user_settings (
          user_id TEXT PRIMARY KEY,
          mode TEXT DEFAULT 'text',
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        );
        """
        pass

    def index_document(self, content: str, metadata: dict = None) -> dict:
        """
        Добавить документ в базу знаний

        Args:
            content: Текстовое содержимое документа
            metadata: Метаданные (filename, category и т.д.)

        Returns:
            Информация о созданном документе
        """
        embedding = self.yandex.get_embeddings(content)

        data = {
            "content": content,
            "metadata": metadata or {},
            "embedding": embedding
        }

        result = self.client.table(self.table_name).insert(data).execute()
        return result.data[0] if result.data else None

    def search(self, query: str, top_k: int = 3, filter_metadata: dict = None, min_similarity: float = 0.5) -> list:
        """
        Семантический поиск в базе знаний

        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            filter_metadata: Фильтр по метаданным (например, {"category": "IT"})
            min_similarity: Минимальный порог схожести (0.0-1.0)

        Returns:
            Список найденных документов с контентом и similarity score
        """
        query_embedding = self.yandex.get_embeddings(query)

        params = {
            "query_embedding": query_embedding,
            "match_count": top_k * 2,  # Берем больше для фильтрации
            "filter": filter_metadata or {}
        }

        result = self.client.rpc("match_documents", params).execute()
        
        if not result.data:
            return []
        
        # Фильтруем по порогу схожести
        filtered_results = [
            doc for doc in result.data 
            if doc.get('similarity', 0) >= min_similarity
        ]
        
        # Возвращаем top_k лучших
        return filtered_results[:top_k]

    def search_text_only(self, query: str, top_k: int = 3) -> list:
        """
        Поиск и возврат только текстового контента

        Args:
            query: Поисковый запрос
            top_k: Количество результатов

        Returns:
            Список строк с контентом документов
        """
        results = self.search(query, top_k)
        return [doc["content"] for doc in results]

    def hybrid_search(self, query: str, top_k: int = 5, min_similarity: float = 0.5) -> list:
        """
        Гибридный поиск: семантический + keyword matching
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            min_similarity: Минимальный порог схожести
            
        Returns:
            Список документов, отсортированных по комбинированному score
        """
        # 1. Семантический поиск
        semantic_results = self.search(query, top_k=top_k*2, min_similarity=min_similarity)
        
        # 2. Keyword поиск в content (простой full-text search через Supabase)
        try:
            # Разбиваем запрос на ключевые слова
            keywords = [w.lower() for w in query.split() if len(w) > 3]
            
            if keywords:
                # Ищем документы, содержащие хотя бы одно ключевое слово
                keyword_query = self.client.table(self.table_name).select(
                    'id', 'content', 'metadata'
                )
                
                # Используем ilike для case-insensitive поиска
                for i, keyword in enumerate(keywords[:3]):  # Ограничиваем 3 словами
                    if i == 0:
                        keyword_query = keyword_query.or_(f"content.ilike.%{keyword}%")
                    else:
                        # Добавляем дополнительные условия через OR
                        pass
                
                keyword_results = keyword_query.limit(top_k*2).execute()
                
                # Объединяем результаты с приоритетом семантического поиска
                seen_ids = set()
                combined_results = []
                
                # Сначала добавляем семантические результаты
                for doc in semantic_results:
                    doc_id = doc.get('id')
                    if doc_id and doc_id not in seen_ids:
                        doc['search_type'] = 'semantic'
                        doc['combined_score'] = doc.get('similarity', 0) * 1.2  # Приоритет семантике
                        combined_results.append(doc)
                        seen_ids.add(doc_id)
                
                # Затем добавляем keyword результаты (если есть совпадения)
                if keyword_results.data:
                    for doc in keyword_results.data:
                        doc_id = doc.get('id')
                        if doc_id and doc_id not in seen_ids:
                            doc['search_type'] = 'keyword'
                            doc['similarity'] = 0.4  # Базовый score для keyword
                            doc['combined_score'] = 0.4
                            combined_results.append(doc)
                            seen_ids.add(doc_id)
                
                # Сортируем по combined_score
                combined_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
                
                return combined_results[:top_k]
        except Exception as e:
            logger.warning(f"Ошибка keyword поиска: {e}. Используем только семантический.")
        
        # Fallback: только семантический поиск
        return semantic_results[:top_k]

    def get_stats(self) -> dict:
        """
        Получить статистику базы знаний

        Returns:
            Dict с количеством документов и чанков
        """
        result = self.client.table(self.table_name).select("id", count="exact").execute()
        return {
            "total_docs": result.count,
            "chunks": result.count
        }

    def delete_all(self):
        """Удалить все документы (используйте с осторожностью!)"""
        self.client.table(self.table_name).delete().neq("id", 0).execute()

    def get_user_mode(self, user_id: str) -> str:
        """
        Получить режим пользователя из БД
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Режим пользователя (text/rag/voice)
        """
        try:
            result = self.client.table(self.users_table).select("mode").eq("user_id", user_id).execute()
            if result.data:
                mode = result.data[0]["mode"]
                logger.debug(f"Режим пользователя {user_id}: {mode}")
                return mode
            return "text"
        except Exception as e:
            logger.error(f"Ошибка получения режима пользователя {user_id}: {e}")
            return "text"

    def set_user_mode(self, user_id: str, mode: str) -> bool:
        """
        Сохранить режим пользователя в БД
        
        Args:
            user_id: ID пользователя
            mode: Режим (text/rag/voice)
            
        Returns:
            True если успешно
        """
        try:
            data = {
                "user_id": user_id,
                "mode": mode,
                "updated_at": "now()"
            }
            
            # Проверяем существует ли запись
            existing = self.client.table(self.users_table).select("user_id").eq("user_id", user_id).execute()
            
            if existing.data:
                # Обновляем
                self.client.table(self.users_table).update(data).eq("user_id", user_id).execute()
            else:
                # Создаем
                self.client.table(self.users_table).insert(data).execute()
            
            logger.info(f"Режим пользователя {user_id} установлен в {mode}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения режима пользователя {user_id}: {e}")
            return False

    def get_chat_history(self, user_id: str, limit: int = 5) -> list:
        """
        Получить историю чата пользователя для контекста диалога
        
        Args:
            user_id: ID пользователя
            limit: Количество последних сообщений (по умолчанию 5)
            
        Returns:
            Список сообщений в формате [{'role': 'user'/'assistant', 'content': '...'}]
        """
        try:
            result = self.client.table('chat_history').select(
                'message_type', 'content'
            ).eq('user_id', user_id).order(
                'created_at', desc=True
            ).limit(limit).execute()
            
            if not result.data:
                logger.debug(f"История чата не найдена для пользователя {user_id}")
                return []
            
            # Преобразуем в формат для промпта (последние сообщения первыми в списке)
            history = []
            for msg in reversed(result.data):  # Разворачиваем чтобы oldest first
                role = 'user' if msg['message_type'] == 'user' else 'assistant'
                history.append({
                    'role': role,
                    'content': msg['content']
                })
            
            logger.debug(f"Получено {len(history)} сообщений истории для {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"Ошибка получения истории чата для {user_id}: {e}")
            return []
