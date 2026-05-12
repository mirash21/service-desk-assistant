#!/usr/bin/env python3
"""
Скрипт для оптимизации длины чанков в базе знаний RAG

Проблемы:
- 36 чанков слишком длинные (>600 симв.) - нужно разделить
- 5 чанков короткие (<200 симв.) - нужно объединить или расширить

Решения:
1. Разбивает длинные чанки на части с перекрытием (overlap=50)
2. Объединяет короткие соседние чанки одной категории
3. Сохраняет metadata и keywords при модификации
"""

from supabase import create_client
import os
from dotenv import load_dotenv
import sys
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.document_validator import DocumentQualityValidator

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
validator = DocumentQualityValidator()


def get_all_documents():
    """Получает все документы из базы"""
    print("📥 Получение всех документов...")
    result = supabase.table('documents').select(
        'id', 'content', 'metadata', 'created_at'
    ).order('created_at', desc=True).execute()
    
    docs = result.data
    print(f"✅ Найдено {len(docs)} документов\n")
    return docs


def analyze_chunk_lengths(docs: List[Dict]) -> Dict:
    """Анализирует распределение длин чанков"""
    stats = {
        'total': len(docs),
        'long_chunks': [],      # >600 символов
        'short_chunks': [],     # <200 символов
        'optimal_chunks': [],   # 200-600 символов
    }
    
    for doc in docs:
        length = len(doc['content'])
        
        if length > 600:
            stats['long_chunks'].append({
                'id': doc['id'],
                'length': length,
                'content': doc['content'][:100] + '...',
                'metadata': doc.get('metadata', {})
            })
        elif length < 200:
            stats['short_chunks'].append({
                'id': doc['id'],
                'length': length,
                'content': doc['content'],
                'metadata': doc.get('metadata', {})
            })
        else:
            stats['optimal_chunks'].append(doc)
    
    return stats


def split_long_chunk(content: str, target_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Разбивает длинный чанк на несколько частей с перекрытием
    
    Args:
        content: Текст для разделения
        target_size: Целевой размер чанка (по умолчанию 400)
        overlap: Перекрытие между чанками (по умолчанию 50)
    
    Returns:
        Список чанков
    """
    if len(content) <= 600:
        return [content]
    
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + target_size
        
        # Находим границу предложения для естественного разделения
        if end < len(content):
            # Ищем конец предложения
            sentence_end = content.rfind('.', start, end)
            if sentence_end == -1:
                sentence_end = content.rfind('\n', start, end)
            
            # Если нашли подходящую границу (не слишком близко к началу)
            if sentence_end > start + 150:
                end = sentence_end + 1
        
        chunk = content[start:end].strip()
        
        # Добавляем только если чанк достаточно длинный
        if chunk and len(chunk) >= 150:
            chunks.append(chunk)
        
        # Перемещаемся с учетом перекрытия
        start = end - overlap
    
    return chunks


def merge_short_chunks(docs: List[Dict], min_length: int = 200) -> List[Tuple[List[str], Dict]]:
    """
    Группирует короткие чанки для объединения
    
    Args:
        docs: Список коротких документов
        min_length: Минимальная длина после объединения
    
    Returns:
        Список групп документов для объединения
    """
    # Сортируем по категории и дате создания
    sorted_docs = sorted(
        docs, 
        key=lambda x: (
            x.get('metadata', {}).get('category', 'unknown'),
            x.get('created_at', '')
        )
    )
    
    groups = []
    current_group = []
    current_category = None
    
    for doc in sorted_docs:
        category = doc.get('metadata', {}).get('category', 'unknown')
        
        # Если категория изменилась или группа уже достаточно большая
        if current_category != category or len(current_group) >= 3:
            if current_group:
                groups.append((current_group, current_category))
            current_group = [doc]
            current_category = category
        else:
            current_group.append(doc)
    
    # Добавляем последнюю группу
    if current_group:
        groups.append((current_group, current_category))
    
    # Фильтруем группы: оставляем только те, где можно достичь min_length
    valid_groups = []
    for group, category in groups:
        total_length = sum(len(doc['content']) for doc in group)
        if total_length >= min_length or len(group) == 1:
            valid_groups.append((group, category))
    
    return valid_groups


def process_long_chunks(stats: Dict, dry_run: bool = True) -> Dict:
    """
    Обрабатывает длинные чанки - разделяет их на части
    
    Returns:
        Статистика обработки
    """
    long_chunks = stats['long_chunks']
    print(f"\n{'='*80}")
    print(f"ОБРАБОТКА ДЛИННЫХ ЧАНКОВ ({len(long_chunks)} шт.)")
    print(f"{'='*80}\n")
    
    results = {
        'split_count': 0,
        'new_chunks_created': 0,
        'errors': 0
    }
    
    for i, chunk_info in enumerate(long_chunks, 1):
        doc_id = chunk_info['id']
        content = chunk_info['content']
        metadata = chunk_info['metadata']
        original_length = chunk_info['length']
        
        print(f"[{i}/{len(long_chunks)}] Обработка документа {str(doc_id)[:8]}...")
        print(f"  Исходная длина: {original_length} символов")
        
        # Разбиваем на части
        new_chunks = validator.split_long_chunk(content, target_size=400, overlap=50)
        
        print(f"  Создано чанков: {len(new_chunks)}")
        for j, new_chunk in enumerate(new_chunks, 1):
            print(f"    Чанк {j}: {len(new_chunk)} символов")
        
        if not dry_run:
            try:
                # Удаляем старый документ
                supabase.table('documents').delete().eq('id', doc_id).execute()
                
                # Создаем новые чанки с тем же metadata
                from services.yandex_service import YandexAIService
                yandex = YandexAIService()
                
                for new_chunk in new_chunks:
                    embedding = yandex.get_embeddings(new_chunk)
                    
                    supabase.table('documents').insert({
                        'content': new_chunk,
                        'embedding': embedding,
                        'metadata': metadata
                    }).execute()
                
                results['split_count'] += 1
                results['new_chunks_created'] += len(new_chunks)
                print(f"  ✅ Успешно разделен")
                
            except Exception as e:
                results['errors'] += 1
                print(f"  ❌ Ошибка: {e}")
        else:
            print(f"  🔍 DRY RUN - изменения не применены")
        
        print()
    
    return results


def process_short_chunks(stats: Dict, dry_run: bool = True) -> Dict:
    """
    Обрабатывает короткие чанки - предлагает объединить или расширить
    
    Returns:
        Статистика обработки
    """
    short_chunks = stats['short_chunks']
    print(f"\n{'='*80}")
    print(f"ОБРАБОТКА КОРОТКИХ ЧАНКОВ ({len(short_chunks)} шт.)")
    print(f"{'='*80}\n")
    
    results = {
        'merge_groups': 0,
        'expanded_count': 0,
        'skipped_count': 0,
        'errors': 0
    }
    
    # Группируем короткие чанки для объединения
    merge_groups = merge_short_chunks(short_chunks)
    
    print(f"Найдено {len(merge_groups)} групп для обработки:\n")
    
    for i, (group, category) in enumerate(merge_groups, 1):
        print(f"Группа {i} (категория: {category}):")
        
        if len(group) == 1:
            # Одиночный короткий чанк - предлагаем расширить
            doc = group[0]
            print(f"  Документ: {str(doc['id'])[:8]}")
            print(f"  Длина: {len(doc['content'])} символов")
            print(f"  Содержимое: {doc['content'][:100]}...")
            print(f"  💡 Рекомендация: Расширить содержимое или объединить с похожими чанками")
            
            if not dry_run:
                # TODO: Здесь можно добавить логику расширения через LLM
                results['expanded_count'] += 0  # Пока пропускаем
                results['skipped_count'] += 1
            print()
        
        else:
            # Несколько чанков - можно объединить
            total_length = sum(len(doc['content']) for doc in group)
            print(f"  Количество чанков: {len(group)}")
            print(f"  Общая длина: {total_length} символов")
            
            if total_length >= 200:
                print(f"  ✅ Можно объединить в один чанк")
                
                if not dry_run:
                    try:
                        # Объединяем содержимое
                        merged_content = "\n\n".join([doc['content'] for doc in group])
                        
                        # Используем metadata первого документа
                        merged_metadata = group[0].get('metadata', {}).copy()
                        
                        # Генерируем embedding
                        from services.yandex_service import YandexAIService
                        yandex = YandexAIService()
                        embedding = yandex.get_embeddings(merged_content)
                        
                        # Создаем новый объединенный документ
                        supabase.table('documents').insert({
                            'content': merged_content,
                            'embedding': embedding,
                            'metadata': merged_metadata
                        }).execute()
                        
                        # Удаляем старые документы
                        for doc in group:
                            supabase.table('documents').delete().eq('id', doc['id']).execute()
                        
                        results['merge_groups'] += 1
                        print(f"  ✅ Успешно объединено")
                        
                    except Exception as e:
                        results['errors'] += 1
                        print(f"  ❌ Ошибка: {e}")
                else:
                    print(f"  🔍 DRY RUN - изменения не применены")
            else:
                print(f"  ⚠️  Даже после объединения будет слишком коротко ({total_length} симв.)")
                results['skipped_count'] += 1
            
            print()
    
    return results


def main():
    """Основная функция"""
    print("="*80)
    print("ОПТИМИЗАЦИЯ ДЛИНЫ ЧАНКОВ В БАЗЕ ЗНАНИЙ RAG")
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
    
    # Получаем все документы
    docs = get_all_documents()
    
    # Анализируем длины
    stats = analyze_chunk_lengths(docs)
    
    print(f"{'='*80}")
    print(f"СТАТИСТИКА ДЛИН ЧАНКОВ")
    print(f"{'='*80}")
    print(f"Всего документов: {stats['total']}")
    print(f"Оптимальные (200-600): {len(stats['optimal_chunks'])} ({len(stats['optimal_chunks'])/stats['total']*100:.1f}%)")
    print(f"Длинные (>600): {len(stats['long_chunks'])} ({len(stats['long_chunks'])/stats['total']*100:.1f}%)")
    print(f"Короткие (<200): {len(stats['short_chunks'])} ({len(stats['short_chunks'])/stats['total']*100:.1f}%)")
    print()
    
    # Обрабатываем длинные чанки
    if stats['long_chunks']:
        long_results = process_long_chunks(stats, dry_run=dry_run)
        
        print(f"\n{'='*80}")
        print(f"РЕЗУЛЬТАТЫ ОБРАБОТКИ ДЛИННЫХ ЧАНКОВ")
        print(f"{'='*80}")
        print(f"Разделено чанков: {long_results['split_count']}")
        print(f"Создано новых чанков: {long_results['new_chunks_created']}")
        print(f"Ошибок: {long_results['errors']}")
    
    # Обрабатываем короткие чанки
    if stats['short_chunks']:
        short_results = process_short_chunks(stats, dry_run=dry_run)
        
        print(f"\n{'='*80}")
        print(f"РЕЗУЛЬТАТЫ ОБРАБОТКИ КОРОТКИХ ЧАНКОВ")
        print(f"{'='*80}")
        print(f"Объединено групп: {short_results['merge_groups']}")
        print(f"Расширено чанков: {short_results['expanded_count']}")
        print(f"Пропущено: {short_results['skipped_count']}")
        print(f"Ошибок: {short_results['errors']}")
    
    print(f"\n{'='*80}")
    print(f"✅ АНАЛИЗ ЗАВЕРШЕН")
    print(f"{'='*80}")
    
    if dry_run:
        print("\n💡 Запустите с флагом --apply для применения изменений")


if __name__ == '__main__':
    main()
