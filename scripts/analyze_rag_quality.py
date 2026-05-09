#!/usr/bin/env python3
"""Комплексный анализ качества базы знаний RAG"""

from supabase import create_client
import os
from dotenv import load_dotenv
from collections import Counter, defaultdict
import re

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print('=' * 80)
print('КОМПЛЕКСНЫЙ АНАЛИЗ БАЗЫ ЗНАНИЙ RAG')
print('=' * 80)

# Получаем выборку документов для анализа
result = supabase.table('documents').select('id', 'content', 'metadata').limit(100).execute()
docs = result.data

print(f'\n📊 Анализ выборки: {len(docs)} документов\n')

# 1. Проверка формата Q&A
print('1️⃣  Формат чанков:')
qa_format = 0
non_qa_format = 0
for doc in docs:
    content = doc['content']
    if re.search(r'[ВвQq]:\s', content):
        qa_format += 1
    else:
        non_qa_format += 1

print(f'   ✅ В формате Q&A: {qa_format} ({qa_format/len(docs)*100:.1f}%)')
print(f'   ❌ Другой формат: {non_qa_format} ({non_qa_format/len(docs)*100:.1f}%)')

# 2. Проверка метаданных
print('\n2️⃣  Качество метаданных:')
has_keywords = sum(1 for d in docs if 'keywords' in d.get('metadata', {}))
has_category = sum(1 for d in docs if 'category' in d.get('metadata', {}))
has_type = sum(1 for d in docs if 'type' in d.get('metadata', {}))

print(f'   📂 С категорией: {has_category}/{len(docs)}')
print(f'   🏷️  С типом: {has_type}/{len(docs)}')
print(f'   🔑 С keywords: {has_keywords}/{len(docs)} ⚠️')

# 3. Анализ длины чанков
print('\n3️⃣  Длина чанков:')
lengths = [len(d['content']) for d in docs]
avg_len = sum(lengths) / len(lengths)
min_len = min(lengths)
max_len = max(lengths)

print(f'   Средняя: {avg_len:.0f} символов')
print(f'   Мин: {min_len}, Макс: {max_len}')

if avg_len > 500:
    print('   ⚠️  Чанки слишком длинные (рекомендуется 300-500)')
elif avg_len < 200:
    print('   ⚠️  Чанки слишком короткие')
else:
    print('   ✅ Оптимальная длина')

# 4. Проверка на наличие контекста
print('\n4️⃣  Контекстуализация чанков:')
with_context = 0
isolated = 0
for doc in docs:
    content = doc['content']
    # Проверяем есть ли заголовок/контекст в начале
    lines = content.split('\n')
    if len(lines) > 1 and len(lines[0]) < 100 and not lines[0].startswith(('В:', 'О:', '•', '1.', '-')):
        with_context += 1
    else:
        isolated += 1

print(f'   ✅ С контекстом: {with_context}')
print(f'   ❌ Изолированные: {isolated}')

# 5. Проверка на синонимы
print('\n5️⃣  Наличие синонимов:')
synonym_patterns = [
    r'\([^)]*(password|пароль)[^)]*\)',
    r'\([^)]*(принтер|printer)[^)]*\)',
    r'\(.*или.*\)',
]

with_synonyms = 0
for doc in docs:
    for pattern in synonym_patterns:
        if re.search(pattern, doc['content'], re.IGNORECASE):
            with_synonyms += 1
            break

print(f'   С синонимами: {with_synonyms}/{len(docs)}')
if with_synonyms < len(docs) * 0.1:
    print('   ⚠️  Мало синонимов - рекомендуется добавить')

# 6. Распределение по категориям
print('\n6️⃣  Распределение по категориям:')
categories = Counter(d.get('metadata', {}).get('category', 'unknown') for d in docs)
for cat, count in categories.most_common(10):
    bar = '█' * (count // 2)
    print(f'   {cat:25s}: {count:3d} {bar}')

print('\n' + '=' * 80)
print('РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:')
print('=' * 80)

issues = []

if has_keywords == 0:
    issues.append('❌ Отсутствуют keywords в метаданных - критично для поиска')
    
if isolated > len(docs) * 0.7:
    issues.append('❌ Большинство чанков изолированы без контекста')
    
if with_synonyms < len(docs) * 0.1:
    issues.append('⚠️  Недостаточно синонимов в текстах')
    
if avg_len > 500:
    issues.append('⚠️  Чанки слишком длинные - разбить на более мелкие')

if issues:
    print('\nНайденные проблемы:')
    for issue in issues:
        print(f'  {issue}')
else:
    print('\n✅ База знаний в хорошем состоянии!')

print('\nРекомендуемые улучшения:')
print('  1. Добавить keywords в metadata для всех документов')
print('  2. Добавить контекстные заголовки к чанкам')
print('  3. Внедрить синонимы в тексты')
print('  4. Использовать overlapping chunks при создании новых чанков')
print('=' * 80)
