#!/usr/bin/env python3
"""
Скрипт для автоматического добавления категорий в документы RAG

Проблема:
- Только 64% документов имеют категории (остальные 'unknown' или пустые)

Решение:
- Анализирует содержимое документов
- Определяет категорию на основе ключевых слов
- Обновляет metadata с правильной категорией
"""

from supabase import create_client
import os
from dotenv import load_dotenv
import sys
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.document_validator import DocumentQualityValidator

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
validator = DocumentQualityValidator()


def get_documents_without_category():
    """Получает документы без категории или с category='unknown'"""
    print("📥 Получение документов без категории...")
    
    result = supabase.table('documents').select(
        'id', 'content', 'metadata', 'created_at'
    ).execute()
    
    docs_without_category = []
    docs_with_category = []
    
    for doc in result.data:
        category = doc.get('metadata', {}).get('category', '')
        
        if not category or category == 'unknown':
            docs_without_category.append(doc)
        else:
            docs_with_category.append(doc)
    
    print(f"✅ Всего документов: {len(result.data)}")
    print(f"✅ С категорией: {len(docs_with_category)} ({len(docs_with_category)/len(result.data)*100:.1f}%)")
    print(f"⚠️  Без категории: {len(docs_without_category)} ({len(docs_without_category)/len(result.data)*100:.1f}%)\n")
    
    return docs_without_category, docs_with_category


def detect_and_add_categories(docs: List[Dict], dry_run: bool = True) -> Dict:
    """
    Определяет и добавляет категории для документов
    
    Args:
        docs: Список документов без категории
        dry_run: Если True, только показывает что будет сделано
    
    Returns:
        Статистика обработки
    """
    print(f"{'='*80}")
    print(f"ДОБАВЛЕНИЕ КАТЕГОРИЙ ({len(docs)} документов)")
    print(f"{'='*80}\n")
    
    results = {
        'total': len(docs),
        'categorized': 0,
        'uncategorized': 0,
        'errors': 0,
        'categories_distribution': {}
    }
    
    for i, doc in enumerate(docs, 1):
        doc_id = doc['id']
        content = doc['content']
        metadata = doc.get('metadata', {}).copy()
        
        print(f"[{i}/{len(docs)}] Обработка документа {str(doc_id)[:8]}...")
        
        # Определяем категорию
        suggested_category = validator._detect_category(content)
        
        if suggested_category:
            print(f"  Определена категория: '{suggested_category}'")
            
            if not dry_run:
                try:
                    # Обновляем metadata
                    metadata['category'] = suggested_category
                    
                    supabase.table('documents').update({
                        'metadata': metadata
                    }).eq('id', doc_id).execute()
                    
                    results['categorized'] += 1
                    
                    # Обновляем распределение категорий
                    if suggested_category not in results['categories_distribution']:
                        results['categories_distribution'][suggested_category] = 0
                    results['categories_distribution'][suggested_category] += 1
                    
                    print(f"  ✅ Категория добавлена")
                    
                except Exception as e:
                    results['errors'] += 1
                    print(f"  ❌ Ошибка обновления: {e}")
            else:
                print(f"  🔍 DRY RUN - изменения не применены")
        else:
            print(f"  ⚠️  Не удалось определить категорию")
            results['uncategorized'] += 1
        
        print()
    
    return results


def show_category_suggestions(docs: List[Dict]):
    """Показывает примеры предлагаемых категорий"""
    print(f"\n{'='*80}")
    print(f"ПРИМЕРЫ ОПРЕДЕЛЕНИЯ КАТЕГОРИЙ")
    print(f"{'='*80}\n")
    
    # Показываем первые 10 документов с предложенными категориями
    sample_size = min(10, len(docs))
    
    for i, doc in enumerate(docs[:sample_size], 1):
        content = doc['content']
        suggested_category = validator._detect_category(content)
        
        print(f"{i}. Документ: {str(doc['id'])[:8]}")
        print(f"   Содержимое: {content[:150]}...")
        print(f"   Предложенная категория: {suggested_category or 'НЕ ОПРЕДЕЛЕНА'}")
        
        # Показываем keywords которые помогли определить категорию
        if suggested_category:
            from utils.document_validator import CATEGORY_KEYWORDS
            keywords = CATEGORY_KEYWORDS.get(suggested_category, [])
            found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
            print(f"   Найдены keywords: {found_keywords[:5]}")
        
        print()


def main():
    """Основная функция"""
    print("="*80)
    print("АВТОМАТИЧЕСКОЕ ДОБАВЛЕНИЕ КАТЕГОРИЙ В ДОКУМЕНТЫ RAG")
    print("="*80)
    print()
    
    # Проверяем режим
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("⚠️  РЕЖИМ: DRY RUN (без изменений в базе)")
        print("Для применения изменений используйте: --apply\n")
    else:
        print("⚠️  РЕЖИМ: APPLY (с изменениями в базе)")
        confirm = input("Вы уверены? Все изменения необратимы! (yes/no): ") if sys.stdin.isatty() else "yes"
        if confirm.lower() != 'yes':
            print("❌ Отменено пользователем")
            return
        print()
    
    # Получаем документы без категории
    docs_without_category, docs_with_category = get_documents_without_category()
    
    if not docs_without_category:
        print("✅ Все документы уже имеют категории!")
        return
    
    # Показываем примеры определений
    show_category_suggestions(docs_without_category)
    
    # Добавляем категории
    results = detect_and_add_categories(docs_without_category, dry_run=dry_run)
    
    # Итоговая статистика
    print(f"\n{'='*80}")
    print(f"РЕЗУЛЬТАТЫ ДОБАВЛЕНИЯ КАТЕГОРИЙ")
    print(f"{'='*80}")
    print(f"Всего обработано: {results['total']}")
    print(f"Добавлено категорий: {results['categorized']}")
    print(f"Не определено: {results['uncategorized']}")
    print(f"Ошибок: {results['errors']}")
    
    if results['categories_distribution']:
        print(f"\nРаспределение по категориям:")
        for category, count in sorted(results['categories_distribution'].items()):
            print(f"  {category}: {count}")
    
    # Финальная статистика
    total_docs = len(docs_without_category) + len(docs_with_category)
    final_with_category = len(docs_with_category) + results['categorized']
    final_percentage = (final_with_category / total_docs * 100) if total_docs > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*80}")
    print(f"Документов с категорией: {final_with_category}/{total_docs} ({final_percentage:.1f}%)")
    print(f"Улучшение: +{results['categorized']} документов (+{results['categorized']/total_docs*100:.1f}%)")
    
    if final_percentage < 80:
        print(f"\n⚠️  Внимание: Только {final_percentage:.1f}% документов имеют категории.")
        print(f"   Рекомендуется вручную проверить {results['uncategorized']} документов без категории.")
    else:
        print(f"\n✅ Отлично! {final_percentage:.1f}% документов имеют категории.")
    
    if dry_run:
        print(f"\n💡 Запустите с флагом --apply для применения изменений")


if __name__ == '__main__':
    main()
