from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 70)
print("ПРОВЕРКА ТАБЛИЦЫ chat_history")
print("=" * 70)

try:
    # Проверяем через pg_tables
    result = client.table('pg_tables').select('tablename').eq('schemaname', 'public').execute()
    tables = [r['tablename'] for r in result.data]
    print(f"\nТаблицы в схеме public: {tables}")
    
    if 'chat_history' in tables:
        print("\n✅ Таблица chat_history СУЩЕСТВУЕТ!")
        
        # Проверяем данные
        try:
            data_result = client.table('chat_history').select('*').limit(5).execute()
            print(f"Записей в таблице: {len(data_result.data)}")
            
            if data_result.data:
                print("\n📊 Пример данных:")
                for r in data_result.data:
                    print(f"  - ID: {r.get('id')}")
                    print(f"    User: {r.get('user_id')}")
                    print(f"    Type: {r.get('message_type')}")
                    print(f"    Content: {str(r.get('content', ''))[:60]}...")
                    print()
        except Exception as e2:
            print(f"\n⚠️  Ошибка при чтении данных: {e2}")
    else:
        print("\n❌ Таблица chat_history НЕ найдена!")
        print("\n💡 Возможно, вы создали таблицу не в той базе данных или схеме.")
        print("Проверьте, что выполнили SQL в правильном проекте Supabase.")
        
except Exception as e:
    print(f"\n❌ Ошибка проверки: {e}")
    import traceback
    traceback.print_exc()
