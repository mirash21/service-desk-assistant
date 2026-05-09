-- Миграция: добавление поля created_at в таблицу documents
-- Дата: 2026-04-29

-- Добавляем колонку created_at с default значением NOW()
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Обновляем существующие записи (устанавливаем текущее время)
UPDATE documents 
SET created_at = NOW() 
WHERE created_at IS NULL;

-- Добавляем индекс для быстрых запросов по времени
CREATE INDEX IF NOT EXISTS idx_documents_created_at 
ON documents(created_at);

-- Комментарий
COMMENT ON COLUMN documents.created_at IS 'Время создания документа';
