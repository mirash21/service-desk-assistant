#!/usr/bin/env python3
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing Supabase connection...")
print(f"URL: {os.getenv('SUPABASE_URL')[:50]}")
print(f"Key exists: {bool(os.getenv('SUPABASE_KEY'))}")

try:
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    result = supabase.table('documents').select('id').limit(1).execute()
    print(f"Connection OK! Documents count sample: {len(result.data)}")
except Exception as e:
    print(f"Error: {e}")
