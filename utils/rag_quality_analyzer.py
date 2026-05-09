#!/usr/bin/env python3
"""
Утилита для анализа качества базы знаний RAG
Выявляет дубликаты, короткие документы, проблемы с кодировкой
"""

import os
import sys
sys.path.insert(0, '/app')

from supabase import create_client
from dotenv import load_dotenv
from collections import Counter
import re

load_dotenv()

def analyze_database():
    """Анализ качества базы знаний"""
    
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    print("=" * 70)
    print("АНАЛИЗ КАЧЕСТВА БАЗЫ ЗНАНИЙ RAG")
    print("=" * 70)
    
    # Получаем все документы
    result = supabase.table('documents').select('id', 'content', 'metadata').execute()
    docs = result.data
    
    print(f"\n📊 Общая статистика:")
    print(f"   Всего документов: {len(docs)}")
    
    # 1. Анализ длины документов
    print(f"\n📏 Анализ длины документов:")
    lengths = [len(doc['content']) for doc in docs]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    min_length = min(lengths) if lengths else 0
    max_length = max(lengths) if lengths else 0
    
    print(f"   Средняя длина: {avg_length:.0f} символов")
    print(f"   Минимальная: {min_length} символов")
    print(f"   Максимальная: {max_length} символов")
    
    # Короткие документы (< 50 символов)
    short_docs = [doc for doc in docs if len(doc['content']) < 50]
    if short_docs:
        print(f"\n   ⚠️  Найдено {len(short_docs)} очень коротких документов (< 50 симв):")
        for doc in short_docs[:5]:  # Показываем первые 5
            content_preview = doc['content'][:60].replace('\n', ' ')
            print(f"      - ID {doc['id']}: '{content_preview}...'")
    
    # 2. Поиск потенциальных дубликатов (по первым 100 символам)
    print(f"\n🔍 Поиск потенциальных дубликатов:")
    content_prefixes = {}
    duplicates = []
    
    for doc in docs:
        prefix = doc['content'][:100].strip()
        if prefix in content_prefixes:
            duplicates.append({
                'original_id': content_prefixes[prefix],
                'duplicate_id': doc['id'],
                'prefix': prefix[:80]
            })
        else:
            content_prefixes[prefix] = doc['id']
    
    if duplicates:
        print(f"   ⚠️  Найдено {len(duplicates)} потенциальных дубликатов:")
        for dup in duplicates[:5]:  # Показываем первые 5
            print(f"      - ID {dup['duplicate_id']} дублирует ID {dup['original_id']}")
            print(f"        Начало: '{dup['prefix']}...'")
    else:
        print(f"   ✅ Дубликаты не обнаружены")
    
    # 3. Анализ категорий
    print(f"\n📂 Распределение по категориям:")
    categories = Counter()
    for doc in docs:
        category = doc.get('metadata', {}).get('category', 'unknown')
        categories[category] += 1
    
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(docs)) * 100
        print(f"   {cat:30s}: {count:4d} ({percentage:5.1f}%)")
    
    # 4. Проверка наличия вопросов-ответов
    print(f"\n❓ Анализ формата Q&A:")
    qa_format_count = 0
    non_qa_count = 0
    
    for doc in docs:
        content = doc['content']
        # Проверяем наличие маркеров вопроса/ответа
        if re.search(r'[Вв]:\s', content) or re.search(r'[Qq]:\s', content):
            qa_format_count += 1
        else:
            non_qa_count += 1
    
    print(f"   В формате Q&A: {qa_format_count} ({qa_format_count/len(docs)*100:.1f}%)")
    print(f"   Другой формат: {non_qa_count} ({non_qa_count/len(docs)*100:.1f}%)")
    
    if non_qa_count > len(docs) * 0.3:
        print(f"   ⚠️  Много документов не в формате Q&A. Рекомендуется конвертировать.")
    
    # 5. Поиск документов без метаданных
    print(f"\n🏷️  Анализ метаданных:")
    no_metadata = [doc for doc in docs if not doc.get('metadata') or doc['metadata'] == {}]
    if no_metadata:
        print(f"   ⚠️  Найдено {len(no_metadata)} документов без метаданных")
        for doc in no_metadata[:3]:
            print(f"      - ID {doc['id']}: {doc['content'][:60]}...")
    else:
        print(f"   ✅ Все документы имеют метаданные")
    
    # 6. Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    
    recommendations = []
    
    if short_docs:
        recommendations.append(
            f"1. Удалить или объединить {len(short_docs)} очень коротких документов"
        )
    
    if duplicates:
        recommendations.append(
            f"2. Проверить и удалить {len(duplicates)} дубликатов"
        )
    
    if non_qa_count > len(docs) * 0.3:
        recommendations.append(
            f"3. Конвертировать {non_qa_count} документов в формат Q&A для лучшего поиска"
        )
    
    if no_metadata:
        recommendations.append(
            f"4. Добавить метаданные к {len(no_metadata)} документам"
        )
    
    # Проверка на документы с низкой информативностью
    low_info = [doc for doc in docs if len(doc['content'].split()) < 10]
    if low_info:
        recommendations.append(
            f"5. Удалить {len(low_info)} документов с менее чем 10 словами"
        )
    
    if recommendations:
        for rec in recommendations:
            print(f"   {rec}")
    else:
        print(f"   ✅ База знаний в хорошем состоянии!")
    
    print("\n" + "=" * 70)
    
    return {
        'total_docs': len(docs),
        'short_docs': len(short_docs),
        'duplicates': len(duplicates),
        'qa_format': qa_format_count,
        'non_qa': non_qa_count,
        'no_metadata': len(no_metadata)
    }


def clean_duplicates(dry_run=True):
    """
    Удаление дубликатов
    
    Args:
        dry_run: Если True, только показывает что будет удалено
    """
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    print("\n" + "=" * 70)
    print("ОЧИСТКА ДУБЛИКАТОВ")
    print("=" * 70)
    
    result = supabase.table('documents').select('id', 'content').execute()
    docs = result.data
    
    content_prefixes = {}
    duplicates_to_delete = []
    
    for doc in docs:
        prefix = doc['content'][:100].strip()
        if prefix in content_prefixes:
            duplicates_to_delete.append(doc['id'])
        else:
            content_prefixes[prefix] = doc['id']
    
    if not duplicates_to_delete:
        print("✅ Дубликаты не найдены")
        return
    
    print(f"\nНайдено {len(duplicates_to_delete)} дубликатов для удаления:\n")
    for doc_id in duplicates_to_delete[:10]:
        doc = next(d for d in docs if d['id'] == doc_id)
        print(f"   ID {doc_id}: {doc['content'][:80]}...")
    
    if len(duplicates_to_delete) > 10:
        print(f"   ... и еще {len(duplicates_to_delete) - 10} документов")
    
    if not dry_run:
        confirm = input(f"\nУдалить {len(duplicates_to_delete)} дубликатов? (yes/no): ")
        if confirm.lower() == 'yes':
            for doc_id in duplicates_to_delete:
                supabase.table('documents').delete().eq('id', doc_id).execute()
            print(f"✅ Удалено {len(duplicates_to_delete)} дубликатов")
        else:
            print("❌ Операция отменена")
    else:
        print(f"\n⚠️  Dry run mode. Для реального удаления запустите с dry_run=False")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Анализ и очистка базы знаний RAG')
    parser.add_argument('--clean', action='store_true', help='Удалить дубликаты')
    parser.add_argument('--force', action='store_true', help='Подтвердить удаление без запроса')
    
    args = parser.parse_args()
    
    # Анализ
    stats = analyze_database()
    
    # Очистка если запрошено
    if args.clean:
        clean_duplicates(dry_run=not args.force)
