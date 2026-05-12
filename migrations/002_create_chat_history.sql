-- Миграция: Создание таблицы для хранения истории чатов
-- Дата: 2026-05-10
-- Описание: Добавляет таблицу chat_history для отслеживания диалогов пользователей с ботом

CREATE TABLE IF NOT EXISTS chat_history (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  message_type TEXT NOT NULL CHECK (message_type IN ('user', 'bot')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Индекс для быстрого поиска по пользователю и времени
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_time ON chat_history(user_id, created_at DESC);

-- Комментарий к таблице
COMMENT ON TABLE chat_history IS 'История сообщений между пользователями и ботом';
COMMENT ON COLUMN chat_history.user_id IS 'ID пользователя в MAX Messenger';
COMMENT ON COLUMN chat_history.message_type IS 'Тип сообщения: user (от пользователя) или bot (ответ бота)';
COMMENT ON COLUMN chat_history.content IS 'Содержимое сообщения';
COMMENT ON COLUMN chat_history.metadata IS 'Дополнительные метаданные (режим, наличие изображений и т.д.)';
COMMENT ON COLUMN chat_history.created_at IS 'Время создания сообщения';
