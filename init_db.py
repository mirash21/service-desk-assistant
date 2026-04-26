"""
Скрипт для автоматической инициализации базы данных Supabase
"""
import sys
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, validate_config
from utils.logger import logger


def init_database():
    """Инициализация базы данных Supabase"""
    
    # Валидация конфигурации
    validate_config()
    
    logger.info("Подключение к Supabase...")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    sql_commands = [
        # Включить векторное расширение
        """
        CREATE EXTENSION IF NOT EXISTS vector;
        """,
        
        # Создать таблицу документов
        """
        CREATE TABLE IF NOT EXISTS documents (
          id BIGSERIAL PRIMARY KEY,
          content TEXT NOT NULL,
          metadata JSONB DEFAULT '{}'::jsonb,
          embedding vector(256),
          created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        
        # Создать индекс для быстрого поиска
        """
        CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents 
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        """,
        
        # Функция для семантического поиска
        """
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
        """,
        
        # Таблица настроек пользователей
        """
        CREATE TABLE IF NOT EXISTS user_settings (
          user_id TEXT PRIMARY KEY,
          mode TEXT DEFAULT 'text',
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        );
        """
    ]
    
    try:
        for i, sql in enumerate(sql_commands, 1):
            logger.info(f"Выполнение SQL команды {i}/{len(sql_commands)}...")
            result = client.rpc('exec_sql', {'query': sql}).execute()
            logger.info(f"✓ Команда {i} выполнена успешно")
        
        logger.info("✅ База данных успешно инициализирована!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        logger.info("\nАльтернативный способ:")
        logger.info("1. Откройте SQL Editor в Supabase Studio")
        logger.info("2. Скопируйте SQL из rag/supabase_manager.py (метод init_database)")
        logger.info("3. Выполните SQL вручную")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
