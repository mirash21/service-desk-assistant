-- Проверка индексов таблицы chat_history
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes
WHERE tablename = 'chat_history'
ORDER BY indexname;

-- Если индексы отсутствуют, создаем их:
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_time ON chat_history(user_id, created_at DESC);

-- Проверка количества записей
SELECT count(*) as total_records FROM chat_history;

-- Проверка распределения по пользователям
SELECT 
    user_id,
    count(*) as message_count,
    min(created_at) as first_message,
    max(created_at) as last_message
FROM chat_history
GROUP BY user_id
ORDER BY message_count DESC
LIMIT 10;
