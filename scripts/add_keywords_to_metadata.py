#!/usr/bin/env python3
"""Добавление keywords в metadata документов на основе их содержания"""

from supabase import create_client
import os
from dotenv import load_dotenv
import re

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Словарь тематических keywords по категориям
KEYWORDS_MAP = {
    'printers': ['принтер', 'печать', 'driver', 'драйвер', 'картридж', 'toner', 'MFP', 'МФУ'],
    'network': ['сеть', 'wi-fi', 'wifi', 'internet', 'интернет', 'router', 'роутер', 'подключение'],
    'email': ['почта', 'email', 'outlook', 'thunderbird', 'письмо', 'attachment', 'вложение'],
    'password': ['пароль', 'password', 'pin', 'пин-код', 'сброс', 'reset', 'учетная запись'],
    'software': ['программа', 'software', 'установка', 'install', 'обновление', 'update', 'лицензия'],
    'hardware': ['компьютер', 'computer', 'ноутбук', 'laptop', 'монитор', 'keyboard', 'клавиатура', 'мышь'],
    'security': ['вирус', 'virus', 'антивирус', 'firewall', 'брандмауэр', 'безопасность', 'security'],
    'windows': ['windows', 'ошибка', 'error', 'синий экран', 'bsod', 'обновление windows'],
    'office': ['word', 'excel', 'powerpoint', 'office', 'документ', 'таблица', 'презентация'],
}

def extract_keywords(content):
    """Извлекает релевантные keywords из текста"""
    content_lower = content.lower()
    found_keywords = []
    
    for category, keywords in KEYWORDS_MAP.items():
        for keyword in keywords:
            if keyword.lower() in content_lower:
                if keyword not in found_keywords:
                    found_keywords.append(keyword)
    
    # Добавляем общие keywords
    general_keywords = ['помощь', 'help', 'решение', 'solution', 'проблема', 'problem']
    for kw in general_keywords:
        if kw in content_lower and kw not in found_keywords:
            found_keywords.append(kw)
    
    return found_keywords[:10]  # Ограничиваем до 10 keywords

def update_documents_with_keywords(dry_run=True):
    """Обновляет документы, добавляя keywords в metadata"""
    
    print("Получение документов...")
    result = supabase.table('documents').select('id', 'content', 'metadata').execute()
    docs = result.data
    
    print(f"Найдено {len(docs)} документов\n")
    
    updated_count = 0
    skipped_count = 0
    
    for i, doc in enumerate(docs, 1):
        current_metadata = doc.get('metadata', {})
        
        # Проверяем, есть ли уже keywords
        if 'keywords' in current_metadata and current_metadata['keywords']:
            skipped_count += 1
            continue
        
        # Извлекаем keywords
        keywords = extract_keywords(doc['content'])
        
        if keywords:
            # Обновляем metadata
            current_metadata['keywords'] = keywords
            
            if not dry_run:
                try:
                    supabase.table('documents').update({
                        'metadata': current_metadata
                    }).eq('id', doc['id']).execute()
                    updated_count += 1
                except Exception as e:
                    print(f"Ошибка обновления документа {doc['id']}: {e}")
            else:
                updated_count += 1
            
            if i % 50 == 0:
                print(f"Обработано {i}/{len(docs)} документов...")
    
    print(f"\n{'='*80}")
    print(f"РЕЗУЛЬТАТЫ:")
    print(f"{'='*80}")
    print(f"Всего документов: {len(docs)}")
    print(f"Обновлено: {updated_count}")
    print(f"Пропущено (уже есть keywords): {skipped_count}")
    
    if dry_run:
        print(f"\n⚠️  Это тестовый режим (dry run)")
        print(f"Для реального обновления запустите: python3 scripts/add_keywords_to_metadata.py --apply")
    else:
        print(f"\n✅ Metadata успешно обновлены!")

if __name__ == '__main__':
    import sys
    
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("Запуск в режиме DRY RUN (без изменений)\n")
    else:
        print("Запуск в режиме APPLY (с изменениями)\n")
        confirm = input("Вы уверены? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Отменено.")
            exit(0)
    
    update_documents_with_keywords(dry_run=dry_run)
