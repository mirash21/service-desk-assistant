-- Инициализация базы данных Supabase для Service Desk Assistant
-- Выполните этот SQL в SQL Editor вашего Supabase Studio

-- 1. Включить векторное расширение
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Создать таблицу документов (размерность вектора будет определена автоматически)
CREATE TABLE IF NOT EXISTS documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  embedding vector,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Индекс создается автоматически после добавления данных

-- 4. Функция для семантического поиска
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector,
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

-- 5. Таблица настроек пользователей
CREATE TABLE IF NOT EXISTS user_settings (
  user_id TEXT PRIMARY KEY,
  mode TEXT DEFAULT 'text',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Готово! База данных инициализирована.
