import os
import sys
sys.path.insert(0, '/app')

from rag.supabase_manager import SupabaseRAGManager

rag = SupabaseRAGManager()

results = rag.search('как сбросить пароль', top_k=3)
print(f"Найдено документов: {len(results)}")
for i, doc in enumerate(results):
    print(f"\nДокумент {i+1}:")
    print(f"Ключи: {list(doc.keys())}")
    content = doc.get('content', 'НЕТ')
    print(f"Content (первые 200 симв): {repr(content[:200])}")
    print(f"Полный doc: {doc}")
