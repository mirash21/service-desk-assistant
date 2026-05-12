from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 70)
print("СОЗДАНИЕ ТАБЛИЦЫ chat_history ЧЕРЕЗ PYTHON")
print("=" * 70)

# SQL для создания таблицы
sql = """
CREATE TABLE IF NOT EXISTS chat_history (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  message_type TEXT NOT NULL CHECK (message_type IN ('user', 'bot')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_time ON chat_history(user_id, created_at DESC);
"""

try:
    # Выполняем SQL через rpc
    result = client.rpc('exec_sql', {'sql': sql}).execute()
    print("\n✅ Таблица успешно создана!")
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    print("\n💡 Попробуйте выполнить SQL вручную в Supabase Dashboard")
    print("\nSQL код:")
    print("-" * 70)
    print(sql)
    print("-" * 70)
