#!/usr/bin/env python3
"""
Применение миграции для создания таблицы rag_quality_metrics
"""

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def create_table():
    """Создает таблицу rag_quality_metrics через SQL"""
    
    sql = """
    CREATE TABLE IF NOT EXISTS rag_quality_metrics (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        top_k INTEGER NOT NULL,
        avg_faithfulness FLOAT NOT NULL,
        avg_answer_relevance FLOAT NOT NULL,
        avg_context_precision FLOAT NOT NULL,
        avg_context_recall FLOAT NOT NULL,
        total_questions INTEGER NOT NULL,
        avg_evaluation_time FLOAT NOT NULL,
        evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_rag_metrics_top_k ON rag_quality_metrics(top_k);
    CREATE INDEX IF NOT EXISTS idx_rag_metrics_evaluated_at ON rag_quality_metrics(evaluated_at DESC);
    """
    
    try:
        # Выполняем SQL через Supabase RPC
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("✅ Таблица rag_quality_metrics создана успешно")
        return True
    
    except Exception as e:
        print(f"⚠️  RPC метод exec_sql недоступен: {e}")
        print("Создайте таблицу вручную через Supabase Dashboard → SQL Editor")
        print("\nSQL для выполнения:")
        print(sql)
        return False

if __name__ == '__main__':
    print("="*80)
    print("ПРИМЕНЕНИЕ МИГРАЦИИ: Создание таблицы rag_quality_metrics")
    print("="*80)
    print()
    
    create_table()
