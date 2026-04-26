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

    def search(self, query: str, top_k: int = 3, filter_metadata: dict = None) -> list:
        """
        Семантический поиск в базе знаний

        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            filter_metadata: Фильтр по метаданным (например, {"category": "IT"})

        Returns:
            Список найденных документов с контентом и similarity score
        """
        query_embedding = self.yandex.get_embeddings(query)

        params = {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "filter": filter_metadata or {}
        }

        result = self.client.rpc("match_documents", params).execute()
        return result.data if result.data else []

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
