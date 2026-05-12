#!/usr/bin/env python3
import time
import sys
sys.path.insert(0, '/app')
from rag.supabase_manager import SupabaseRAGManager

print("Обновление кэша схемы Supabase...")
rag = SupabaseRAGManager()

# Выполняем несколько запросов для обновления кэша
for i in range(5):
    try:
        result = rag.client.table('documents').select('id').limit(1).execute()
        print(f"Попытка {i+1}: OK")
        time.sleep(2)
    except Exception as e:
        print(f"Попытка {i+1}: {e}")

print("\nПроверка chat_history...")
try:
    result = rag.client.table('chat_history').select('*').limit(1).execute()
    print(f"✅ УСПЕХ! Таблица видна!")
except Exception as e:
    print(f"❌ Все еще ошибка: {e}")
    print("\n💡 Подождите еще 1-2 минуты и перезапустите контейнер бота")
