-- Создаем функцию для вставки в chat_history
-- Это обходит кэш схемы PostgREST

CREATE OR REPLACE FUNCTION insert_chat_history(
  p_user_id TEXT,
  p_message_type TEXT,
  p_content TEXT,
  p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS VOID AS $$
BEGIN
  INSERT INTO chat_history (user_id, message_type, content, metadata, created_at)
  VALUES (p_user_id, p_message_type, p_content, p_metadata, NOW());
END;
$$ LANGUAGE plpgsql;

-- Тестовая вставка
SELECT insert_chat_history('test_user', 'user', 'Тестовое сообщение', '{"test": true}'::jsonb);

-- Проверка
SELECT * FROM chat_history ORDER BY created_at DESC LIMIT 5;
