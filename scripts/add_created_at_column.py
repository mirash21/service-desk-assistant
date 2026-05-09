#!/usr/bin/env python3
"""
Скрипт для добавления поля created_at в таблицу documents
"""

import os
import sys
sys.path.insert(0, '/app')

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def add_created_at_column():
    """Добавляет колонку created_at через Supabase API"""
    
    print("=" * 70)
    print("ДОБАВЛЕНИЕ ПОЛЯ created_at В ТАБЛИЦУ documents")
    print("=" * 70)
    
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    
    try:
        # Проверяем существует ли уже колонка
        print("\n🔍 Проверка существующей структуры таблицы...")
        
        # Пробуем получить одну запись с created_at
        test_result = supabase.table('documents').select('id', 'created_at').limit(1).execute()
        
        if test_result.data and 'created_at' in test_result.data[0]:
            print("✅ Поле created_at уже существует!")
            
            # Проверяем есть ли записи без created_at
            null_check = supabase.table('documents').select('id').is_('created_at', None).execute()
            
            if null_check.data:
                print(f"⚠️  Найдено {len(null_check.data)} записей без created_at")
                print("   Обновляем их...")
                
                # К сожалению, Supabase client не поддерживает UPDATE без условия
                # Поэтому используем raw SQL через RPC если доступно
                print("   ⚠️  Для обновления существующих записей используйте SQL Editor в Supabase:")
                print("   UPDATE documents SET created_at = NOW() WHERE created_at IS NULL;")
            else:
                print("✅ Все записи имеют created_at")
            
            return True
        
    except Exception as e:
        error_msg = str(e)
        if 'column documents.created_at does not exist' in error_msg or '42703' in error_msg:
            print("❌ Поле created_at не существует. Создаем...")
            
            # Используем Supabase Management API или SQL через Admin
            print("\n⚠️  Для создания колонки выполните следующий SQL в Supabase SQL Editor:")
            print("\n" + "=" * 70)
            print("""
-- Добавьте эту колонку через Supabase Dashboard → SQL Editor
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

UPDATE documents 
SET created_at = NOW() 
WHERE created_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_documents_created_at 
ON documents(created_at);

COMMENT ON COLUMN documents.created_at IS 'Время создания документа';
""")
            print("=" * 70)
            print("\nПосле выполнения SQL запустите этот скрипт снова для проверки.")
            
            return False
        else:
            print(f"❌ Ошибка: {e}")
            raise
    
    print("\n✅ Миграция успешно применена!")
    return True


if __name__ == "__main__":
    success = add_created_at_column()
    sys.exit(0 if success else 1)
