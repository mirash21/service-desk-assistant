"""
Тестовый скрипт для проверки работы контекста разговора
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from rag.supabase_manager import SupabaseRAGManager
from utils.logger import logger

def test_chat_history():
    """Тестирует извлечение истории чата"""
    print("=" * 60)
    print("ТЕСТ: Извлечение истории чата")
    print("=" * 60)
    
    rag_manager = SupabaseRAGManager()
    
    # Тест 1: Проверка метода get_chat_history
    print("\n1. Проверяем метод get_chat_history()...")
    test_user_id = "test_user_123"
    
    try:
        history = rag_manager.get_chat_history(test_user_id, limit=5)
        print(f"✓ Метод работает корректно")
        print(f"  Получено сообщений: {len(history)}")
        
        if history:
            print(f"\n  Пример истории:")
            for i, msg in enumerate(history[-3:], 1):  # Последние 3 сообщения
                role = "Пользователь" if msg['role'] == 'user' else "Ассистент"
                content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
                print(f"    {i}. {role}: {content_preview}")
        else:
            print(f"  История пуста (это нормально если нет сообщений от этого пользователя)")
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False
    
    # Тест 2: Проверка формата данных
    print("\n2. Проверяем формат данных...")
    if history:
        first_msg = history[0]
        required_keys = ['role', 'content']
        
        if all(key in first_msg for key in required_keys):
            print(f"✓ Формат данных корректный")
            print(f"  Ключи: {list(first_msg.keys())}")
        else:
            print(f"✗ Отсутствуют ключи: {set(required_keys) - set(first_msg.keys())}")
            return False
    else:
        print(f"⊘ Пропущено (нет данных для проверки)")
    
    # Тест 3: Проверка build_rag_prompt с историей
    print("\n3. Проверяем build_rag_prompt с историей...")
    from utils.prompt_builder import build_rag_prompt
    
    test_query = "Как сбросить пароль?"
    test_context = "Для сброса пароля перейдите в настройки системы."
    test_history = [
        {'role': 'user', 'content': 'У меня проблема с входом'},
        {'role': 'assistant', 'content': 'Опишите проблему подробнее'},
        {'role': 'user', 'content': 'Не могу войти в систему'}
    ]
    
    try:
        prompt = build_rag_prompt(test_query, test_context, test_history)
        print(f"✓ Промпт сгенерирован успешно")
        print(f"  Длина промпта: {len(prompt)} символов")
        
        # Проверяем что история включена в промпт
        if "История диалога:" in prompt:
            print(f"✓ История диалога включена в промпт")
            
            # Проверяем наличие сообщений из истории
            if "У меня проблема с входом" in prompt:
                print(f"✓ Сообщения из истории присутствуют в промпте")
            else:
                print(f"✗ Сообщения из истории не найдены в промпте")
                return False
        else:
            print(f"✗ История диалога НЕ включена в промпт")
            return False
            
    except Exception as e:
        print(f"✗ Ошибка генерации промпта: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_chat_history()
    sys.exit(0 if success else 1)
