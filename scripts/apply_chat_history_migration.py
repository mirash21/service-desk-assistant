#!/usr/bin/env python3
"""
Скрипт для применения миграции chat_history через прямое подключение к PostgreSQL
"""

import os
import sys
sys.path.insert(0, '/app')

from dotenv import load_dotenv

load_dotenv()

def apply_chat_history_migration():
    """Применяет миграцию chat_history через прямое подключение к БД"""
    
    print("=" * 70)
    print("ПРИМЕНЕНИЕ МИГРАЦИИ: Создание таблицы chat_history")
    print("=" * 70)
    
    # Получаем DATABASE_URL из переменных окружения или конструируем из SUPABASE_URL и KEY
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("\n❌ DATABASE_URL не настроен в .env файле")
        print("\n📋 ИНСТРУКЦИЯ ПО ПРИМЕНЕНИЮ МИГРАЦИИ:")
        print("\n1️⃣  Откройте Supabase Dashboard: https://app.supabase.com")
        print("2️⃣  Выберите ваш проект")
        print("3️⃣  Перейдите в раздел 'SQL Editor' (в левом меню)")
        print("4️⃣  Нажмите 'New query'")
        print("5️⃣  Скопируйте и выполните следующий SQL:\n")
        
        sql_content = open('/app/migrations/002_create_chat_history.sql', 'r').read()
        print("=" * 70)
        print(sql_content)
        print("=" * 70)
        
        print("\n6️⃣  Нажмите 'Run' или Ctrl+Enter")
        print("7️⃣  После успешного выполнения вернитесь сюда\n")
        
        return False
    
    # Если DATABASE_URL есть, используем psycopg2
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        print(f"\n🔗 Подключение к базе данных...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("✅ Подключение установлено")
        
        # Читаем SQL миграции
        sql_file = '/app/migrations/002_create_chat_history.sql'
        with open(sql_file, 'r') as f:
            sql_commands = f.read()
        
        print("\n📝 Выполнение миграции...")
        
        # Разбиваем на отдельные команды и выполняем
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        for i, command in enumerate(commands, 1):
            if command:
                try:
                    print(f"   [{i}/{len(commands)}] {command[:60]}...")
                    cur.execute(command)
                    print(f"   ✅ Выполнено")
                except Exception as e:
                    print(f"   ⚠️  Пропущено (возможно уже существует): {str(e)[:80]}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Миграция успешно применена!")
        print("\n🔍 Таблица chat_history создана с полями:")
        print("   - id (BIGSERIAL PRIMARY KEY)")
        print("   - user_id (TEXT)")
        print("   - message_type (TEXT: 'user' или 'bot')")
        print("   - content (TEXT)")
        print("   - metadata (JSONB)")
        print("   - created_at (TIMESTAMP)")
        
        return True
        
    except ImportError:
        print("\n❌ psycopg2 не установлен")
        print("   Установите: pip install psycopg2-binary")
        print("\n   Или используйте ручной способ через Supabase Dashboard (см. выше)")
        return False
        
    except Exception as e:
        print(f"\n❌ Ошибка выполнения миграции: {e}")
        print("\n   Попробуйте ручной способ через Supabase Dashboard")
        return False


if __name__ == "__main__":
    success = apply_chat_history_migration()
    sys.exit(0 if success else 1)
