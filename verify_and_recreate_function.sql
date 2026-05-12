-- Проверяем существование функции
SELECT routine_name, routine_type 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name = 'insert_chat_history';

-- Если функция не найдена, создаем её заново
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

-- Тест
SELECT insert_chat_history('test123', 'user', 'Test message', '{}'::jsonb);

-- Проверка данных
SELECT * FROM chat_history WHERE user_id = 'test123' ORDER BY created_at DESC LIMIT 1;
