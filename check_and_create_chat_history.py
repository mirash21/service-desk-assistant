#!/usr/bin/env python3
"""
Проверка и создание таблицы chat_history
"""
import sys
sys.path.insert(0, '/app')
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client
import os

client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 70)
print("ПРОВЕРКА ТАБЛИЦЫ chat_history")
print("=" * 70)

try:
    # Проверяем существование таблицы
    result = client.table('chat_history').select('id').limit(1).execute()
    print("\n✅ Таблица chat_history существует")
    print(f"   Количество записей: {len(result.data)}")
    
    if len(result.data) > 0:
        print("\n📊 Пример данных:")
        for record in result.data[:2]:
            print(f"   - ID: {record.get('id')}")
            print(f"     User: {record.get('user_id')}")
            print(f"     Type: {record.get('message_type')}")
            print(f"     Content: {str(record.get('content', ''))[:50]}...")
except Exception as e:
    print(f"\n❌ Таблица chat_history не найдена!")
    print(f"   Ошибка: {e}")
    print("\n" + "=" * 70)
    print("СОЗДАНИЕ ТАБЛИЦЫ")
    print("=" * 70)
    
    # SQL для создания таблицы
    sql_create_table = """
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
    
    print("\n📋 Выполните следующий SQL в Supabase Dashboard:")
    print("\n1. Откройте https://app.supabase.com")
    print("2. Выберите ваш проект")
    print("3. Перейдите в SQL Editor")
    print("4. Вставьте и выполните этот код:\n")
    print("-" * 70)
    print(sql_create_table)
    print("-" * 70)
    print("\n5. После выполнения вернитесь сюда и запустите этот скрипт снова")
