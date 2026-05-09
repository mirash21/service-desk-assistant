#!/usr/bin/env python3
"""
Скрипт для удаления точных дубликатов из базы знаний RAG
Удаляет документы с полностью одинаковым content, оставляя только один экземпляр
"""

import os
import sys
sys.path.insert(0, '/app')

from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

def remove_exact_duplicates(dry_run=True):
    """
    Удаляет точные дубликаты документов
    
    Args:
        dry_run: Если True, только показывает что будет удалено
    """
    
    print("=" * 80)
    print("УДАЛЕНИЕ ТОЧНЫХ ДУБЛИКАТОВ ИЗ БАЗЫ ЗНАНИЙ RAG")
    print("=" * 80)
    
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    # Получаем все документы
    print("\n📥 Загрузка документов из базы данных...")
    result = supabase.table('documents').select('id', 'content', 'metadata', 'created_at').execute()
    docs = result.data
    
    print(f"   Всего документов: {len(docs)}")
    
    # Группируем по content
    print("\n🔍 Поиск точных дубликатов...")
    content_groups = defaultdict(list)
    
    for doc in docs:
        content_key = doc['content'].strip()
        content_groups[content_key].append(doc)
    
    # Находим дубликаты (группы с более чем 1 документом)
    duplicates_to_delete = []
    unique_docs_kept = 0
    
    for content, group in content_groups.items():
        if len(group) > 1:
            # Оставляем первый документ (с наименьшим ID или earliest created_at)
            # Сортируем по created_at если есть, иначе по id
            if group[0].get('created_at'):
                group.sort(key=lambda x: x.get('created_at', ''))
            else:
                group.sort(key=lambda x: x['id'])
            
            # Первый оставляем, остальные помечаем на удаление
            kept = group[0]
            unique_docs_kept += 1
            
            for dup in group[1:]:
                duplicates_to_delete.append({
                    'id': dup['id'],
                    'kept_id': kept['id'],
                    'category': dup.get('metadata', {}).get('category', 'unknown'),
                    'content_preview': content[:100]
                })
        else:
            unique_docs_kept += 1
    
    print(f"\n📊 Результаты анализа:")
    print(f"   Уникальных документов: {unique_docs_kept}")
    print(f"   Найдено дубликатов: {len(duplicates_to_delete)}")
    print(f"   После очистки останется: {unique_docs_kept} документов")
    
    if not duplicates_to_delete:
        print("\n✅ Точные дубликаты не найдены!")
        return
    
    # Показываем примеры
    print(f"\n📋 Примеры дубликатов (первые 10):")
    print("-" * 80)
    
    for i, dup in enumerate(duplicates_to_delete[:10], 1):
        print(f"{i}. Удалить ID {dup['id']} (дубликат ID {dup['kept_id']})")
        print(f"   Категория: {dup['category']}")
        print(f"   Content: {dup['content_preview']}...")
        print()
    
    if len(duplicates_to_delete) > 10:
        print(f"   ... и еще {len(duplicates_to_delete) - 10} дубликатов\n")
    
    # Распределение по категориям
    print(f"📂 Распределение дубликатов по категориям:")
    category_counts = defaultdict(int)
    for dup in duplicates_to_delete:
        category_counts[dup['category']] += 1
    
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {cat:30s}: {count:4d}")
    
    # Удаление
    if dry_run:
        print(f"\n⚠️  DRY RUN MODE - ничего не удалено")
        print(f"\n💡 Для реального удаления запустите:")
        print(f"   docker compose exec max-bot-webhook python3 scripts/remove_duplicates.py --force")
    else:
        print(f"\n❓ Вы уверены что хотите удалить {len(duplicates_to_delete)} дубликатов?")
        confirm = input("   Введите 'yes' для подтверждения: ")
        
        if confirm.lower() != 'yes':
            print("\n❌ Операция отменена")
            return
        
        print(f"\n🗑️  Удаление дубликатов...")
        deleted_count = 0
        
        for i, dup in enumerate(duplicates_to_delete, 1):
            try:
                result = supabase.table('documents').delete().eq('id', dup['id']).execute()
                if result.data:
                    deleted_count += 1
                    if i % 10 == 0 or i == len(duplicates_to_delete):
                        print(f"   Удалено: {i}/{len(duplicates_to_delete)}")
            except Exception as e:
                print(f"   ⚠️  Ошибка удаления ID {dup['id']}: {e}")
        
        print(f"\n✅ Удалено {deleted_count} дубликатов")
        
        # Проверка результата
        final_count = supabase.table('documents').select('id', count='exact').execute().count
        print(f"📈 Теперь в базе {final_count} документов")
        
        if final_count == unique_docs_kept:
            print("✅ Все дубликаты успешно удалены!")
        else:
            print(f"⚠️  Ожидалось {unique_docs_kept}, получилось {final_count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Удаление дубликатов из базы знаний RAG')
    parser.add_argument('--force', action='store_true', help='Подтвердить удаление без запроса')
    
    args = parser.parse_args()
    
    remove_exact_duplicates(dry_run=not args.force)
