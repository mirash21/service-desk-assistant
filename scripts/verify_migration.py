#!/usr/bin/env python3
"""
Скрипт для проверки применения миграции created_at
"""

import os
import sys
sys.path.insert(0, '/app')

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def verify_migration():
    """Проверяет наличие поля created_at"""
    
    print("=" * 70)
    print("ПРОВЕРКА МИГРАЦИИ: created_at")
    print("=" * 70)
    
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    try:
        # Пробуем получить запись с created_at
        result = supabase.table('documents').select('id', 'created_at').limit(5).execute()
        
        if not result.data:
            print("\n⚠️  Таблица documents пуста")
            return False
        
        print(f"\n✅ Поле created_at существует!")
        print(f"\n📊 Примеры записей:")
        
        for i, doc in enumerate(result.data, 1):
            created_at = doc.get('created_at', 'N/A')
            print(f"   {i}. ID: {doc['id']}, created_at: {created_at}")
        
        # Проверяем есть ли записи без created_at
        null_check = supabase.table('documents').select('id').is_('created_at', None).limit(1).execute()
        
        if null_check.data:
            print(f"\n⚠️  Есть записи без created_at. Необходимо обновить:")
            print("   UPDATE documents SET created_at = NOW() WHERE created_at IS NULL;")
        else:
            print(f"\n✅ Все записи имеют created_at")
        
        # Статистика
        total = supabase.table('documents').select('id', count='exact').execute().count
        print(f"\n📈 Всего документов: {total}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        if 'column documents.created_at does not exist' in error_msg or '42703' in error_msg:
            print(f"\n❌ Поле created_at НЕ существует")
            print(f"\n📋 Примените миграцию:")
            print("   docker compose exec max-bot-webhook python3 scripts/apply_migration.py")
            return False
        else:
            print(f"\n❌ Ошибка проверки: {e}")
            raise


if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
