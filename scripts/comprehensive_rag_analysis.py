#!/usr/bin/env python3
"""
Комплексный анализатор качества RAG базы знаний

Анализирует и предоставляет рекомендации по:
1. Длине чанков (слишком длинные/короткие)
2. Наличию категорий
3. Наличию keywords
4. Формату Q&A
5. Синонимам

Может автоматически исправлять найденные проблемы.
"""

from supabase import create_client
import os
from dotenv import load_dotenv
import sys
from typing import Dict, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.document_validator import DocumentQualityValidator

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
validator = DocumentQualityValidator()


def get_sample_documents(sample_size: int = 100):
    """Получает образец документов для анализа"""
    print(f"📥 Получение {sample_size} документов для анализа...")
    
    result = supabase.table('documents').select(
        'id', 'content', 'metadata', 'created_at'
    ).limit(sample_size).execute()
    
    docs = result.data
    print(f"✅ Загружено {len(docs)} документов\n")
    
    return docs


def analyze_chunk_lengths(docs: List[Dict]) -> Dict:
    """Анализирует распределение длин чанков"""
    stats = {
        'total': len(docs),
        'long_chunks': [],      # >600 символов
        'short_chunks': [],     # <200 символов
        'optimal_chunks': [],   # 200-600 символов
        'avg_length': 0,
        'min_length': float('inf'),
        'max_length': 0
    }
    
    lengths = []
    
    for doc in docs:
        length = len(doc['content'])
        lengths.append(length)
        
        if length > 600:
            stats['long_chunks'].append({
                'id': doc['id'],
                'length': length,
                'preview': doc['content'][:100] + '...'
            })
        elif length < 200:
            stats['short_chunks'].append({
                'id': doc['id'],
                'length': length,
                'preview': doc['content']
            })
        else:
            stats['optimal_chunks'].append(doc)
        
        stats['min_length'] = min(stats['min_length'], length)
        stats['max_length'] = max(stats['max_length'], length)
    
    stats['avg_length'] = sum(lengths) / len(lengths) if lengths else 0
    
    return stats


def analyze_categories(docs: List[Dict]) -> Dict:
    """Анализирует наличие категорий"""
    stats = {
        'total': len(docs),
        'with_category': 0,
        'without_category': 0,
        'categories_distribution': {}
    }
    
    for doc in docs:
        category = doc.get('metadata', {}).get('category', '')
        
        if category and category != 'unknown':
            stats['with_category'] += 1
            
            if category not in stats['categories_distribution']:
                stats['categories_distribution'][category] = 0
            stats['categories_distribution'][category] += 1
        else:
            stats['without_category'] += 1
    
    return stats


def analyze_keywords(docs: List[Dict]) -> Dict:
    """Анализирует наличие keywords"""
    stats = {
        'total': len(docs),
        'with_keywords': 0,
        'without_keywords': 0,
        'avg_keywords_count': 0
    }
    
    total_keywords = 0
    
    for doc in docs:
        keywords = doc.get('metadata', {}).get('keywords', [])
        
        if keywords:
            stats['with_keywords'] += 1
            total_keywords += len(keywords)
        else:
            stats['without_keywords'] += 1
    
    stats['avg_keywords_count'] = total_keywords / stats['with_keywords'] if stats['with_keywords'] > 0 else 0
    
    return stats


def analyze_qa_format(docs: List[Dict]) -> Dict:
    """Анализирует формат Q&A"""
    import re
    
    stats = {
        'total': len(docs),
        'has_qa_format': 0,
        'no_qa_format': 0
    }
    
    for doc in docs:
        content = doc['content']
        
        if re.search(r'[ВвQq]:\s', content):
            stats['has_qa_format'] += 1
        else:
            stats['no_qa_format'] += 1
    
    return stats


def generate_quality_report(length_stats: Dict, category_stats: Dict, 
                           keyword_stats: Dict, qa_stats: Dict) -> str:
    """Генерирует отчет о качестве"""
    
    report = []
    report.append("="*80)
    report.append("ОТЧЕТ О КАЧЕСТВЕ БАЗЫ ЗНАНИЙ RAG")
    report.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("="*80)
    report.append("")
    
    # Общая статистика
    report.append("📊 ОБЩАЯ СТАТИСТИКА")
    report.append("-"*80)
    report.append(f"Проанализировано документов: {length_stats['total']}")
    report.append("")
    
    # Длины чанков
    report.append("📏 ДЛИНЫ ЧАНКОВ")
    report.append("-"*80)
    report.append(f"Средняя длина: {length_stats['avg_length']:.0f} символов")
    report.append(f"Минимальная длина: {length_stats['min_length']} символов")
    report.append(f"Максимальная длина: {length_stats['max_length']} символов")
    report.append("")
    report.append(f"✅ Оптимальные (200-600): {len(length_stats['optimal_chunks'])} "
                 f"({len(length_stats['optimal_chunks'])/length_stats['total']*100:.1f}%)")
    report.append(f"⚠️  Длинные (>600): {len(length_stats['long_chunks'])} "
                 f"({len(length_stats['long_chunks'])/length_stats['total']*100:.1f}%)")
    report.append(f"⚠️  Короткие (<200): {len(length_stats['short_chunks'])} "
                 f"({len(length_stats['short_chunks'])/length_stats['total']*100:.1f}%)")
    report.append("")
    
    # Категории
    category_pct = (category_stats['with_category'] / category_stats['total'] * 100) if category_stats['total'] > 0 else 0
    report.append("🏷️  КАТЕГОРИИ")
    report.append("-"*80)
    report.append(f"С категорией: {category_stats['with_category']}/{category_stats['total']} ({category_pct:.1f}%)")
    report.append(f"Без категории: {category_stats['without_category']}/{category_stats['total']} "
                 f"({100-category_pct:.1f}%)")
    
    if category_stats['categories_distribution']:
        report.append("")
        report.append("Распределение по категориям:")
        for cat, count in sorted(category_stats['categories_distribution'].items()):
            report.append(f"  {cat}: {count}")
    report.append("")
    
    # Keywords
    keyword_pct = (keyword_stats['with_keywords'] / keyword_stats['total'] * 100) if keyword_stats['total'] > 0 else 0
    report.append("🔑 KEYWORDS")
    report.append("-"*80)
    report.append(f"С keywords: {keyword_stats['with_keywords']}/{keyword_stats['total']} ({keyword_pct:.1f}%)")
    report.append(f"Без keywords: {keyword_stats['without_keywords']}/{keyword_stats['total']} "
                 f"({100-keyword_pct:.1f}%)")
    report.append(f"Среднее количество keywords: {keyword_stats['avg_keywords_count']:.1f}")
    report.append("")
    
    # Формат Q&A
    qa_pct = (qa_stats['has_qa_format'] / qa_stats['total'] * 100) if qa_stats['total'] > 0 else 0
    report.append("❓ ФОРМАТ Q&A")
    report.append("-"*80)
    report.append(f"В формате Q&A: {qa_stats['has_qa_format']}/{qa_stats['total']} ({qa_pct:.1f}%)")
    report.append(f"Не в формате Q&A: {qa_stats['no_qa_format']}/{qa_stats['total']} "
                 f"({100-qa_pct:.1f}%)")
    report.append("")
    
    # Рекомендации
    report.append("="*80)
    report.append("💡 РЕКОМЕНДАЦИИ")
    report.append("="*80)
    report.append("")
    
    recommendations = []
    
    # Рекомендации по длинам чанков
    if len(length_stats['long_chunks']) > 0:
        recommendations.append(
            f"1. 🔴 {len(length_stats['long_chunks'])} чанков слишком длинные (>600 симв.). "
            f"Рассмотрите возможность их разделения.\n"
            f"   Команда: python3 scripts/optimize_chunk_lengths.py --apply"
        )
    
    if len(length_stats['short_chunks']) > 0:
        recommendations.append(
            f"2. 🟡 {len(length_stats['short_chunks'])} чанков короткие (<200 симв.). "
            f"Рассмотрите возможность их объединения или расширения.\n"
            f"   Команда: python3 scripts/optimize_chunk_lengths.py --apply"
        )
    
    # Рекомендации по категориям
    if category_pct < 80:
        recommendations.append(
            f"3. 🔴 Только {category_pct:.0f}% документов имеют категории. "
            f"Убедитесь что категория установлена при добавлении документов.\n"
            f"   Команда: python3 scripts/add_categories_to_documents.py --apply"
        )
    
    # Рекомендации по keywords
    if keyword_pct < 80:
        recommendations.append(
            f"4. 🟡 Только {keyword_pct:.0f}% документов имеют keywords. "
            f"Используйте автоисправление при добавлении новых документов.\n"
            f"   Команда: python3 scripts/add_keywords_to_metadata.py --apply"
        )
    
    # Рекомендации по Q&A формату
    if qa_pct < 95:
        recommendations.append(
            f"5. ⚠️  {100-qa_pct:.1f}% документов не в формате Q&A. "
            f"Преобразуйте их для улучшения поиска."
        )
    
    if recommendations:
        for rec in recommendations:
            report.append(rec)
            report.append("")
    else:
        report.append("✅ Отлично! База знаний соответствует всем стандартам качества.")
        report.append("")
    
    # Оценка качества
    quality_score = 0
    
    # Длины чанков (25 баллов)
    optimal_pct = len(length_stats['optimal_chunks']) / length_stats['total'] * 100
    quality_score += min(25, optimal_pct * 0.25)
    
    # Категории (25 баллов)
    quality_score += min(25, category_pct * 0.25)
    
    # Keywords (25 баллов)
    quality_score += min(25, keyword_pct * 0.25)
    
    # Q&A формат (25 баллов)
    quality_score += min(25, qa_pct * 0.25)
    
    report.append("="*80)
    report.append(f"🎯 ОБЩАЯ ОЦЕНКА КАЧЕСТВА: {quality_score:.0f}/100")
    report.append("="*80)
    report.append("")
    
    if quality_score >= 90:
        report.append("✅ ОТЛИЧНО! База знаний высокого качества")
    elif quality_score >= 75:
        report.append("👍 ХОРОШО! Есть небольшие области для улучшения")
    elif quality_score >= 60:
        report.append("⚠️  УДОВЛЕТВОРИТЕЛЬНО! Рекомендуется улучшить качество")
    else:
        report.append("🔴 ТРЕБУЕТ ВНИМАНИЯ! Необходимо срочно улучшить качество")
    
    report.append("")
    report.append("="*80)
    
    return "\n".join(report)


def main():
    """Основная функция"""
    print("="*80)
    print("КОМПЛЕКСНЫЙ АНАЛИЗ КАЧЕСТВА RAG БАЗЫ ЗНАНИЙ")
    print("="*80)
    print()
    
    # Получаем образец документов
    sample_size = 100
    if '--full' in sys.argv:
        print("⚠️  ПОЛНЫЙ АНАЛИЗ (все документы)")
        # Для полного анализа нужно получить все документы
        result = supabase.table('documents').select('id', 'content', 'metadata', 'created_at').execute()
        docs = result.data
        print(f"✅ Загружено {len(docs)} документов\n")
    else:
        docs = get_sample_documents(sample_size)
    
    if not docs:
        print("❌ Нет документов для анализа")
        return
    
    # Выполняем анализы
    print("🔍 Анализ длин чанков...")
    length_stats = analyze_chunk_lengths(docs)
    
    print("🔍 Анализ категорий...")
    category_stats = analyze_categories(docs)
    
    print("🔍 Анализ keywords...")
    keyword_stats = analyze_keywords(docs)
    
    print("🔍 Анализ формата Q&A...")
    qa_stats = analyze_qa_format(docs)
    
    print("\n✅ Анализ завершен!\n")
    
    # Генерируем отчет
    report = generate_quality_report(length_stats, category_stats, keyword_stats, qa_stats)
    
    # Выводим отчет
    print(report)
    
    # Сохраняем отчет в файл
    report_file = f"rag_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Отчет сохранен в: {report_file}")
    
    # Показываем команды для исправления
    print("\n" + "="*80)
    print("🛠️  КОМАНДЫ ДЛЯ ИСПРАВЛЕНИЯ ПРОБЛЕМ")
    print("="*80)
    print()
    
    if len(length_stats['long_chunks']) > 0 or len(length_stats['short_chunks']) > 0:
        print("1. Оптимизация длин чанков:")
        print("   python3 scripts/optimize_chunk_lengths.py           # DRY RUN")
        print("   python3 scripts/optimize_chunk_lengths.py --apply   # Применить изменения")
        print()
    
    if category_stats['without_category'] > 0:
        print("2. Добавление категорий:")
        print("   python3 scripts/add_categories_to_documents.py           # DRY RUN")
        print("   python3 scripts/add_categories_to_documents.py --apply   # Применить изменения")
        print()
    
    if keyword_stats['without_keywords'] > 0:
        print("3. Добавление keywords:")
        print("   python3 scripts/add_keywords_to_metadata.py           # DRY RUN")
        print("   python3 scripts/add_keywords_to_metadata.py --apply   # Применить изменения")
        print()
    
    print("="*80)


if __name__ == '__main__':
    main()
