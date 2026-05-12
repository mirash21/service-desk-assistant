#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функциональности раздела Activities
"""

import os
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'admin_panel'))

from dotenv import load_dotenv
load_dotenv()

def test_chat_history_api():
    """Тестирует API методы для работы с историей чатов"""
    
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ РАЗДЕЛА ACTIVITIES")
    print("=" * 70)
    
    try:
        from admin_panel.api.rag_api import RAGApi
        api = RAGApi()
        
        print("\n✅ RAGApi успешно импортирован")
        
        # Тест 1: Получение уникальных пользователей
        print("\n📋 Тест 1: Получение списка пользователей...")
        try:
            users = api.get_unique_users()
            print(f"   Найдено пользователей: {len(users)}")
            if users:
                print(f"   Примеры: {users[:3]}")
            else:
                print("   ⚠️  Список пуст (это нормально, если бот еще не получал сообщения)")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False
        
        # Тест 2: Получение статистики пользователей
        print("\n📋 Тест 2: Получение статистики...")
        try:
            stats = api.get_user_stats()
            print(f"   Статистика по пользователям: {len(stats)}")
            if stats:
                for user_id, user_stats in list(stats.items())[:2]:
                    print(f"   - {user_id}: {user_stats}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False
        
        # Тест 3: Получение истории чатов (все сообщения)
        print("\n📋 Тест 3: Получение истории чатов (все)...")
        try:
            result = api.get_chat_history(page=1, page_size=5)
            print(f"   Всего сообщений: {result['total']}")
            print(f"   Страница: {result['page']} из {result['total_pages']}")
            if result['messages']:
                print(f"   Показано сообщений: {len(result['messages'])}")
                for msg in result['messages'][:2]:
                    msg_type = "👤 Пользователь" if msg['message_type'] == 'user' else "🤖 Бот"
                    content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
                    print(f"   - {msg_type}: {content_preview}")
            else:
                print("   ⚠️  История пуста (это нормально для нового развертывания)")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False
        
        # Тест 4: Проверка структуры таблицы
        print("\n📋 Тест 4: Проверка структуры таблицы chat_history...")
        try:
            result = api.supabase.table('chat_history').select('*').limit(1).execute()
            if result.data:
                columns = list(result.data[0].keys())
                print(f"   Колонки таблицы: {columns}")
                
                required_columns = ['id', 'user_id', 'message_type', 'content', 'metadata', 'created_at']
                missing = [col for col in required_columns if col not in columns]
                
                if missing:
                    print(f"   ❌ Отсутствуют колонки: {missing}")
                    return False
                else:
                    print("   ✅ Все необходимые колонки присутствуют")
            else:
                print("   ⚠️  Таблица пуста (структура будет проверена при первом сообщении)")
        except Exception as e:
            print(f"   ❌ Ошибка проверки структуры: {e}")
            print("   💡 Возможно, таблица chat_history еще не создана")
            print("   📋 Выполните миграцию из migrations/002_create_chat_history.sql")
            return False
        
        print("\n" + "=" * 70)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 70)
        print("\n🎉 Раздел Activities готов к использованию!")
        print("\n📝 Следующие шаги:")
        print("   1. Запустите панель администратора: streamlit run admin_panel/app.py")
        print("   2. Перейдите на страницу '💬 Деятельность'")
        print("   3. Отправьте несколько сообщений боту для генерации данных")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("   Убедитесь, что все зависимости установлены:")
        print("   pip install supabase python-dotenv streamlit")
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_chat_history_api()
    sys.exit(0 if success else 1)
